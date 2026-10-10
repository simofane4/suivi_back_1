"""Production settings.

Selected by `DJANGO_SETTINGS_MODULE=suivi_back.settings.prod`. Requires
`DJANGO_SECRET_KEY` to be set in the environment; startup fails loudly without
it rather than falling back to an insecure default.
"""

import os
import sys

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401,F403
from .base import MIDDLEWARE, REST_FRAMEWORK, SECRET_KEY, STORAGES

DEBUG = False

if not SECRET_KEY:
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY must be set in the environment for production."
    )

# Never fall back to the Browsable API in production: it exposes the schema and
# is not meant to be reachable outside a development machine.
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = (
    "rest_framework.renderers.JSONRenderer",
)

# WhiteNoise for static files (insert after SecurityMiddleware)
if "whitenoise.middleware.WhiteNoiseMiddleware" not in MIDDLEWARE:
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

STORAGES["staticfiles"]["BACKEND"] = "whitenoise.storage.CompressedManifestStaticFilesStorage"

SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Uploaded scans and patient documents are private; never serve them straight
# off disk.
SECURE_REFERRER_POLICY = "same-origin"

# The default file storage is a plain filesystem write. Pointing
# DJANGO_MEDIA_ROOT at a mounted disk is enough to make uploads survive
# deploys; moving to object storage is a config change rather than a code
# change, so an S3-compatible backend can be dropped in later without
# touching the apps.
STORAGES["default"]["BACKEND"] = os.environ.get(
    "DJANGO_DEFAULT_FILE_STORAGE",
    STORAGES["default"]["BACKEND"],
)
