import io
import logging

from google import genai
from google.genai import types
from PIL import Image
from google.oauth2 import service_account
from .base import BaseImageGenerator

logger = logging.getLogger(__name__)

GOOGLE_MODELS_PREFIX = "models/"


def _convert_raw_image_to_png(raw_image_bytes: bytes) -> bytes:
    """Convert raw image bytes (any format) to PNG bytes."""
    image = Image.open(io.BytesIO(raw_image_bytes))
    output_buffer = io.BytesIO()
    image.save(output_buffer, format="PNG")
    return output_buffer.getvalue()


def _is_gemini_model(model_name: str) -> bool:
    """Gemini models use the generateContent API."""
    return "gemini" in model_name.lower()


def _is_image_generation_model(model_name: str) -> bool:
    """Check if a model name corresponds to an image generation model."""
    name_lower = model_name.lower()
    is_imagen = "imagen" in name_lower and "generate" in name_lower
    is_gemini_image = "gemini" in name_lower and "image" in name_lower
    return is_imagen or is_gemini_image


def _strip_models_prefix(model_name: str) -> str:
    """Remove the 'models/' prefix from Google model names."""
    if model_name.startswith(GOOGLE_MODELS_PREFIX):
        return model_name[len(GOOGLE_MODELS_PREFIX):]
    return model_name


class GoogleImageGenerator(BaseImageGenerator):
    """Google image generator supporting both Imagen and Gemini image models."""

    provider_name = "google_imagen"
    display_name = "Google Imagen (via Gemini API)"
    api_key_env_variable = "GOOGLE_API_KEY"
    SCOPES = ['https://www.googleapis.com/auth/cloud-platform']

    def __init__(self):
        # api_key = self._load_api_key()
        service_account_file = self._load_service_account()
        project_id = self._load_project_id()
        google_cloud_location = self._load_google_cloud_location()
        creds = self._get_credentials(service_account_file=service_account_file)
        self.client = genai.Client(
                                    vertexai=True,
                              
                                    project=project_id,
                                    location=google_cloud_location,
                                    credentials=creds
                                   )


    def _get_credentials(self,service_account_file):
        
        creds = service_account.Credentials.from_service_account_file(filename=service_account_file,scopes=self.SCOPES)
        return creds

    def generate(self, prompt: str, **kwargs) -> bytes:
        model_name = kwargs.get("model_name", "imagen-4.0-generate-001")
        print(model_name,"Model name")

        if _is_gemini_model(model_name):
            return self._generate_with_gemini(prompt, model_name)
        return self._generate_with_imagen(prompt, model_name, kwargs)

    def _generate_with_gemini(self, prompt: str, model_name: str) -> bytes:
        """Generate image using Gemini's generateContent API."""
        response = self.client.models.generate_content(
            model=model_name,
            
            contents=[types.Content(parts=[types.Part(text=prompt)])],
            config=types.GenerateContentConfig(
                response_modalities=["image", "text"],
                
            ),
        )
        return self._extract_image_from_gemini_response(response)

    def _generate_with_imagen(
        self, prompt: str, model_name: str, kwargs: dict
    ) -> bytes:
        """Generate image using Imagen's generateImages API."""
        aspect_ratio = kwargs.get("aspect_ratio", "1:1")

        response = self.client.models.generate_images(
            model=model_name,
            prompt=prompt,
        
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio=aspect_ratio,
                negative_prompt="lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry."
            ),
        )

        if not response.generated_images:
            raise RuntimeError("Imagen returned no images.")

        raw_bytes = response.generated_images[0].image.image_bytes
        return _convert_raw_image_to_png(raw_bytes)

    def _extract_image_from_gemini_response(self, response) -> bytes:
        """Extract the first image from a Gemini generateContent response."""
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                return _convert_raw_image_to_png(part.inline_data.data)
        raise RuntimeError("Gemini did not return an image in the response.")

    @classmethod
    def fetch_available_models(cls, api_key: str) -> list[str]:
        """Fetch image generation models from the Google GenAI API."""
        client = genai.Client(api_key=api_key)
        available_models = []

        try:
            for model in client.models.list():
                if _is_image_generation_model(model.name):
                    clean_name = _strip_models_prefix(model.name)
                    available_models.append(clean_name)
        except Exception as error:
            logger.error("Failed to fetch Google models: %s", error)

        return available_models
