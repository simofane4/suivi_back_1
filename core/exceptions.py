"""Uniform error envelope: `{error: {status, code, detail, fields}}`.

The Angular client normalises this shape in `core/api-error.ts`, so every
failing request must answer with it, including validation errors raised by
serializers.
"""

from rest_framework.views import exception_handler

STATUS_CODES = {
    400: "validation_error",
    401: "unauthorized",
    403: "permission_denied",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    415: "unsupported_media_type",
    500: "server_error",
}

DEFAULT_DETAIL = {
    "validation_error": "Invalid input",
    "unauthorized": "Authentication credentials were not provided or are invalid",
    "permission_denied": "You do not have permission to perform this action",
    "not_found": "Not found",
    "method_not_allowed": "Method not allowed",
    "conflict": "Conflict",
    "unsupported_media_type": "Unsupported media type",
    "server_error": "Internal server error",
}


def _stringify(value):
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value]
    if isinstance(value, dict):
        return [str(item) for item in value.values()]
    return [str(value)]


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    status_code = response.status_code
    code = STATUS_CODES.get(status_code, "error")
    data = response.data

    fields = {}
    detail = None

    if isinstance(data, dict):
        for key, value in data.items():
            if key == "detail":
                detail = str(value)
            else:
                fields[key] = _stringify(value)
    elif isinstance(data, (list, tuple)):
        detail = "; ".join(str(item) for item in data)

    response.data = {
        "error": {
            "status": status_code,
            "code": code,
            "detail": detail or DEFAULT_DETAIL.get(code, "Request failed"),
            "fields": fields or None,
        }
    }
    return response
