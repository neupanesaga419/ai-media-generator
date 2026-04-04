from django.urls import path
from . import views

app_name = "imageapp"

urlpatterns = [
    path("", views.generate_page, name="generate"),
    path("editor/", views.editor_page, name="editor"),
    path("gallery/", views.gallery_page, name="gallery"),
    path("api/generate/", views.api_generate_image, name="api_generate"),
    path("api/providers/", views.api_list_providers, name="api_providers"),
]
