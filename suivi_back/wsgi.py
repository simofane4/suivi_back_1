"""
WSGI config for suivi_back project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Use production settings unless DJANGO_DEBUG is explicitly "true"
if os.environ.get("DJANGO_DEBUG", "False").lower() == "true":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "suivi_back.settings.dev")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "suivi_back.settings.prod")

application = get_wsgi_application()
