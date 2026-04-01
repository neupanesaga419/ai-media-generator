import os
import logging
import threading

from django.utils import timezone

from .ai import IMAGE_PROVIDERS, PROVIDER_API_KEY_ENV_VARS
from .models import CachedModel

logger = logging.getLogger(__name__)

# Track ongoing refresh threads to avoid duplicate refreshes
_refresh_lock = threading.Lock()
_refresh_in_progress = set()


def get_cached_models_for_provider(provider_name):
    """Return cached model IDs for a provider. Triggers background refresh if stale."""
    if CachedModel.is_cache_stale(provider_name):
        _trigger_background_refresh(provider_name)

    return CachedModel.get_models_for_provider(provider_name)


def get_all_provider_models():
    """Return a dict of {provider_name: [model_id, ...]} from cache."""
    provider_models = {}
    for provider_name in IMAGE_PROVIDERS:
        provider_models[provider_name] = get_cached_models_for_provider(provider_name)
    return provider_models


def _trigger_background_refresh(provider_name):
    """Start a background thread to refresh models for a provider (if not already running)."""
    with _refresh_lock:
        if provider_name in _refresh_in_progress:
            return
        _refresh_in_progress.add(provider_name)

    thread = threading.Thread(
        target=_refresh_provider_models,
        args=(provider_name,),
        daemon=True,
    )
    thread.start()


def _refresh_provider_models(provider_name):
    """Fetch models from the API and update the cache. Runs in a background thread."""
    try:
        provider_class = IMAGE_PROVIDERS.get(provider_name)
        if provider_class is None:
            return

        api_key_env_var = PROVIDER_API_KEY_ENV_VARS.get(provider_name, "")
        api_key = os.getenv(api_key_env_var, "")
        if not api_key:
            logger.warning(f"[{provider_name}] No API key ({api_key_env_var}), cannot refresh models.")
            return

        logger.info(f"[{provider_name}] Background refresh: fetching models from API...")
        fetched_model_ids = provider_class.fetch_available_models(api_key)

        if not fetched_model_ids:
            logger.warning(f"[{provider_name}] API returned no image generation models.")
            return

        # Mark existing as unavailable, then upsert fresh data
        CachedModel.objects.filter(provider=provider_name).update(is_available=False)

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

        logger.info(f"[{provider_name}] Cached {len(fetched_model_ids)} models.")

    except Exception as refresh_error:
        logger.error(f"[{provider_name}] Background refresh failed: {refresh_error}")
    finally:
        with _refresh_lock:
            _refresh_in_progress.discard(provider_name)
