import time
from typing import Any, Dict, Iterator, List, Optional

from langchain_core.callbacks import (
    CallbackManagerForLLMRun,
)
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
)
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from pydantic import SecretStr


from src.config import DEFAULT_CONFIG
from src.inetum_agent import InetumSDK
from src.interfaces import InetumGenerationModel
from src.utils.env import get_env_variable


class ChatInetum(BaseChatModel):
    """Inetum Chat Model.
    Inherits from BaseChatModel and implements the chat generation logic

    Attributes:
        model_name: The name of the model to use for generation.
        temperature: The temperature to use for generation.
        max_tokens: The maximum number of tokens to generate.
        timeout: The timeout for the generation request.
        stop: A list of strings on which the model should stop generating.
        max_retries: The maximum number of retries for the generation request.
    """

    inetum_api: Optional[InetumSDK] = None
    polling_interval: float = DEFAULT_CONFIG["polling_interval"]

    model_name: InetumGenerationModel = DEFAULT_CONFIG["model_name"]

    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None

    stop: Optional[List[str]] = None

    timeout: int = DEFAULT_CONFIG["timeout"]
    max_retries: int = 2

    def __init__(
        self,
        api_key: Optional[SecretStr] = None,
        api_url: Optional[str] = None,
        polling_interval: Optional[float] = None,
        model_name: InetumGenerationModel = DEFAULT_CONFIG["model_name"],
        temperature: Optional[float] = 0.16,
        max_tokens: Optional[int] = 16_000,
        top_p: Optional[float] = None,
        **kwargs: Any,
    ):
        super().__init__()

        if api_key is None:
            api_key = SecretStr(get_env_variable("INETUM_GENAI_API_KEY"))

        if api_url is None:
            api_url = DEFAULT_CONFIG["api_url"]

        # Custom model config
        self.model_name = model_name
        self.temperature = temperature
        self.top_p = top_p

        self.polling_interval = polling_interval or DEFAULT_CONFIG["polling_interval"]
        self.timeout = kwargs.get("timeout", DEFAULT_CONFIG["timeout"])

        self.max_tokens = max_tokens or DEFAULT_CONFIG["max_retries"]
        self.stop = kwargs.get("stop", None)

        self.inetum_api = InetumSDK(
            api_key=api_key,
            base_url=api_url,
            model=model_name,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
        )

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Override the _generate method to implement the chat model logic.

        Args:
            messages: the prompt composed of a list of messages.
            stop: a list of strings on which the model should stop generating.
                  If generation stops due to a stop token, the stop token itself
                  SHOULD BE INCLUDED as part of the output. This is not enforced
                  across models right now, but it's a good practice to follow since
                  it makes it much easier to parse the output of the model
                  downstream and understand why generation stopped.
            run_manager: A run manager with callbacks for the LLM.
        """

        if not self.inetum_api:
            raise ValueError("InetumSDK instance could not be initialized.")

        system_prompt = None
        conversation: str = ""

        for message in messages:
            if message.type == "system":
                system_prompt = str(message.content)
            else:
                conversation += f"{message.type}: {message.content}\n---\n"

        # Call the hub API to get the response
        user_prompt = ""
        if len(conversation) > 0:
            user_prompt = conversation
        else:
            user_prompt = str(messages[0].content)

        start_time = time.time()

        # Call the Inetum API to generate a response
        response_text = self.inetum_api.generate(
            user_prompt,
            system_prompt,
            timeout=self.timeout,
            stop=stop,
            polling_interval=self.polling_interval,
            **kwargs,
        )

        generation_time = time.time() - start_time

        last_message = messages[-1]
        tokens = last_message.content

        # Count the number of tokens in the input and output
        ct_input_tokens = sum(len(message.content) for message in messages)
        ct_output_tokens = len(tokens)

        message = AIMessage(
            content=response_text,
            additional_kwargs={},  # Used to add additional payload to the message
            response_metadata={  # Use for response metadataversation_id
                "time_in_seconds": generation_time,
                "model_name": self.model_name,
            },
            usage_metadata={
                "input_tokens": ct_input_tokens,
                "output_tokens": ct_output_tokens,
                "total_tokens": ct_input_tokens + ct_output_tokens,
            },
        )

        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        """Override the _stream method to implement the chat model logic."""
        raise NotImplementedError("Streaming is not supported yet.")

    @property
    def _llm_type(self) -> str:
        return "inetum-chat-generation"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Return a dictionary of identifying parameters.

        This information is used by the LangChain callback system, which
        is used for tracing purposes make it possible to monitor LLMs.
        """
        return {
            "model_name": self.model_name,
        }
