# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django web app for AI image generation. Supports multiple AI providers (currently Google Imagen via Vertex AI and Grok/xAI). No user authentication — credentials are loaded from `.env` and Application Default Credentials. The project is designed to add more generation features (video, more providers) incrementally.

## Commands

```bash
# Activate virtual environment
source venv/Scripts/activate          # Git Bash / WSL
venv\Scripts\activate                 # PowerShell

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Start dev server
python manage.py runserver

# Django system check
python manage.py check
```

## Architecture & Design Patterns

### Project Structure

```
ai-app-easy/
├── core/                        # Django project config (settings, root urls)
├── imageapp/                    # Image generation app
│   ├── ai/                      # AI provider modules (one file per provider)
│   │   ├── base.py              # BaseImageGenerator ABC
│   │   ├── google_image_generator.py
│   │   ├── grok_image_generator.py
│   │   └── __init__.py          # IMAGE_PROVIDERS registry + factory
│   ├── templates/imageapp/      # App-specific templates (extends base.html)
│   │   ├── base.html
│   │   ├── generate.html
│   │   └── gallery.html
│   ├── models.py                # GeneratedImage model
│   ├── views.py                 # Page views + JSON API endpoints
│   └── urls.py                  # /images/ routes
├── templates/                   # Global templates
│   └── base.html                # Root layout with Tailwind CDN + nav
├── media/images/                # Generated image files (gitignored)
├── .env.example                 # Required env vars template
└── requirements.txt
```

### AI Provider Pattern (Strategy + Factory)

Each AI provider is a class inheriting from `BaseImageGenerator` (ABC) in `imageapp/ai/base.py`. Every provider must implement:
- `generate(prompt, **kwargs) -> bytes` — returns raw image bytes
- `fetch_available_models() -> list[str]` — classmethod, loads its own credentials

Providers are registered in `imageapp/ai/__init__.py` via the `IMAGE_PROVIDERS` dict. Use `create_image_generator("provider_name")` factory to instantiate.

**To add a new image provider:**
1. Create `imageapp/ai/new_provider_generator.py` with a class extending `BaseImageGenerator`
2. Register it in `imageapp/ai/__init__.py` in `IMAGE_PROVIDERS`
3. Add the provider choice to `GeneratedImage.PROVIDER_CHOICES` in `models.py`

### Template Inheritance

```
templates/base.html                      ← global layout (Tailwind, nav)
  └── imageapp/templates/imageapp/base.html  ← app-level base
        ├── generate.html
        └── gallery.html
```

Each app has its own `base.html` that extends the global `base.html`. Page templates extend their app's `base.html`. When adding new apps (e.g., videosapp), follow the same pattern.

### API Pattern

Views serve both HTML pages and JSON API endpoints from the same `views.py`. API endpoints are prefixed with `api/` in the URL path and return `JsonResponse`. No DRF — plain Django views with `@require_POST` for mutations.

### Naming Convention

**Always use full, descriptive names.** Never abbreviate variables, functions, or identifiers. Use `image_record` not `img`, `provider_class` not `cls`, `response` not `resp`, `error` not `err`, `generation_status` not `stat`.

## Configuration

- **Google Vertex AI** uses Application Default Credentials (ADC) — run `gcloud auth application-default login`
- **xAI API key** is read from `.env` via `BaseImageGenerator._load_api_key()`
- **No user login** — the app runs without authentication
- **Tailwind CSS** via CDN in `templates/base.html` (no build step)
- **SQLite** default database
- **Media uploads** at `media/` served in DEBUG mode

### Required Environment Variables

```
GOOGLE_CLOUD_PROJECT=your-gcp-project   # For Vertex AI (Imagen / Gemini)
GOOGLE_CLOUD_LOCATION=us-central1       # Vertex AI region (default: us-central1)
XAI_API_KEY=your-xai-api-key            # For Grok image generation
```

### Authentication Setup

**Google Vertex AI:**
1. Install [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
2. `gcloud auth application-default login`
3. Set `GOOGLE_CLOUD_PROJECT` in `.env`

## Current Providers

| Provider              | Module                          | Auth                    | Models                                   |
|-----------------------|---------------------------------|-------------------------|------------------------------------------|
| Google Imagen (Vertex)| `google_image_generator.py`     | ADC + project env var   | imagen-4.0-generate-001, gemini models   |
| Grok (xAI)            | `grok_image_generator.py`       | API key                 | grok-2-image                             |
