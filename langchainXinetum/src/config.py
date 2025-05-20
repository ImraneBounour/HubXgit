import os
from typing import TypedDict

from src.interfaces import InetumGenerationModel


class DefaultConfig(TypedDict):
    api_url: str
    api_key: str
    model_name: InetumGenerationModel
    polling_interval: float
    max_retries: int
    timeout: int


DEFAULT_CONFIG: DefaultConfig = {
    "api_url": "https://playground.inetum.group/api",
    "model_name": "inetum-gpt4o",
    "api_key": os.getenv("INETUM_GENAI_API_KEY", ""),
    "polling_interval": 0.8,
    "max_retries": 3,
    "timeout": 30,
}
