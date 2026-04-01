from django.db import models
from django.utils import timezone


class CachedModel(models.Model):
    """Stores AI models fetched from provider APIs. Refreshed every 5-7 days."""

    CAPABILITY_CHOICES = [
        ("image_generation", "Image Generation"),
        ("video_generation", "Video Generation"),
    ]

    provider = models.CharField(max_length=50)
    model_id = models.CharField(max_length=200)
    display_name = models.CharField(max_length=200, blank=True, default="")
    capability = models.CharField(max_length=50, choices=CAPABILITY_CHOICES, default="image_generation")
    is_available = models.BooleanField(default=True)
    fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["provider", "model_id"]
        ordering = ["provider", "model_id"]

    def __str__(self):
        return f"[{self.provider}] {self.model_id}"

    @classmethod
    def get_models_for_provider(cls, provider_name, capability="image_generation"):
        """Return cached models for a provider. Returns empty list if cache is stale or empty."""
        return list(
            cls.objects.filter(
                provider=provider_name,
                capability=capability,
                is_available=True,
            ).values_list("model_id", flat=True)
        )

    @classmethod
    def is_cache_stale(cls, provider_name, max_age_days=5):
        """Check if the cached models for a provider need refreshing."""
        latest = cls.objects.filter(provider=provider_name).order_by("-fetched_at").first()
        if latest is None:
            return True
        age = timezone.now() - latest.fetched_at
        return age.days >= max_age_days


class GeneratedImage(models.Model):
    PROVIDER_CHOICES = [
        ("google_imagen", "Google Imagen"),
        ("grok", "Grok (xAI)"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    prompt = models.TextField()
    negative_prompt = models.TextField(blank=True, default="")
    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES)
    model_name = models.CharField(max_length=100, blank=True, default="")
    image = models.ImageField(upload_to="images/%Y/%m/%d/", blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.provider}] {self.prompt[:50]}"
