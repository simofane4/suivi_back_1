"""
ASGI config for suivi_back project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# Use production settings unless DJANGO_DEBUG is explicitly "true"
if os.environ.get("DJANGO_DEBUG", "False").lower() == "true":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "suivi_back.settings.dev")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "suivi_back.settings.prod")

application = get_asgi_application()
