from typing import Literal, Optional, Union

from src.inetum_genai_hub.base import BaseAgent, Model


class AIAgent(BaseAgent):
    def __init__(self, agent_id: str, org_id: str, model: Optional[Model] = None, temperature: float = 0.16):

        if not agent_id:
            raise ValueError("Agent ID is required")

        if not org_id:
            raise ValueError("Organization ID is required")

        super().__init__(agent_id, org_id, model, temperature)

    def create_agent(self, name: str):
        raise NotImplementedError(
            "You cannot create agent while being logged in an agent"
        )

    def get_agents(self):
        raise NotImplementedError(
            "You cannot get agents while being logged in an agent"
        )

    def get_current_prompt(self):

        if not self.agent_settings["defaultPromptId"]:
            return None

        return self._get_prompt(self.agent_settings["defaultPromptId"])["data"]

    def create_prompt(
        self,
        name: str,
        text: str,
        group: str = "Default",
        type: Literal["System", "User"] = "System",
    ):
        return self._create_prompt(name, text, group, type)["data"]

    def update_prompt(
        self, prompt_id: str, name: str, text: str, group: str, type: str
    ):
        return self.__update_prompt(prompt_id, name, text, group, type)

    def get_prompt(self, prompt_id: str):
        return self._get_prompt(prompt_id)["data"]

    def get_prompts(self):
        return self._get_prompts()["data"]

    def assign_prompt(self, prompt_id: str):
        # Check if the prompt exists
        prompt = self._get_prompt(prompt_id)["data"]

        self.agent_settings["defaultPromptId"] = prompt["id"]

        self._update_settings(self.agent_settings)

    def get_agent(self):
        return self._get_agent()["data"]

    def get_settings(self):
        return self._get_settings()["data"]

    def update_settings(self, settings: dict):
        return self._update_settings(settings)

    def create_conversation(self):
        return self._create_conversation()

    def get_conversation(self, conversation_id: Optional[str] = None):

        if not conversation_id:
            data = self._get_conversation(self.conversation_uuid)
            return data["data"]

        data = self._get_conversation(conversation_id)
        return data["data"]

    def chat(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        new_conversation: bool = False,
    ) -> Union[str, None]:

        res = self._send_message(user_prompt, system_prompt, new_conversation)
        
        task_location = res["headers"]["Location"]
        task_succeeded = self._wait_for_anwser(task_location)

        if task_succeeded:
            data = self._get_conversation(self.conversation_uuid)["data"]
            return data["messages"][-1]["text"]

        return None
