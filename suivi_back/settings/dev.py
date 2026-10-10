"""Development settings.

    python manage.py runserver

Selected by `DJANGO_SETTINGS_MODULE=suivi_back.settings.dev`.
"""

from .base import *  # noqa: F401,F403
from .base import REST_FRAMEWORK, env_bool

DEBUG = env_bool("DJANGO_DEBUG", True)

# The Angular client runs on :4200 by default. Any origin is allowed while
# developing; production sets an explicit list instead.
CORS_ALLOW_ALL_ORIGINS = DEBUG

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = (
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
)

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
