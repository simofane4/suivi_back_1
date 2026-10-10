"""Shared PDF helpers: A4 canvas, Arabic shaping and a bundled Arabic font.

Arabic joins/orders characters, so reports use `arabic-reshaper` + `python-bidi`
and draw with a TrueType Arabic font registered once. If the font is missing the
text falls back to the built-in font (still valid, narrower Arabic coverage).
"""

import os

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ARABIC_FONT_NAME = "CabinetArabic"
PAGE = A4

_FONT_PATH_CANDIDATES = (
    r"C:\Windows\Fonts\trado.ttf",  # Traditional Arabic (Windows)
    r"C:\Windows\Fonts\arial.ttf",
    "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",
    "/usr/share/fonts/truetype/amiri/Amiri-Regular.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
)

_arabic_ready = None


def arabic_font_name() -> str | None:
    """Register and return the Arabic font name, or None when unavailable."""
    global _arabic_ready
    if _arabic_ready is not None:
        return _arabic_ready or None
    for path in _FONT_PATH_CANDIDATES:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(ARABIC_FONT_NAME, path))
                _arabic_ready = ARABIC_FONT_NAME
                return ARABIC_FONT_NAME
            except Exception:
                continue
    _arabic_ready = ""
    return None


def ar_text(value) -> str:
    """Shape + reorder an Arabic string for a left-to-right PDF engine."""
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display

        return get_display(arabic_reshaper.reshape(value or ""))
    except Exception:
        return value or ""


def draw_ar(c: canvas.Canvas, x: float, y: float, text: str, font_size: float = 10):
    """Right-aligned Arabic text at (x, y) if an Arabic font is available."""
    font = arabic_font_name()
    c.setFont(font or "Helvetica", font_size)
    c.drawRightString(x, y, ar_text(text) if font else text or "")


def new_pdf_response(stream, filename):
    from django.http import HttpResponse

    response = HttpResponse(stream.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response