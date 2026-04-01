import base64
import io
import os

import requests

from .base import BaseImageGenerator


class GrokImageGenerator(BaseImageGenerator):
    """xAI Grok image generator using the xAI API."""

    name = "grok"
    description = "Grok (xAI) Image Generation"

    def __init__(self):
        self.api_key = self.get_api_key("XAI_API_KEY")
        self.api_base_url = "https://api.x.ai/v1/images/generations"

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
            self.api_base_url,
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
            image_response = requests.get(image_data["url"], timeout=60)
            image_response.raise_for_status()
            return image_response.content
        else:
            raise RuntimeError("Grok API returned no image data.")

    def get_available_models(self) -> list[str]:
        return ["grok-2-image"]

    def get_default_params(self) -> dict:
        return {
            "width": 1024,
            "height": 1024,
            "model_name": "grok-2-image",
        }
