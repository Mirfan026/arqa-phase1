"""
ARQA Phase 1 — Communication Agent (Day 8, updated Day 10–11)

The system's front door. Takes a free-text client brief (EN/UR/AR)
and turns it into a structured requirements object the downstream
agents (Design, Report, Supervisor) can act on.

Pipeline:  detect language  ->  LLM extraction  ->  parse  ->  completeness check

Author: Muhammad Irfan
"""

import os
import json
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from arqa.language_detector import detect_language

load_dotenv()

MODEL = "Qwen/Qwen2.5-7B-Instruct:featherless-ai"

# Fields the system genuinely CANNOT proceed without (must ask the client).
# floors/budget/plot_size are intentionally NOT here — the system can offer
# options or proceed with defaults for those (range->scenarios design decision).
ESSENTIAL_FIELDS = ["country", "project_type"]

# The instruction we give the LLM. It describes the EXACT schema and
# tells the model how to handle synonyms, exact numbers, and ranges.
EXTRACTION_PROMPT = """You are an extraction assistant for an architectural design system.
The client's brief may be written in English, Urdu, or Arabic. Understand it in any of
these languages, but ALWAYS extract into the English-keyed JSON schema below.
Return ONLY a JSON object (no markdown, no commentary) with EXACTLY this structure:

{
  "project_type": <string or null>,        // villa, apartment, house, etc.
  "country": <string or null>,             // one of: saudi_arabia, uae, pakistan, qatar, or null
  "budget": {"min": <number>, "max": <number>, "currency": <string>} or null,
  "floors": {"min": <number>, "max": <number>} or null,
  "plot_size": <string or null>,
  "rooms": {                                // each value is {"min": n, "max": n} or null
     "bedrooms": <range or null>,
     "bathrooms": <range or null>,
     "kitchen": <range or null>,
     "living": <range or null>,
     "majlis": <range or null>
  },
  "cultural_flags": [<strings>],            // choose from: gender_segregation, visual_privacy,
                                            // male_guest_majlis, family_privacy, qibla_orientation,
                                            // separate_entrances
  "other_cultural_notes": <string or null>,
  "other_requirements": <string or null>
}

RULES:
- An EXACT number is a range with equal min and max. "5 floors" -> {"min":5,"max":5}.
- A RANGE keeps both. "2 to 3 floors" -> {"min":2,"max":3}.
- Recognize SYNONYMS across languages and romanized forms. Map all to the correct field:
  - floors = storeys = stories = levels = manzil/manzila = tabaq/taba2/taba2een; "G+2" = 3 floors.
  - bedrooms = beds = BR = kamre/kamray = ghuraf nom/ghuraf naum/ghuraf.
  - bathrooms = hammam/7ammam/7ammamat; kitchen = matbakh; living = salon/saala/drawing room.
  - majlis = baithak/bethak (guest sitting room) = guest room for receiving visitors.
- Land/plot units: "marla", "kanal", "gaz" (South Asia), "dunum" (Gulf) -> put in plot_size
  exactly as stated (e.g. "5 marla", "1 kanal").
- Map currency words: riyal/SAR, dirham/AED, rupee/PKR, qatari riyal/QAR.
- If a field is not mentioned, use null.
- CRITICAL: If the brief explicitly NAMES a country or a city (e.g. "Lahore", "Dubai",
  "Riyadh"), you MUST set "country" to the matching country — even if other cultural cues
  in the text might suggest a different region. An explicitly named place ALWAYS wins.
  (Lahore/Karachi/Islamabad -> pakistan; Riyadh/Jeddah -> saudi_arabia; Dubai/Abu Dhabi -> uae.)
  Do NOT INFER country from cultural cues alone (e.g. a majlis does NOT by itself imply Saudi
  Arabia). If no country or city is named anywhere, country MUST be null.
- Set budget.currency ONLY if a currency is named OR a country is explicitly stated.
  If neither, currency MUST be null. Never guess location or currency.
- cultural_flags: only include flags clearly implied by the brief.
- Return ONLY the JSON. No explanation.

Client brief:
\"\"\"{brief}\"\"\"
"""


