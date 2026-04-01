import base64
import logging
import os

import requests

from .base import BaseImageGenerator

logger = logging.getLogger(__name__)


class GrokImageGenerator(BaseImageGenerator):
    """xAI Grok image generator using the xAI API."""

    name = "grok"
    description = "Grok (xAI) Image Generation"

    MODELS_LIST_URL = "https://api.x.ai/v1/models"
    IMAGE_GENERATION_URL = "https://api.x.ai/v1/images/generations"

    def __init__(self):
        self.api_key = self.get_api_key("XAI_API_KEY")

    def generate(self, prompt: str, **kwargs) -> bytes:
        model_name = kwargs.get("model_name", "grok-2-image")
        width = kwargs.get("width", 1024)
        height = kwargs.get("height", 1024)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model_name,
            "prompt": prompt,
            "n": 1,
            "size": f"{width}x{height}",
        }

        response = requests.post(
            self.IMAGE_GENERATION_URL,
            headers=headers,
            json=payload,
            timeout=120,
        )
        response.raise_for_status()

        response_data = response.json()
        image_data = response_data["data"][0]

        if "b64_json" in image_data:
            return base64.b64decode(image_data["b64_json"])
        elif "url" in image_data:
            image_download_response = requests.get(image_data["url"], timeout=60)
            image_download_response.raise_for_status()
            return image_download_response.content
        else:
            raise RuntimeError("Grok API returned no image data.")

    @classmethod
    def fetch_available_models(cls, api_key: str) -> list[str]:
        """Call xAI API to list all models, filter for image generation ones."""
        headers = {
            "Authorization": f"Bearer {api_key}",
        }

        image_generation_models = []

        try:
            response = requests.get(
                cls.MODELS_LIST_URL,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()

            all_models = response.json().get("data", [])
            for model in all_models:
                model_id = model.get("id", "")
                # Filter for image-capable models
                if "image" in model_id.lower():
                    image_generation_models.append(model_id)
        except Exception as fetch_error:
            logger.error(f"Failed to fetch xAI models: {fetch_error}")

        return image_generation_models

    def get_default_params(self) -> dict:
        return {
            "width": 1024,
            "height": 1024,
        }
