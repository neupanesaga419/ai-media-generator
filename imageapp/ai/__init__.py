from .google_image_generator import GoogleImageGenerator
from .grok_image_generator import GrokImageGenerator

IMAGE_PROVIDERS = {
    "google_imagen": GoogleImageGenerator,
    "grok": GrokImageGenerator,
}

# Maps provider name to the env var that holds its API key
PROVIDER_API_KEY_ENV_VARS = {
    "google_imagen": "GOOGLE_API_KEY",
    "grok": "XAI_API_KEY",
}


def get_image_generator(provider_name: str):
    """Factory: get an image generator by provider name."""
    provider_class = IMAGE_PROVIDERS.get(provider_name)
    if provider_class is None:
        raise ValueError(
            f"Unknown provider '{provider_name}'. "
            f"Available: {list(IMAGE_PROVIDERS.keys())}"
        )
    return provider_class()