def _get_client():
    """Create the HuggingFace inference client using the token from .env."""
    token = os.getenv("HF_TOKEN")
    if not token:
        raise RuntimeError("HF_TOKEN not found in .env")
    return InferenceClient(token=token)


def _parse_json(raw_text):
    """
    Robustly parse the LLM's response into a Python dict.
    LLMs sometimes wrap JSON in ```json fences or add stray text.
    """
    text = raw_text.strip()

    # Remove markdown code fences if present
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
        if text.endswith("```"):
            text = text[:-3].strip()

    # Fallback: grab from the first { to the last }
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            text = text[start:end + 1]

    return json.loads(text)


def check_completeness(data):
    """
    Decide whether the brief has enough essential info to proceed,
    or whether the Supervisor must ask the client clarifying questions.

    Adds two fields:
      - missing_required: list of essential fields that are null/empty
      - ready_for_design: True if nothing essential is missing
    """
    missing = []

    for field in ESSENTIAL_FIELDS:
        if not data.get(field):          # null, empty string, or missing
            missing.append(field)

    # Rooms are essential too: need at least ONE room type specified
    rooms = data.get("rooms") or {}
    has_any_room = any(v for v in rooms.values())
    if not has_any_room:
        missing.append("rooms")

    data["missing_required"] = missing
    data["ready_for_design"] = (len(missing) == 0)
    return data


def extract_requirements(brief, max_tokens=800):
    """
    Turn a free-text client brief into a structured requirements dict.

    Steps:
      1. Detect the brief's language (EN/UR/AR)  [Day 3]
      2. Ask the LLM to extract into the English schema  [Day 2 client]
      3. Parse the JSON
      4. Check completeness (flag missing essential fields)

    Returns the structured requirements dict (the 'blackboard' entry).
    """
    # 1. Detect language
    language = detect_language(brief)

    # 2. Ask the LLM to extract
    client = _get_client()
    prompt = EXTRACTION_PROMPT.replace("{brief}", brief)

    response = client.chat_completion(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.1,   # low temperature = consistent, deterministic extraction
    )
    raw = response.choices[0].message.content

    # 3. Parse JSON (with graceful failure)
    try:
        data = _parse_json(raw)
        parse_ok = True
    except Exception as e:
        print(f"[warn] JSON parse failed: {e}")
        data = {}
        parse_ok = False

    # 4. Attach metadata and check completeness
    data["language"] = language
    data["raw_brief"] = brief
    data["_parse_ok"] = parse_ok
    data = check_completeness(data)      # flag missing essential fields
    return data


if __name__ == "__main__":
    # Test on a realistic English brief
    test_brief = (
        "I want to build a 4 bedroom villa in Riyadh. Budget is around "
        "1.5 to 2 million riyals. I'd like 2 to 3 storeys, 3 bathrooms, "
        "a kitchen, a living room, and a separate majlis for male guests. "
        "Privacy for the family is very important, and please keep a "
        "separate entrance for women."
    )

    print("Extracting requirements from brief...\n")
    result = extract_requirements(test_brief)
    print("=" * 60)
    print("STRUCTURED REQUIREMENTS")
    print("=" * 60)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # --- Stress test: a vague, messy, real-world brief ---
    messy_brief = (
        "looking for a biggish family home, maybe 3 or 4 beds, ground plus one, "
        "nothing too fancy, decent budget not sure exactly maybe 800k-ish, "
        "really want privacy from the street and somewhere to receive male guests separately"
    )
    print("\n\n" + "=" * 60)
    print("MESSY BRIEF STRESS TEST")
    print("=" * 60)
    print(json.dumps(extract_requirements(messy_brief), indent=2, ensure_ascii=False))