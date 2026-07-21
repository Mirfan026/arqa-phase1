"""
ARQA Phase 1 — Report Agent: PDF rendering (Day 17)

Renders an assembled report (arqa.report_agent.assemble_report) into a
client-facing PDF, in English, Arabic, or Urdu. Reuses the Day-17
proven pipeline (Noto Naskh Arabic + arabic-reshaper + python-bidi) for
native-script languages; Latin-script languages (English, Roman Urdu,
Arabizi) use plain Helvetica — no extra work needed.

Author: Muhammad Irfan
"""

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT_PATH = "arqa/fonts/NotoNaskhArabic.ttf"
FONT_NAME = "NotoNaskhArabic"
_font_registered = False

# Languages that need the native-script (Arabic/Urdu) shaping pipeline.
NATIVE_SCRIPT_LANGS = {"arabic", "urdu"}

LABELS = {
    "english": {
        "title": "ARQA - Preliminary Design Report",
        "project": "Project", "plot": "Plot", "rooms": "Room Schedule",
        "cost": "Cost Estimate", "compliance": "Code Compliance Summary",
        "found": "Rule found", "not_in_code": "Not specified in code",
        "disclaimer": "This is a preliminary estimate based on regional "
                       "market benchmarks, not a binding quote.",
    },
    "arabic": {
        "title": "\u0623\u0631\u0642\u0649 - \u062a\u0642\u0631\u064a\u0631 \u0627\u0644\u062a\u0635\u0645\u064a\u0645 \u0627\u0644\u0623\u0648\u0644\u064a",
        "project": "\u0627\u0644\u0645\u0634\u0631\u0648\u0639", "plot": "\u0627\u0644\u0642\u0637\u0639\u0629",
        "rooms": "\u062c\u062f\u0648\u0644 \u0627\u0644\u063a\u0631\u0641",
        "cost": "\u062a\u0642\u062f\u064a\u0631 \u0627\u0644\u062a\u0643\u0644\u0641\u0629",
        "compliance": "\u0645\u0644\u062e\u0635 \u0627\u0644\u0627\u0645\u062a\u062b\u0627\u0644 \u0644\u0644\u0643\u0648\u062f",
        "found": "\u062a\u0645 \u0627\u0644\u0639\u062b\u0648\u0631 \u0639\u0644\u0649 \u0642\u0627\u0639\u062f\u0629",
        "not_in_code": "\u063a\u064a\u0631 \u0645\u062d\u062f\u062f \u0641\u064a \u0627\u0644\u0643\u0648\u062f",
        "disclaimer": "\u0647\u0630\u0627 \u062a\u0642\u062f\u064a\u0631 \u0623\u0648\u0644\u064a \u064a\u0633\u062a\u0646\u062f \u0625\u0644\u0649 \u0645\u0639\u0627\u064a\u064a\u0631 \u0627\u0644\u0633\u0648\u0642 \u0627\u0644\u0625\u0642\u0644\u064a\u0645\u064a\u0629.",
    },
    "urdu": {
        "title": "\u0622\u0631\u06a9\u06cc\u0648 - \u0627\u0628\u062a\u062f\u0627\u0626\u06cc \u0688\u06cc\u0632\u0627\u0626\u0646 \u0631\u067e\u0648\u0631\u0679",
        "project": "\u067e\u0631\u0627\u062c\u06cc\u06a9\u0679",
        "plot": "\u067e\u0644\u0627\u0679",
        "rooms": "\u06a9\u0645\u0631\u0648\u06ba \u06a9\u06cc \u062a\u0641\u0635\u06cc\u0644",
        "cost": "\u0644\u0627\u06af\u062a \u06a9\u0627 \u062a\u062e\u0645\u06cc\u0646\u06c1",
        "compliance": "\u0636\u0627\u0628\u0637\u06d2 \u06a9\u06cc \u062a\u0639\u0645\u06cc\u0644 \u06a9\u0627 \u062e\u0644\u0627\u0635\u06c1",
        "found": "\u0636\u0627\u0628\u0637\u06c1 \u0645\u0644\u0627",
        "not_in_code": "\u0636\u0627\u0628\u0637\u06d2 \u0645\u06cc\u06ba \u0645\u0648\u062c\u0648\u062f \u0646\u06c1\u06cc\u06ba",
        "disclaimer": "\u06cc\u06c1 \u0627\u06cc\u06a9 \u0627\u0628\u062a\u062f\u0627\u0626\u06cc \u062a\u062e\u0645\u06cc\u0646\u06c1 \u06c1\u06d2\u060c \u062d\u062a\u0645\u06cc \u0642\u06cc\u0645\u062a \u0646\u06c1\u06cc\u06ba\u06d4",
    },
}


