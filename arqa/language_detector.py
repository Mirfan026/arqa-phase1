"""
ARQA Phase 1 — Language Detector

Detects whether a text is English ('english'), Urdu ('urdu'), or Arabic ('arabic').

Strategy — reliable, deterministic layers (no flaky statistics):
  Layer 1: Detect Arabic SCRIPT by Unicode ranges.
           Arabic script -> Urdu or Arabic (go to Layer 2).
  Layer 2: Distinguish Urdu from Arabic by Urdu-only letters.
  Layer 3 (NEW): If the text is Latin script, decide between
           ROMANIZED languages and English using distinctive markers:
             - Arabizi (Roman Arabic): digit-in-word substitutions
               (7awali, ma3, 3a2ila) + Arabic function words.
             - Roman Urdu: distinctive Urdu function words
               (mujhe, chahiye, ghar, hai...).
           Checked in order of signal strength (Arabizi first).

This avoids statistical detectors, which mishandle short domain text
AND romanized languages. Every decision here is inspectable.

Author: Muhammad Irfan
"""

import re

# Urdu-specific letters that do NOT exist in standard Arabic.
URDU_ONLY_LETTERS = set("ٹڈڑپچگژںھےۂۀ")

# Roman Urdu marker words — highly distinctive, rarely appear in English.
ROMAN_URDU_MARKERS = {
    "mujhe", "mujhy", "mainu", "chahiye", "chahta", "chahti", "chahte",
    "banana", "banwana", "ghar", "gher", "makan", "kamra", "kamre", "kamray",
    "hai", "hain", "hon", "hou", "kos", "mein", "mei", "mai", "ke", "ka", "ki",
    "ko", "liye", "aur", "nahi", "nahin", "kya", "acha", "achha", "zaroori",
    "manzil", "manzila", "baithak", "bethak", "marla", "kanal", "gaz",
    "mehman", "mehmano", "alag", "sath", "wala", "wali",
}

# Arabizi (Roman Arabic) marker words — function words common in Gulf Arabizi.
ARABIZI_MARKERS = {
    "abi", "abni", "abgha", "fi", "el", "al", "wa", "lel", "lil", "min",
    "ma3", "3ala", "3and", "ghuraf", "ghurfa", "nom", "naum", "matbakh",
    "hammam", "7ammam", "duyoof", "duyuf", "manzil", "taba2", "taba2een",
    "khususiyat", "3a2ila", "muhimma", "jiddan", "munfasil", "villa",
}


def has_arabic_script(text: str) -> bool:
    """Layer 1: True if the text contains Arabic-script characters."""
    for char in text:
        code = ord(char)
        if (0x0600 <= code <= 0x06FF
                or 0x0750 <= code <= 0x077F
                or 0x08A0 <= code <= 0x08FF):
            return True
    return False


def is_urdu(text: str) -> bool:
    """Layer 2: True if Arabic-script text contains Urdu-only letters."""
    for char in text:
        if char in URDU_ONLY_LETTERS:
            return True
    return False


def _tokens(text: str):
    """Lowercase word tokens (letters+digits), for marker matching."""
    return re.findall(r"[a-z0-9]+", text.lower())


def looks_like_arabizi(text: str) -> bool:
    """
    Layer 3a: True if Latin text looks like Roman Arabic (Arabizi).

    Strongest signal: a digit (2,3,5,6,7,9) embedded INSIDE an
    alphabetic word (e.g. '7awali', 'ma3', '3a2ila') — English does
    not do this. Backup signal: several Arabizi function words.
    """
    # Signal 1: digit-in-word substitution (very distinctive)
    if re.search(r"[a-z]+[235679]+[a-z]*|[235679]+[a-z]+", text.lower()):
        return True

    # Signal 2: multiple Arabizi marker words
    toks = set(_tokens(text))
    hits = toks & ARABIZI_MARKERS
    return len(hits) >= 2


def looks_like_roman_urdu(text: str) -> bool:
    """
    Layer 3b: True if Latin text looks like Roman Urdu.

    Signal: presence of distinctive Roman Urdu function words that
    essentially never occur in English. Require >=2 distinct markers
    to avoid misfiring on short/ambiguous English.
    """
    toks = set(_tokens(text))
    hits = toks & ROMAN_URDU_MARKERS
    return len(hits) >= 2


def detect_language(text: str) -> str:
    """
    Main entry point. Returns 'english', 'urdu', or 'arabic'.

    Flow:
      1. Empty/whitespace -> 'english'.
      2. Layer 1+2: Arabic script -> 'urdu' or 'arabic'.
      3. Layer 3 (Latin script): Arabizi -> 'arabic';
         Roman Urdu -> 'urdu'; otherwise -> 'english'.
    """
    if not text or not text.strip():
        return "english"

    # Layers 1 & 2: script-based (unchanged, reliable)
    if has_arabic_script(text):
        return "urdu" if is_urdu(text) else "arabic"

    # Layer 3: Latin script — romanized language or English?
    # Check Arabizi FIRST (digit-substitution is the cleanest signal).
    if looks_like_arabizi(text):
        return "arabic"
    if looks_like_roman_urdu(text):
        return "urdu"

    return "english"


if __name__ == "__main__":
    test_cases = [
        # --- original script-based cases (must still pass) ---
        ("Design a four bedroom villa in Riyadh", "english"),
        ("Build a modern house with a large kitchen", "english"),
        ("چار کمروں کا گھر بنائیں جدید طرز کا", "urdu"),
        ("گھر کا نقشہ بنائیں بجٹ کے مطابق", "urdu"),
        ("صمم فيلا من أربع غرف نوم في الرياض", "arabic"),
        ("اريد منزل حديث مع مطبخ كبير", "arabic"),
        # --- NEW: romanized cases (the Day-10 fix) ---
        ("mujhe Lahore mein 5 marla ka ghar banana hai, 3 bedroom hon", "urdu"),
        ("acha sa ghar chahiye 2 manzil ka aur alag baithak ho", "urdu"),
        ("abi abni villa fi Dubai, 7awali 2 million dirham, 3 ghuraf nom", "arabic"),
        ("el budget 7awali 2 million, majlis munfasil lel duyoof", "arabic"),
        # --- English that must NOT be misread as romanized ---
        ("I want a villa with a kitchen and a majlis", "english"),
    ]

    print("\n=== ARQA Language Detector — Self Test (with romanized) ===\n")
    passed = 0
    for text, expected in test_cases:
        result = detect_language(text)
        ok = "PASS" if result == expected else "FAIL"
        if result == expected:
            passed += 1
        print(f"[{ok}] expected={expected:8} got={result:8} | {text[:55]}")

    print(f"\nResult: {passed}/{len(test_cases)} tests passed")