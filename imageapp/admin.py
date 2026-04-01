from django.contrib import admin
from .models import GeneratedImage


@admin.register(GeneratedImage)
class GeneratedImageAdmin(admin.ModelAdmin):
    list_display = ["id", "provider", "model_name", "status", "created_at"]
    list_filter = ["provider", "status"]
    search_fields = ["prompt"]
    readonly_fields = ["created_at"]
