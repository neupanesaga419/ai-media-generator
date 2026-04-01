from django.db import models


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
