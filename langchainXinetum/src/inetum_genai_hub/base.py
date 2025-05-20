import os
import time
from typing import Any, Dict, Literal, Optional, TypedDict
import uuid
import requests
from requests import Response

from interfaces import InetumGenerationModel


class ResponseDict(TypedDict):
    data: Any
    status: int
    headers: Dict[str, Any]


def ai_operation(func):
    def wrapper(self, *args, **kwargs) -> ResponseDict:
        response = func(self, *args, **kwargs)
        if response.status_code == 401:
            tokens = self.refresh_tokens()

            setattr(self, "access_token", tokens["accessToken"])
            setattr(self, "refresh_token", tokens["refreshToken"])
            self.headers["Authorization"] = f"Bearer {self.access_token}"
            # Retry the request with the new token
            response = func(self, *args, **kwargs)

        result: ResponseDict = {
            "data": response.json() if len(response.text) else None,
            "status": response.status_code,
            "headers": response.headers,
        }

        return result

    return wrapper


class BaseAgent:
    def __init__(
        self,
        agent_id: Optional[str],
        org_id: Optional[str],
        model: Optional[InetumGenerationModel] = None,
        temperature: float = 0.16,
    ):
        self.agent_id = agent_id
        self.organization_id = org_id

        self.conversation_uuid = str(uuid.uuid4())  # Create a default conversation
        self.agent_settings = {}
        self.base_url = os.environ["HUB_URL"]

        payload = {
            "username": os.environ["AUTH_USERNAME"],
            "password": os.environ["AUTH_PASSWORD"],
        }

        if agent_id and org_id:
            payload["agentId"] = agent_id
            payload["organizationId"] = org_id

        res = requests.post(self.base_url + "/account/login", json=payload)
        data = res.json()

        self.access_token = data.get("accessToken")
        self.refresh_token = data.get("refreshToken")

        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        settings = self._get_settings()

        if settings["status"] == 200:
            data = settings["data"]
            self.agent_settings = {
                "id": data["id"],
                "agentId": data["agentId"],
                "embeddingModelId": data["embeddingModelId"],
                "generationModelId": data["generationModelId"],
                "defaultPromptId": data["defaultPromptId"],
                "defaultPromptFlowId": data["defaultPromptFlowId"],
                "knowledgeSimilarityThreshold": data["knowledgeSimilarityThreshold"],
                "maximumKnowledgeItemsForAnswer": data[
                    "maximumKnowledgeItemsForAnswer"
                ],
                "minimumKnowledgeItemsForAnswer": data[
                    "minimumKnowledgeItemsForAnswer"
                ],
                "knowledgePrompt": data["knowledgePrompt"],
                "knowledgeLimitOverridePrompt": data["knowledgeLimitOverridePrompt"],
                "numberPreviousMessages": data["numberPreviousMessages"],
                "generationPromptText": data["generationPromptText"],
                "generationMaxTokens": data["generationMaxTokens"],
                "generationTemperature": data["generationTemperature"],
                "generationTopP": data["generationTopP"],
                "temperature": temperature,
            }

        if model:
            self.__set_model(model)

    def __set_model(self, model_name: InetumGenerationModel):
        res = self._get_agent()
        data = res["data"]

        model_id = None
        for model in data.get("generationModels", []):
            if (
                model.get("name") == model_name
                or model.get("displayName") == model_name
            ):
                model_id = model.get("id")

        if not model_id:
            raise ValueError("Model not found")

        self.agent_settings["generationModelId"] = model_id
        self._update_settings(self.agent_settings)

        return

    def refresh_tokens(self):
        """Refresh the access token.

        Returns:
            bool: operation status
        """

        try:
            payload = {
                "accessToken": self.access_token,
                "refreshToken": self.refresh_token,
            }

            res = requests.post(
                self.base_url + "/account/refresh-token",
                json=payload,
            )

            return res.json()

        except Exception as e:
            print(f"Error: {e}")
            return False

    @ai_operation
    def create_agent(self, name: str) -> Response:
        payload = {"name": name}

        res = requests.post(
            self.base_url + "/agent", json=payload, headers=self.headers
        )

        return res

    @ai_operation
    def get_agent(self, id: str):
        res = requests.get(self.base_url + "/agent/" + id, headers=self.headers)
        return res.json()

    @ai_operation
    def get_agents(self):
        res = requests.get(self.base_url + "/agent/", headers=self.headers)
        return res.json()

    @ai_operation
    def _create_prompt(
        self,
        name: str,
        prompt: str,
        group: str = "Default",
        type: Literal["System", "User"] = "System",
    ) -> Response:
        """Create a prompt.

        Args:
            prompt (str): prompt text

        Returns:
            dict: prompt details
        """
        if not name:
            raise ValueError("Prompt name is required")

        if not prompt:
            raise ValueError("Prompt text is required")

        if type not in ["System", "User"]:
            raise ValueError("Invalid prompt type")

        prompt_uuid = str(uuid.uuid4())

        payload = {
            "id": prompt_uuid,
            "name": name,  # Name of the prompt
            "text": prompt,  # The content of your prompt
            "group": group,  # You can group prompts
            "promptType": type,  # System or User
        }

        res = requests.post(
            self.base_url + "/prompt", json=payload, headers=self.headers
        )

        return res

    @ai_operation
    def _get_prompts(self) -> Response:
        """Get all prompts.

        Returns:
            dict: all prompts
        """
        res = requests.get(
            self.base_url + "/prompt",
            headers=self.headers,
        )
        return res

    @ai_operation
    def _get_prompt(self, id: str) -> Response:
        """Get prompt by id.

        Returns:
            dict: prompt details
        """

        res = requests.get(
            self.base_url + f"/prompt/{id}",
            headers=self.headers,
        )

        return res

    @ai_operation
    def __update_prompt(
        self, prompt_id: str, name: str, text: str, group: str, type: str
    ) -> Response:
        res = requests.put(
            self.base_url + f"/prompt/{prompt_id}",
            json={
                "name": name,
                "text": text,
                "group": group,
                "promptType": type,
            },
            headers=self.headers,
        )
        return res

    @ai_operation
    def _get_agent(self) -> Response:
        res = requests.get(
            self.base_url + f"/agent/{self.agent_id}",
            headers=self.headers,
        )
        return res

    @ai_operation
    def _get_settings(self) -> Response:
        res = requests.get(
            self.base_url + "/settings/get-agent-settings",
            headers=self.headers,
        )
        return res

    @ai_operation
    def _update_settings(self, settings: dict) -> Response:
        res = requests.put(
            self.base_url + f"/settings/{self.agent_settings['id']}",
            json=settings,
            headers=self.headers,
        )
        return res

    def _create_conversation(self):
        self.conversation_uuid = str(uuid.uuid4())

    @ai_operation
    def _get_conversation(self, conversation_id: Optional[str]) -> Response:
        res = None
        if not conversation_id:
            # Get the current conversation
            res = requests.get(
                self.base_url + f"/Chat/{self.conversation_uuid}", headers=self.headers
            )
            return res

        res = requests.get(
            self.base_url + f"/Chat/{conversation_id}", headers=self.headers
        )
        return res

    @ai_operation
    def __check_task_status(self, task_location: str) -> Response:
        res = requests.get(task_location, headers=self.headers)
        return res

    @ai_operation
    def _send_message(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        new_conversation: bool = False,
    ) -> Response:
        if new_conversation:
            self._create_conversation()

        payload = {
            "conversationId": self.conversation_uuid,
            "inputText": user_prompt,
        }

        if system_prompt:
            payload["userPrompt"] = system_prompt

        res = requests.post(
            self.base_url + "/Chat",
            json=payload,
            headers=self.headers,
        )

        return res

    def _wait_for_anwser(self, task_location: str):
        res = self.__check_task_status(task_location)
        data = res["data"]

        while data["status"] != "Failed" and data["status"] != "Succeeded":
            res = self.__check_task_status(task_location)
            data = res["data"]
            time.sleep(0.8)

        if data["status"] == "Failed":
            print("There was an error with the task")
            return False

        return True
