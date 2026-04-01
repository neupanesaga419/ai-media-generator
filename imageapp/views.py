import json
import uuid

from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .ai import IMAGE_PROVIDERS, get_image_generator
from .model_cache import get_all_provider_models
from .models import GeneratedImage


def generate_page(request):
    """Render the image generation form page."""
    provider_models = get_all_provider_models()

    providers = []
    for provider_key, provider_class in IMAGE_PROVIDERS.items():
        providers.append({
            "key": provider_key,
            "name": provider_class.description,
            "models": provider_models.get(provider_key, []),
        })

    provider_models_json = json.dumps({
        provider["key"]: provider["models"]
        for provider in providers
    })

    return render(request, "imageapp/generate.html", {
        "providers": providers,
        "provider_models_json": provider_models_json,
    })


def gallery_page(request):
    """Show all generated images."""
    images = GeneratedImage.objects.filter(status="completed")
    return render(request, "imageapp/gallery.html", {"images": images})


@require_POST
def api_generate_image(request):
    """API endpoint: generate an image and return the result."""
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    prompt = body.get("prompt", "").strip()
    if not prompt:
        return JsonResponse({"error": "Prompt is required"}, status=400)

    provider_name = body.get("provider", "google_imagen")
    model_name = body.get("model_name", "")

    image_record = GeneratedImage.objects.create(
        prompt=prompt,
        negative_prompt=body.get("negative_prompt", ""),
        provider=provider_name,
        model_name=model_name,
        status="processing",
    )

    try:
        generator = get_image_generator(provider_name)
        generation_kwargs = {}
        if model_name:
            generation_kwargs["model_name"] = model_name

        image_bytes = generator.generate(prompt, **generation_kwargs)

        filename = f"{provider_name}_{uuid.uuid4().hex[:8]}.png"
        image_record.image.save(filename, ContentFile(image_bytes), save=False)
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
    """API endpoint: list available image generation providers and their cached models."""
    provider_models = get_all_provider_models()
    providers_list = []

    for provider_key, provider_class in IMAGE_PROVIDERS.items():
        providers_list.append({
            "key": provider_key,
            "name": provider_class.description,
            "models": provider_models.get(provider_key, []),
        })

    return JsonResponse({"providers": providers_list})
