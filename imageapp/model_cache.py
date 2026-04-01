import logging
import os
import threading

from django.utils import timezone

from .ai import IMAGE_PROVIDERS, get_provider_api_key_env_variable
from .models import CachedModel

logger = logging.getLogger(__name__)

_refresh_lock = threading.Lock()
_active_refresh_providers = set()


def get_cached_models_for_provider(provider_name: str) -> list[str]:
    """Return cached model IDs for a provider. Triggers background refresh if stale."""
    if CachedModel.is_cache_stale(provider_name):
        _trigger_background_refresh(provider_name)
    return CachedModel.get_models_for_provider(provider_name)


def get_all_cached_provider_models() -> dict[str, list[str]]:
    """Return {provider_name: [model_id, ...]} for all registered providers."""
    return {
        provider_name: get_cached_models_for_provider(provider_name)
        for provider_name in IMAGE_PROVIDERS
    }


def upsert_provider_models(
    provider_name: str, fetched_model_ids: list[str]
) -> None:
    """Replace a provider's cached models with freshly fetched ones.

    Marks all existing entries as unavailable, then upserts the new list.
    This is the single source of truth for cache writes — used by both
    the management command and the background refresh thread.
    """
    CachedModel.objects.filter(provider=provider_name).update(
        is_available=False
    )

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


def _trigger_background_refresh(provider_name: str) -> None:
    """Start a background thread to refresh models (skips if already running)."""
    with _refresh_lock:
        if provider_name in _active_refresh_providers:
            return
        _active_refresh_providers.add(provider_name)

    thread = threading.Thread(
        target=_refresh_provider_models_in_background,
        args=(provider_name,),
        daemon=True,
    )
    thread.start()


def _refresh_provider_models_in_background(provider_name: str) -> None:
    """Fetch models from the API and update the cache. Runs in a daemon thread."""
    try:
        provider_class = IMAGE_PROVIDERS.get(provider_name)
        if provider_class is None:
            return

        api_key_env_variable = get_provider_api_key_env_variable(provider_name)
        api_key = os.getenv(api_key_env_variable, "")
        if not api_key:
            logger.warning(
                "[%s] No API key (%s), skipping model refresh.",
                provider_name, api_key_env_variable,
            )
            return

        logger.info("[%s] Background refresh: fetching models...", provider_name)
        fetched_model_ids = provider_class.fetch_available_models(api_key)

        if not fetched_model_ids:
            logger.warning(
                "[%s] API returned no image generation models.", provider_name
            )
            return

        upsert_provider_models(provider_name, fetched_model_ids)
        logger.info(
            "[%s] Cached %d models.", provider_name, len(fetched_model_ids)
        )

    except Exception as error:
        logger.error("[%s] Background refresh failed: %s", provider_name, error)
    finally:
        with _refresh_lock:
            _active_refresh_providers.discard(provider_name)
