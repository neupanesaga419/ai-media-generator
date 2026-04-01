import io
import os
import logging

from google import genai
from google.genai import types
from PIL import Image

from .base import BaseImageGenerator

logger = logging.getLogger(__name__)


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

        generated_image_data = response.generated_images[0]
        image = Image.open(io.BytesIO(generated_image_data.image.image_bytes))

        output_buffer = io.BytesIO()
        image.save(output_buffer, format="PNG")
        return output_buffer.getvalue()

    @classmethod
    def fetch_available_models(cls, api_key: str) -> list[str]:
        """Call Google GenAI API to list all image generation models."""
        client = genai.Client(api_key=api_key)
        image_generation_models = []

        try:
            for model in client.models.list():
                model_name_lower = model.name.lower()
                # Only include actual Imagen generation models
                # e.g. "models/imagen-3.0-generate-002" — must have "imagen" AND "generate"
                # Excludes chat models like "gemini-2.5-flash-image" which can't generate images
                is_imagen_model = "imagen" in model_name_lower and "generate" in model_name_lower
                if is_imagen_model:
                    clean_model_name = model.name
                    if clean_model_name.startswith("models/"):
                        clean_model_name = clean_model_name[len("models/"):]
                    image_generation_models.append(clean_model_name)
        except Exception as fetch_error:
            logger.error(f"Failed to fetch Google models: {fetch_error}")

        return image_generation_models

    def get_default_params(self) -> dict:
        return {
            "aspect_ratio": "1:1",
        }
