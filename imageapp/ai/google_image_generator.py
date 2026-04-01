import io
import os

from google import genai
from google.genai import types
from PIL import Image

from .base import BaseImageGenerator


class GoogleImageGenerator(BaseImageGenerator):
    """Google Imagen image generator using google-genai SDK."""

    name = "google_imagen"
    description = "Google Imagen (via Gemini API)"

    def __init__(self):
        api_key = self.get_api_key("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=api_key)

    def generate(self, prompt: str, **kwargs) -> bytes:
        model_name = kwargs.get("model_name", "imagen-3.0-generate-002")
        aspect_ratio = kwargs.get("aspect_ratio", "1:1")

        response = self.client.models.generate_images(
            model=model_name,
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio=aspect_ratio,
            ),
        )

        if not response.generated_images:
            raise RuntimeError("Google Imagen returned no images.")

        generated_image = response.generated_images[0]
        image = Image.open(io.BytesIO(generated_image.image.image_bytes))

        output_buffer = io.BytesIO()
        image.save(output_buffer, format="PNG")
        return output_buffer.getvalue()

    def get_available_models(self) -> list[str]:
        return [
            "imagen-3.0-generate-002",
            "imagen-3.0-fast-generate-001",
        ]

    def get_default_params(self) -> dict:
        return {
            "aspect_ratio": "1:1",
            "model_name": "imagen-3.0-generate-002",
        }
