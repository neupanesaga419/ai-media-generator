import os
from abc import ABC, abstractmethod


class BaseImageGenerator(ABC):
    """Base class for all image generation AI modules."""

    name: str = "base"
    description: str = ""

    def get_api_key(self, environment_variable_name: str) -> str:
        """Read API key from environment variables."""
        api_key = os.getenv(environment_variable_name, "")
        if not api_key:
            raise ValueError(
                f"API key not found. Set {environment_variable_name} in your .env file."
            )
        return api_key

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> bytes:
        """Generate an image from a text prompt. Returns raw image bytes."""
        ...

    @classmethod
    @abstractmethod
    def fetch_available_models(cls, api_key: str) -> list[str]:
        """Call the provider API to discover image generation models.
        This is used to populate the CachedModel table."""
        ...

    def get_default_params(self) -> dict:
        """Return default generation parameters."""
        return {}
