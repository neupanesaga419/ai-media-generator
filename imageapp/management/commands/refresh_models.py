import os
import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from imageapp.ai import IMAGE_PROVIDERS, PROVIDER_API_KEY_ENV_VARS
from imageapp.models import CachedModel

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Fetch available image generation models from all provider APIs and update the local cache."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force refresh even if cache is not stale.",
        )
        parser.add_argument(
            "--provider",
            type=str,
            default=None,
            help="Only refresh a specific provider (e.g., google_imagen, grok).",
        )

    def handle(self, *args, **options):
        force_refresh = options["force"]
        specific_provider = options.get("provider")

        providers_to_refresh = IMAGE_PROVIDERS.items()
        if specific_provider:
            if specific_provider not in IMAGE_PROVIDERS:
                self.stderr.write(
                    f"Unknown provider '{specific_provider}'. "
                    f"Available: {list(IMAGE_PROVIDERS.keys())}"
                )
                return
            providers_to_refresh = [
                (specific_provider, IMAGE_PROVIDERS[specific_provider])
            ]

        for provider_name, provider_class in providers_to_refresh:
            # Check if cache needs refreshing
            if not force_refresh and not CachedModel.is_cache_stale(provider_name):
                self.stdout.write(
                    f"[{provider_name}] Cache is fresh, skipping. Use --force to override."
                )
                continue

            # Get API key for this provider
            api_key_env_var = PROVIDER_API_KEY_ENV_VARS.get(provider_name, "")
            api_key = os.getenv(api_key_env_var, "")

            if not api_key:
                self.stderr.write(
                    f"[{provider_name}] No API key found ({api_key_env_var}). Skipping."
                )
                continue

            self.stdout.write(f"[{provider_name}] Fetching models from API...")

            try:
                fetched_model_ids = provider_class.fetch_available_models(api_key)
            except Exception as fetch_error:
                self.stderr.write(
                    f"[{provider_name}] Failed to fetch models: {fetch_error}"
                )
                continue

            if not fetched_model_ids:
                self.stderr.write(
                    f"[{provider_name}] API returned no image generation models."
                )
                continue

            # Mark all existing models for this provider as unavailable first
            CachedModel.objects.filter(provider=provider_name).update(is_available=False)

            # Upsert each fetched model
            for model_id in fetched_model_ids:
                CachedModel.objects.update_or_create(
                    provider=provider_name,
                    model_id=model_id,
                    defaults={
                        "display_name": model_id,
                        "capability": "image_generation",
                        "is_available": True,
                        "fetched_at": timezone.now(),
                    },
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"[{provider_name}] Cached {len(fetched_model_ids)} models: "
                    f"{', '.join(fetched_model_ids)}"
                )
            )

        self.stdout.write(self.style.SUCCESS("Model refresh complete."))
