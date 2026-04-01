from django.contrib import admin
from .models import CachedModel, GeneratedImage


@admin.register(CachedModel)
class CachedModelAdmin(admin.ModelAdmin):
    list_display = ["provider", "model_id", "capability", "is_available", "fetched_at"]
    list_filter = ["provider", "capability", "is_available"]
    search_fields = ["model_id"]


@admin.register(GeneratedImage)
class GeneratedImageAdmin(admin.ModelAdmin):
    list_display = ["id", "provider", "model_name", "status", "created_at"]
    list_filter = ["provider", "status"]
    search_fields = ["prompt"]
    readonly_fields = ["created_at"]
