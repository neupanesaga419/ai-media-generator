import os
from abc import ABC, abstractmethod


class BaseImageGenerator(ABC):
    """Base class for all image generation AI modules."""

    name: str = "base"
    description: str = ""

    def get_api_key(self, env_variable_name: str) -> str:
        """Read API key from environment variables."""
        api_key = os.getenv(env_variable_name, "")
        if not api_key:
            raise ValueError(
                f"API key not found. Set {env_variable_name} in your .env file."
            )
        return api_key

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> bytes:
        """Generate an image from a text prompt. Returns raw image bytes."""
        ...

    @abstractmethod
    def get_available_models(self) -> list[str]:
        """Return list of available model names for this provider."""
        ...

    def get_default_params(self) -> dict:
        """Return default generation parameters."""
        return {
            "width": 1024,
            "height": 1024,
        }
