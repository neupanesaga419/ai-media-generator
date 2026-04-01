from .google_image_generator import GoogleImageGenerator
from .grok_image_generator import GrokImageGenerator

IMAGE_PROVIDERS = {
    "google_imagen": GoogleImageGenerator,
    "grok": GrokImageGenerator,
}


def get_provider_api_key_env_variable(provider_name: str) -> str:
    """Return the environment variable name for a provider's API key."""
    provider_class = IMAGE_PROVIDERS.get(provider_name)
    if provider_class is None:
        return ""
    return provider_class.api_key_env_variable


def create_image_generator(provider_name: str):
    """Factory: instantiate an image generator by provider name."""
    provider_class = IMAGE_PROVIDERS.get(provider_name)
    if provider_class is None:
        available_providers = list(IMAGE_PROVIDERS.keys())
        raise ValueError(
            f"Unknown provider '{provider_name}'. "
            f"Available: {available_providers}"
        )
    return provider_class()
