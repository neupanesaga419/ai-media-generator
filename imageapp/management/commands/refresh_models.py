import os

from django.core.management.base import BaseCommand

from imageapp.ai import IMAGE_PROVIDERS, get_provider_api_key_env_variable
from imageapp.model_cache import upsert_provider_models
from imageapp.models import CachedModel


class Command(BaseCommand):
    help = (
        "Fetch available image generation models from provider APIs "
        "and update the local cache."
    )

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
            help="Only refresh a specific provider (e.g. google_imagen, grok).",
        )

    def handle(self, *args, **options):
        force_refresh = options["force"]
        target_provider = options.get("provider")

        providers_to_refresh = self._resolve_providers(target_provider)
        if providers_to_refresh is None:
            return

        for provider_name, provider_class in providers_to_refresh:
            self._refresh_single_provider(
                provider_name, provider_class, force_refresh
            )

        self.stdout.write(self.style.SUCCESS("Model refresh complete."))

    def _resolve_providers(self, target_provider):
        """Return the list of (name, class) pairs to refresh."""
        if target_provider is None:
            return list(IMAGE_PROVIDERS.items())

        if target_provider not in IMAGE_PROVIDERS:
            self.stderr.write(
                f"Unknown provider '{target_provider}'. "
                f"Available: {list(IMAGE_PROVIDERS.keys())}"
            )
            return None

        return [(target_provider, IMAGE_PROVIDERS[target_provider])]

    def _refresh_single_provider(
        self, provider_name, provider_class, force_refresh
    ):
        """Fetch and cache models for one provider."""
        if not force_refresh and not CachedModel.is_cache_stale(provider_name):
            self.stdout.write(
                f"[{provider_name}] Cache is fresh, skipping. "
                f"Use --force to override."
            )
            return

        api_key_env_variable = get_provider_api_key_env_variable(provider_name)
        api_key = os.getenv(api_key_env_variable, "")

        if not api_key:
            self.stderr.write(
                f"[{provider_name}] No API key ({api_key_env_variable}). "
                f"Skipping."
            )
            return

        self.stdout.write(f"[{provider_name}] Fetching models from API...")

        try:
            fetched_model_ids = provider_class.fetch_available_models(api_key)
        except Exception as error:
            self.stderr.write(
                f"[{provider_name}] Failed to fetch models: {error}"
            )
            return

        if not fetched_model_ids:
            self.stderr.write(
                f"[{provider_name}] API returned no image generation models."
            )
            return

        upsert_provider_models(provider_name, fetched_model_ids)
        self.stdout.write(
            self.style.SUCCESS(
                f"[{provider_name}] Cached {len(fetched_model_ids)} models: "
                f"{', '.join(fetched_model_ids)}"
            )
        )
