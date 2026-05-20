"""
ARQA Phase 1 — Language Detector

Detects whether a text is English (en), Urdu (ur), or Arabic (ar).

Strategy — two reliable layers:
  Layer 1: Detect the SCRIPT by Unicode character ranges.
           Latin script  -> English (certain).
           Arabic script -> Urdu or Arabic (go to Layer 2).
  Layer 2: Distinguish Urdu from Arabic by checking for
           Urdu-only letters that do not exist in Arabic.

This avoids the unreliability of raw statistical detection,
which can misclassify short domain text (e.g. "villa" as Danish).

Author: Muhammad Irfan
"""

# Urdu-specific letters that do NOT exist in standard Arabic.
# If any of these appear in Arabic-script text, the text is Urdu.
URDU_ONLY_LETTERS = set("ٹڈڑپچگژںھےۂۀ")

def has_arabic_script(text: str) -> bool:
    """
    Layer 1: Return True if the text contains Arabic-script characters.

    Arabic script (used by both Arabic and Urdu) lives in specific
    Unicode ranges. We check each character's code point against them.
    """
    for char in text:
        code = ord(char)
        # Main Arabic block: U+0600–U+06FF
        # Arabic Supplement:  U+0750–U+077F
        # Arabic Extended-A:  U+08A0–U+08FF
        if (0x0600 <= code <= 0x06FF
                or 0x0750 <= code <= 0x077F
                or 0x08A0 <= code <= 0x08FF):
            return True
    return False

def is_urdu(text: str) -> bool:
    """
    Layer 2: Given Arabic-script text, return True if it is Urdu.

    Urdu uses letters that do not exist in standard Arabic
    (e.g. پ چ گ ٹ ڈ ڑ ھ ے). If any appear, the text is Urdu.
    """
    for char in text:
        if char in URDU_ONLY_LETTERS:
            return True
    return False

def detect_language(text: str) -> str:
    """
    Main entry point. Returns 'english', 'urdu', or 'arabic'.

    Flow:
      1. Empty/whitespace input -> default to 'english'.
      2. Layer 1: no Arabic script -> 'english'.
      3. Layer 2: Arabic script + Urdu-only letters -> 'urdu'.
      4. Otherwise (Arabic script, no Urdu letters) -> 'arabic'.
    """
    # Guard against empty or whitespace-only input
    if not text or not text.strip():
        return "english"

    # Layer 1: is there any Arabic script at all?
    if not has_arabic_script(text):
        return "english"

    # Layer 2: Arabic script present — Urdu or Arabic?
    if is_urdu(text):
        return "urdu"

    return "arabic"

# ─────────────────────────────────────────────────────────────
# Self-test: runs only when this file is executed directly,
# e.g.  python arqa/language_detector.py
# It does NOT run when the module is imported by other code.
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_cases = [
        ("Design a four bedroom villa in Riyadh", "english"),
        ("Build a modern house with a large kitchen", "english"),
        ("چار کمروں کا گھر بنائیں جدید طرز کا", "urdu"),
        ("گھر کا نقشہ بنائیں بجٹ کے مطابق", "urdu"),
        ("صمم فيلا من أربع غرف نوم في الرياض", "arabic"),
        ("اريد منزل حديث مع مطبخ كبير", "arabic"),
    ]

    print("\n=== ARQA Language Detector — Self Test ===\n")
    passed = 0
    for text, expected in test_cases:
        result = detect_language(text)
        ok = "PASS" if result == expected else "FAIL"
        if result == expected:
            passed += 1
        print(f"[{ok}] expected={expected:8} got={result:8} | {text}")

    print(f"\nResult: {passed}/{len(test_cases)} tests passed")