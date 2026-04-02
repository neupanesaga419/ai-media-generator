import json
import uuid

from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .ai import IMAGE_PROVIDERS, create_image_generator
from .model_cache import get_all_cached_provider_models
from .models import GeneratedImage
from .prompt_constants import PROMPT_PRESETS


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
    prompt_presets_json = json.dumps(PROMPT_PRESETS)
    return render(request, "imageapp/generate.html", {
        "providers": providers_list,
        "provider_models_json": provider_models_json,
        "prompt_presets_json": prompt_presets_json,
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
    prompt = request.POST.get("prompt", "").strip()
    if not prompt:
        return JsonResponse({"error": "Prompt is required."}, status=400)

    provider_name = request.POST.get("provider", "google_imagen")
    model_name = request.POST.get("model_name", "")
    negative_prompt = request.POST.get("negative_prompt", "")
    input_image = request.FILES.get("imputImageFile")
    print(input_image,"Inpit iamge")

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
        if input_image:
            generation_kwargs["input_image"] = input_image

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
