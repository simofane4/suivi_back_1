"""A single error envelope for the whole API.

Every failure comes back as:

    {
      "error": {
        "status": 400,
        "code": "validation_error",
        "detail": "...",
        "fields": {"phone": ["..."]}
      }
    }
"""

import logging

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import APIException, NotAuthenticated
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


def _flatten(detail) -> str:
    """Reduce DRF's nested detail structures to one readable sentence."""
    if isinstance(detail, dict):
        return " ".join(f"{key}: {_flatten(value)}" for key, value in detail.items())
    if isinstance(detail, list):
        return " ".join(_flatten(item) for item in detail)
    return str(detail)


def _split_fields(detail) -> dict:
    """Pull a `{"field": [errors]}` mapping out of a DRF detail, when present."""
    if isinstance(detail, dict):
        return {key: value if isinstance(value, list) else [value] for key, value in detail.items()}
    return {}


def exception_handler(exc, context):
    if isinstance(exc, DjangoValidationError):
        exc = APIException(detail=list(exc.messages))
    elif isinstance(exc, DjangoPermissionDenied):
        exc = APIException(detail=str(exc) or "Permission denied.")

    if isinstance(exc, Http404):
        return _envelope(exc, status.HTTP_404_NOT_FOUND, "not_found")

    if isinstance(exc, IntegrityError):
        logger.warning("IntegrityError on %s: %s", context.get("request"), exc)
        return _envelope(
            exc,
            status.HTTP_409_CONFLICT,
            "conflict",
            detail="This record conflicts with existing data.",
        )

    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    code = getattr(exc, "default_code", "error")
    if isinstance(exc, NotAuthenticated):
        code = "not_authenticated"

    return _envelope(exc, response.status_code, code, response=response)


def _envelope(exc, status_code, code, detail=None, response=None):
    if detail is None:
        detail = getattr(exc, "detail", None) or str(exc)

    payload = {
        "error": {
            "status": status_code,
            "code": code,
            "detail": _flatten(detail),
        }
    }

    fields = _split_fields(getattr(exc, "detail", None))
    if fields:
        payload["error"]["fields"] = fields

    if response is None:
        from rest_framework.response import Response

        response = Response(payload, status=status_code)
    else:
        response.data = payload

    return response