def _ensure_font():
    global _font_registered
    if not _font_registered:
        pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))
        _font_registered = True


def shape(text, language):
    """Shape + RTL-order text if it's native-script Arabic/Urdu; else pass through."""
    if language in NATIVE_SCRIPT_LANGS:
        return get_display(arabic_reshaper.reshape(text))
    return text


def render_report_pdf(report, language, out_path):
    """
    Render an assembled report to a PDF, in the given language.
    language: "english", "arabic", or "urdu".
    """
    _ensure_font()
    L = LABELS[language]
    native = language in NATIVE_SCRIPT_LANGS
    font = FONT_NAME if native else "Helvetica"
    font_bold = FONT_NAME if native else "Helvetica-Bold"

    c = canvas.Canvas(out_path)
    y = 800
    right_x, left_x = 550, 50

    def line(text, size=11, bold=False, gap=18):
        nonlocal y
        c.setFont(font_bold if bold else font, size)
        txt = shape(text, language)
        if native:
            c.drawRightString(right_x, y, txt)
        else:
            c.drawString(left_x, y, txt)
        y -= gap

    # Title
    line(L["title"], size=16, bold=True, gap=28)

    # Project + plot
    layout = report["layout"]
    line(f"{L['project']}: {report['requirements'].get('project_type', '-')} "
         f"({report['requirements'].get('country', '-')})", bold=True)
    line(f"{L['plot']}: {layout['plot']['width']} x {layout['plot']['height']} m "
         f"({layout['plot']['area']:.0f} m\u00b2)", gap=26)

    # Room schedule
    line(L["rooms"], size=13, bold=True, gap=20)
    for r in layout["rooms"]:
        drawn = round(r["w"] * r["h"], 1)
        line(f"{r['label']}: {drawn} m\u00b2", size=10, gap=15)
    y -= 8

    # Cost
    cost = report["cost"]
    line(L["cost"], size=13, bold=True, gap=20)
    if cost:
        line(f"{cost['currency']} {cost['low_estimate']:,.0f} - "
             f"{cost['currency']} {cost['high_estimate']:,.0f}", size=11, gap=26)
    else:
        line(L["not_in_code"], size=11, gap=26)

    # Compliance
    line(L["compliance"], size=13, bold=True, gap=20)
    for chk in report["compliance"]:
        status = L["found"] if chk["status"] == "found" else L["not_in_code"]
        line(f"{chk['room_type']}: {status}", size=10, gap=15)
    y -= 10

    # Disclaimer
    c.setFont(font, 8)
    dtxt = shape(L["disclaimer"], language)
    if native:
        c.drawRightString(right_x, y, dtxt)
    else:
        c.drawString(left_x, y, dtxt)

    c.save()
    return out_path


if __name__ == "__main__":
    from arqa.report_agent import assemble_report

    sample = {
        "project_type": "villa",
        "country": "saudi_arabia",
        "plot_size": None,
        "rooms": {
            "bedrooms": {"min": 4, "max": 4},
            "bathrooms": {"min": 2, "max": 2},
            "kitchen": {"min": 1, "max": 1},
            "living": {"min": 1, "max": 1},
            "majlis": {"min": 1, "max": 1},
        },
    }

    report = assemble_report(sample)

    render_report_pdf(report, "english", "report_english.pdf")
    print("Wrote report_english.pdf")

    render_report_pdf(report, "arabic", "report_arabic.pdf")
    print("Wrote report_arabic.pdf")

    render_report_pdf(report, "urdu", "report_urdu.pdf")
    print("Wrote report_urdu.pdf")