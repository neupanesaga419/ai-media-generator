import base64
import logging

import requests

from .base import BaseImageGenerator

logger = logging.getLogger(__name__)

XAI_MODELS_URL = "https://api.x.ai/v1/models"
XAI_IMAGE_GENERATION_URL = "https://api.x.ai/v1/images/generations"
XAI_REQUEST_TIMEOUT_SECONDS = 120
XAI_MODELS_FETCH_TIMEOUT_SECONDS = 30


class GrokImageGenerator(BaseImageGenerator):
    """xAI Grok image generator using the xAI REST API."""

    provider_name = "grok"
    display_name = "Grok (xAI) Image Generation"
    api_key_env_variable = "XAI_API_KEY"

    def __init__(self):
        self.api_key = self._load_api_key()

    def generate(self, prompt: str, **kwargs) -> bytes:
        model_name = kwargs.get("model_name", "grok-imagine-image")

        request_headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        request_payload = {
            "model": model_name,
            "prompt": prompt,
            "n": 1,
            "response_format": "b64_json",
        }

        response = requests.post(
            XAI_IMAGE_GENERATION_URL,
            headers=request_headers,
            json=request_payload,
            timeout=XAI_REQUEST_TIMEOUT_SECONDS,
        )

        if not response.ok:
            raise RuntimeError(
                f"xAI API error ({response.status_code}): {response.text}"
            )

        image_entry = response.json()["data"][0]
        return self._extract_image_bytes(image_entry)

    @staticmethod
    def _extract_image_bytes(image_entry: dict) -> bytes:
        """Extract image bytes from an xAI API response entry."""
        if "b64_json" in image_entry:
            return base64.b64decode(image_entry["b64_json"])

        if "url" in image_entry:
            download_response = requests.get(
                image_entry["url"],
                timeout=XAI_REQUEST_TIMEOUT_SECONDS,
            )
            download_response.raise_for_status()
            return download_response.content

        raise RuntimeError("xAI API response contained no image data.")

    @classmethod
    def fetch_available_models(cls, api_key: str) -> list[str]:
        """Fetch image generation models from the xAI API."""
        request_headers = {"Authorization": f"Bearer {api_key}"}

        try:
            response = requests.get(
                XAI_MODELS_URL,
                headers=request_headers,
                timeout=XAI_MODELS_FETCH_TIMEOUT_SECONDS,
            )
            response.raise_for_status()

            all_models = response.json().get("data", [])
            return [
                model.get("id")
                for model in all_models
                if "image" in model.get("id", "").lower()
            ]
        except Exception as error:
            logger.error("Failed to fetch xAI models: %s", error)
            return []
