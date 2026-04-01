# ai-media-generator

A web app for generating images (and eventually video) using different AI models. Built with Django and Tailwind CSS. Pick a provider, type a prompt, get an image. That's it.

Currently supports **Google Imagen** and **Grok (xAI)**, with the architecture set up so adding more providers is straightforward.

---

## What it looks like

- A simple generate page where you pick a provider, write a prompt, and hit generate
- A gallery page that shows everything you've created
- Dark UI, minimal, gets out of your way

---

## Getting started

### Prerequisites

- Python 3.11+
- A Google API key (for Imagen) and/or an xAI API key (for Grok)

### Setup

```bash
# Clone the repo
git clone https://github.com/your-username/ai-media-generator.git
cd ai-media-generator

# Create and activate a virtual environment
python -m venv venv
source venv/Scripts/activate    # Windows (Git Bash)
# or: venv\Scripts\activate     # Windows (PowerShell)
# or: source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Set up your environment variables
cp .env.example .env
# Open .env and add your API keys

# Run migrations
python manage.py migrate

# Start the server
python manage.py runserver
```

Open [http://localhost:8000](http://localhost:8000) and you're good to go.

### Environment variables

Create a `.env` file in the project root (or copy `.env.example`):

```
GOOGLE_API_KEY=your-google-api-key
XAI_API_KEY=your-xai-api-key
```

You only need the key for the provider you plan to use. The app won't crash if a key is missing — it just won't be able to call that provider.

---

## Project structure

```
ai-media-generator/
├── core/                   # Django project settings and root URL config
├── imageapp/
│   ├── ai/                 # One module per AI provider
│   │   ├── base.py         # Abstract base class all providers inherit from
│   │   ├── google_image_generator.py
│   │   └── grok_image_generator.py
│   ├── templates/imageapp/ # Generate page, gallery
│   ├── models.py           # GeneratedImage model
│   ├── views.py            # Page views + API endpoints
│   └── urls.py
├── templates/
│   └── base.html           # Global layout (Tailwind CSS via CDN)
├── media/                  # Where generated images get saved
├── .env.example
├── requirements.txt
└── manage.py
```

---

## How providers work

Each AI provider is a Python class that inherits from `BaseImageGenerator` and implements two methods:

- `generate(prompt, **kwargs)` — takes a text prompt, returns image bytes
- `get_available_models()` — returns a list of model names the provider supports

Providers are registered in `imageapp/ai/__init__.py`. The app uses a simple factory function to instantiate them by name.

### Adding a new provider

1. Create a new file in `imageapp/ai/`, say `new_provider_generator.py`
2. Write a class that extends `BaseImageGenerator`
3. Register it in `imageapp/ai/__init__.py`
4. Add the choice to `PROVIDER_CHOICES` in `imageapp/models.py`

That's the whole process. No config files to edit, no settings to toggle.

---

## Supported providers

| Provider       | Model(s)                        | Key needed       |
|----------------|---------------------------------|------------------|
| Google Imagen  | imagen-3.0-generate-002, imagen-3.0-fast-generate-001 | `GOOGLE_API_KEY` |
| Grok (xAI)     | grok-2-image                    | `XAI_API_KEY`    |

---

## Tech stack

- **Backend**: Django 5.2, Python 3.11
- **Frontend**: Tailwind CSS (CDN, no build step)
- **Database**: SQLite (default, swap it out if you need to)
- **APIs**: Google GenAI SDK, xAI REST API

---

## What's next

This is a work in progress. Planned additions:

- Video generation (Google Veo, LTX-Video, Runway)
- User accounts and per-user API key management
- More image providers (DALL-E, Stable Diffusion)
- Async generation with background tasks

---

## License

MIT
