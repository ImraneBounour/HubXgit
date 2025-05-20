import json
import time
from typing import Optional
import uuid

from pydantic import SecretStr
import requests

from src.config import DEFAULT_CONFIG
from src.interfaces import InetumGenerationModel
import aiohttp
import asyncio

from dotenv import load_dotenv

load_dotenv()


class InetumSDK:
    def __init__(
        self,
        api_key: SecretStr,
        base_url: str,
        model: InetumGenerationModel,
        temperature: Optional[float],
        top_p: Optional[float],
        max_tokens: Optional[int],
    ) -> None:
        print("Initializing Inetum SDK...")
        self.api_key = api_key
        self.base_url = base_url

        self.headers = {
            "Authorization": f"Bearer {api_key.get_secret_value()}",
            "Content-Type": "application/json",
            "Accept": "*/*",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",  # Fake user agent to avoid blocking
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

        settings_response = self.__fetch_settings()

        if settings_response.status_code == 401:
            raise Exception("Invalid API key. Please check your credentials.")
        elif settings_response.status_code != 200:
            raise Exception(
                f"Error fetching settings: {settings_response.status_code} - {settings_response.text}"
            )
        self.settings = settings_response.json()
        self.agent_id = self.settings["agentId"]

        self.__initialize_model(model, temperature, top_p, max_tokens)

        print("Inetum SDK initialized successfully. \n")

    def __get_agent(self):
        res = requests.get(
            self.base_url + f"/agent/{self.agent_id}",
            headers=self.headers,
        )

        return res.json()

    def __fetch_settings(self):
        res = requests.get(
            self.base_url + "/settings/get-agent-settings",
            headers=self.headers,
        )
        return res

    def __initialize_model(
        self,
        model_name: InetumGenerationModel,
        temperature: Optional[float],
        top_p: Optional[float],
        max_tokens: Optional[int],
    ):
        agent_settings = self.__get_agent()

        model_id = None
        for model in agent_settings.get("generationModels", []):
            if (
                model.get("name") == model_name
                or model.get("displayName") == model_name
            ):
                model_id = model.get("id")
        if not model_id:
            raise Exception(f"Model {model_name} not found.")

        self.settings["generationModelId"] = model_id

        if temperature is not None:
            self.settings["generationTemperature"] = temperature

        if top_p is not None:
            self.settings["generationTopP"] = top_p

        if max_tokens is not None:
            self.settings["generationMaxTokens"] = max_tokens

        self.__update_settings(self.settings)

    def __update_settings(self, settings: dict):
        res = requests.put(
            self.base_url + f"/settings/{self.settings['id']}",
            json=settings,
            headers=self.headers,
        )

        if res.status_code != 200:
            raise Exception(f"Error updating settings: {res.text}")
        return res.json()

    def wait_for_response(
        self,
        task_location: str,
        polling_interval: float,
        timeout: int,
    ) -> None:
        """Wait for the response from the Inetum GenAI Hub."""

        start_time = time.time()

        while True:
            elapsed_time = time.time() - start_time

            if elapsed_time > timeout:
                raise Exception("Timeout waiting for response.")

            res = requests.get(task_location, headers=self.headers)

            if res.status_code != 200:
                raise Exception(f"Error checking task status: {res.text}")

            data = res.json()

            if data["status"] == "Failed":
                raise Exception(f"Task failed: {data}")
            elif data["status"] == "Succeeded":
                return

            time.sleep(polling_interval)

    async def wait_for_response_async(
        self,
        session: aiohttp.ClientSession,
        task_location: str,
        polling_interval: float = DEFAULT_CONFIG["polling_interval"],
        timeout: int = DEFAULT_CONFIG["timeout"],
    ) -> None:
        """Wait for the response from the Inetum GenAI Hub asynchronously."""

        start_time = time.time()
        while True:
            # Check if the timeout has been reached
            elapsed_time = time.time() - start_time

            if elapsed_time > timeout:
                raise Exception("Timeout waiting for response.")

            # Check the status of the task
            async with session.get(task_location) as res:
                if res.status != 200:
                    raise Exception(f"Error checking task status: {await res.text()}")

                data = await res.json()

                if data["status"] == "Failed":
                    raise Exception(f"Task failed: {data['error']}")
                elif data["status"] == "Succeeded":
                    return

                await asyncio.sleep(polling_interval)

    def generate(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        polling_interval: float = DEFAULT_CONFIG["polling_interval"],
        timeout: int = DEFAULT_CONFIG["timeout"],
        **kwargs,
    ) -> str:
        """Generate a response from the Inetum GenAI Hub.

        Args:
            user_prompt (str): the user prompt
            system_prompt (Optional[str], optional): system prompt. Defaults to None.
            **kwargs: additional parameters for the request.

        Raises:
            Exception: _description_
            Exception: _description_
            Exception: _description_
            Exception: _description_

        Returns:
            str: _description_
        """

        # Generate a new conversation ID
        conversation_id = str(uuid.uuid4())

        payload = {
            "conversationId": conversation_id,
            "inputText": user_prompt,
        }

        if system_prompt:
            payload["userPrompt"] = system_prompt

        res = requests.post(
            self.base_url + "/Chat",
            json=payload,
            headers=self.headers,
        )

        if res.status_code != 202:
            raise Exception(f"Error sending message: {res.text}")

        task_location = res.headers["Location"]

        if not task_location:
            raise Exception("No task location found in the response headers.")

        # Wait for the response
        self.wait_for_response(
            task_location,
            polling_interval=polling_interval,
            timeout=timeout,
        )

        # Get the conversation data
        res = requests.get(
            self.base_url + f"/Chat/{conversation_id}", headers=self.headers
        )
        if res.status_code != 200:
            raise Exception(f"Error getting conversation data: {res.text}")
        data = res.json()

        if "messages" not in data:
            raise Exception("No messages found in the conversation data.")

        # Check if the response contains the expected data
        return data["messages"][-1]["text"]

    async def generate_async(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Generate a response from the Inetum GenAI Hub asynchronously.

        Args:
            user_prompt (str): the user prompt
            system_prompt (Optional[str], optional): system prompt. Defaults to None.

        Raises:
            Exception: _description_
            Exception: _description_
            Exception: _description_
            Exception: _description_

        Returns:
            str: _description_
        """

        # Generate a new conversation ID
        conversation_id = str(uuid.uuid4())

        payload = {
            "conversationId": conversation_id,
            "inputText": user_prompt,
        }

        if system_prompt:
            payload["userPrompt"] = system_prompt

        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(
                self.base_url + "/Chat",
                json=payload,
            ) as res:
                if res.status != 202:
                    raise Exception(f"Error sending message: {await res.text()}")

                task_location = res.headers.get("Location")

                if not task_location:
                    raise Exception("No task location found in the response headers.")

                # Wait for the response
                await self.wait_for_response_async(session, task_location)

                # Get the conversation data
                async with session.get(
                    self.base_url + f"/Chat/{conversation_id}"
                ) as res:
                    if res.status != 200:
                        raise Exception(
                            f"Error getting conversation data: {await res.text()}"
                        )
                    data = await res.json()

                    if "messages" not in data:
                        raise Exception("No messages found in the conversation data.")

                    # Check if the response contains the expected data
                    return data["messages"][-1]["text"]
