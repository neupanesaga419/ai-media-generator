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

    def _load_service_account(self):
        service_account_var_name = "GOOGLE_SERVICE_ACCOUNT_PATH"
        service_account = os.getenv(service_account_var_name,"")
        if not service_account:
            raise ValueError(
                f"Service Account File Not found"
                f"Set {service_account_var_name} in your .env file"
            )
        return service_account

    def _load_project_id(self):
        project_id_var = "GOOGLE_CLOUD_PROJECT"
        project_id = os.getenv(project_id_var,"")
        if not project_id:
            raise ValueError(
                f"Google Cloud Project ID not found"
                f"Set {project_id_var} in your .env file"
            )
        return project_id


    def _load_google_cloud_location(self):
        location_var = "GOOGLE_CLOUD_LOCATION"
        google_cloud_location = os.getenv(location_var,"")
        if not google_cloud_location:
            raise ValueError(
                f"Google Cloud Location Not found"
                f"Set {location_var} in your .env file"
            )
        return google_cloud_location
    

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> bytes:
        """Generate an image from a text prompt. Returns raw PNG bytes."""
        ...

    @classmethod
    @abstractmethod
    def fetch_available_models(cls, api_key: str) -> list[str]:
        """Call the provider API to discover available image generation models."""
        ...
