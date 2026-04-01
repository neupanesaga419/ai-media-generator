import os
from abc import ABC, abstractmethod


class BaseImageGenerator(ABC):
    """Abstract base class that all image generation providers must implement."""

    provider_name: str = "base"
    display_name: str = ""
    api_key_env_variable: str = ""

    def _load_api_key(self) -> str:
        """Load the API key from the environment variable defined by the provider."""
        api_key = os.getenv(self.api_key_env_variable, "")
        if not api_key:
            raise ValueError(
                f"API key not found. "
                f"Set {self.api_key_env_variable} in your .env file."
            )
        return api_key

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> bytes:
        """Generate an image from a text prompt. Returns raw PNG bytes."""
        ...

    @classmethod
    @abstractmethod
    def fetch_available_models(cls, api_key: str) -> list[str]:
        """Call the provider API to discover available image generation models."""
        ...
