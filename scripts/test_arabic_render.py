"""
ARQA Phase 1 — Day 17
Proof of concept: render real Arabic script into a PDF, correctly shaped
and right-to-left. Tests the font + reshaping + RTL pipeline in isolation
before building the full trilingual report generator.

Usage: python -m scripts.test_arabic_render
"""

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT_PATH = "arqa/fonts/NotoNaskhArabic.ttf"
FONT_NAME = "NotoNaskhArabic"


def shape_arabic(text):
    """
    Convert plain Arabic/Urdu Unicode into a correctly-shaped,
    right-to-left-ordered string ready for left-to-right PDF drawing.
    """
    reshaped = arabic_reshaper.reshape(text)   # contextual letter forms
    return get_display(reshaped)                # RTL visual order


if __name__ == "__main__":
    # Register the Arabic-script font with reportlab.
    pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))

    c = canvas.Canvas("arabic_test.pdf")

    # English line — proves the existing Helvetica path still works.
    c.setFont("Helvetica", 14)
    c.drawString(50, 780, "ARQA - Arabic rendering test (English line)")

    # Arabic line — a real project-relevant sentence: "4 bedroom villa in Riyadh"
    c.setFont(FONT_NAME, 16)
    arabic_text = "\u0641\u0644\u0627 \u0645\u0643\u0648\u0646\u0629 \u0645\u0646 4 \u063a\u0631\u0641 \u0646\u0648\u0645 \u0641\u064a \u0627\u0644\u0631\u064a\u0627\u0636"
    shaped = shape_arabic(arabic_text)
    c.drawRightString(550, 740, shaped)   # right-aligned, as Arabic reads

    # Urdu line — reuses the SAME font/pipeline (Naskh style, readable;
    # Nastaliq-specific styling logged as a future refinement).
    c.setFont(FONT_NAME, 16)
    urdu_text = "\u0631\u06cc\u0627\u0636 \u0645\u06cc\u06ba 4 \u0628\u06cc\u0688 \u0631\u0648\u0645 \u06a9\u0627 \u0648\u0644\u0627"
    shaped_urdu = shape_arabic(urdu_text)
    c.drawRightString(550, 700, shaped_urdu)

    c.save()
    print("arabic_test.pdf written. Open it and check: does the Arabic/Urdu")
    print("text render as real, connected, right-to-left script (not boxes")
    print("or disconnected backwards letters)?")