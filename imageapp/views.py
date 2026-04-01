import json
import uuid

from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .ai import IMAGE_PROVIDERS, create_image_generator
from .model_cache import get_all_cached_provider_models
from .models import GeneratedImage


def _build_provider_context() -> tuple[list[dict], str]:
    """Build provider list and JSON model map for template rendering.

    Returns:
        A tuple of (providers_list, provider_models_json).
    """
    cached_models_by_provider = get_all_cached_provider_models()

    providers_list = [
        {
            "key": provider_key,
            "name": provider_class.display_name,
            "models": cached_models_by_provider.get(provider_key, []),
        }
        for provider_key, provider_class in IMAGE_PROVIDERS.items()
    ]

    provider_models_json = json.dumps({
        provider["key"]: provider["models"]
        for provider in providers_list
    })

    return providers_list, provider_models_json


# -- Page views ---------------------------------------------------------------


def generate_page(request):
    """Render the image generation form."""
    providers_list, provider_models_json = _build_provider_context()
    return render(request, "imageapp/generate.html", {
        "providers": providers_list,
        "provider_models_json": provider_models_json,
    })


def gallery_page(request):
    """Show all successfully generated images."""
    completed_images = GeneratedImage.objects.filter(status="completed")
    return render(request, "imageapp/gallery.html", {
        "images": completed_images,
    })


# -- API endpoints ------------------------------------------------------------


@require_POST
def api_generate_image(request):
    """Accept a generation request, run the provider, and return the result."""
    try:
        request_body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    prompt = request_body.get("prompt", "").strip()
    if not prompt:
        return JsonResponse({"error": "Prompt is required."}, status=400)

    provider_name = request_body.get("provider", "google_imagen")
    model_name = request_body.get("model_name", "")
    negative_prompt = request_body.get("negative_prompt", "")

    image_record = GeneratedImage.objects.create(
        prompt=prompt,
        negative_prompt=negative_prompt,
        provider=provider_name,
        model_name=model_name,
        status="processing",
    )

    try:
        generator = create_image_generator(provider_name)

        generation_kwargs = {}
        if model_name:
            generation_kwargs["model_name"] = model_name

        generated_image_bytes = generator.generate(prompt, **generation_kwargs)

        filename = f"{provider_name}_{uuid.uuid4().hex[:8]}.png"
        image_record.image.save(
            filename, ContentFile(generated_image_bytes), save=False
        )
        image_record.status = "completed"
        image_record.save()

        return JsonResponse({
            "id": image_record.id,
            "status": "completed",
            "image_url": image_record.image.url,
            "prompt": image_record.prompt,
            "provider": image_record.provider,
            "model_name": image_record.model_name,
        })

    except Exception as generation_error:
        image_record.status = "failed"
        image_record.error_message = str(generation_error)
        image_record.save()

        return JsonResponse({
            "id": image_record.id,
            "status": "failed",
            "error": str(generation_error),
        }, status=500)


def api_list_providers(request):
    """Return available providers and their cached models as JSON."""
    providers_list, _ = _build_provider_context()
    return JsonResponse({"providers": providers_list})
