"""
ARQA Phase 1 — Compliance Checker (Day 16)

Checks a Design Agent layout against real building-code rules (via the
Day-7 RAG) and cultural-requirement coverage. Queried ONCE PER ROOM TYPE
(codes specify rules by category, e.g. "bedrooms", not by instance like
"Bedroom 1") and applied to every room instance of that type.

Honest by design (F3 pattern): a rule either is found above the
confidence threshold, or the result is reported as NOT SPECIFIED IN CODE
— never fabricated. Cultural-specific room types (majlis) predictably
surface F4: the codes are silent on them, which is the finding, not a bug.

Author: Muhammad Irfan
"""

from arqa.code_knowledge import get_relevant_rules

# One representative compliance query per room TYPE.
QUERY_FOR_TYPE = {
    "bedrooms": "minimum bedroom area requirements residential",
    "bathrooms": "bathroom WC minimum area ventilation requirements",
    "kitchen": "kitchen minimum area ventilation requirements",
    "living": "living room minimum area requirements residential",
    "majlis": "majlis guest reception room privacy requirements",
}


def check_room_type(room_type, country, sample_area):
    """
    Query the RAG once for a room TYPE and judge compliance for a
    representative drawn area of that type.

    Returns:
      {
        "room_type", "query", "status" ("found"/"not_in_code"),
        "rule_text", "score", "note"
      }
    """
    query = QUERY_FOR_TYPE.get(room_type)
    if not query:
        return {
            "room_type": room_type, "query": None, "status": "not_in_code",
            "rule_text": None, "score": None,
            "note": "No compliance query defined for this room type.",
        }

    result = get_relevant_rules(query, country, top_k=1)

    # Guard against near-threshold false positives (F9): the majlis query
    # matched an unrelated toilet-privacy rule at score 0.46, just barely
    # above the RAG's 0.45 threshold, by lexical coincidence on "privacy" —
    # while genuine matches for other room types scored 0.63-0.72. A
    # slightly higher bar for compliance-specific checks filters this out
    # without rejecting genuinely relevant general-language rules (e.g.
    # "habitable rooms... 6.5 m2" never says the word "bedroom" but is a
    # real bedroom-area rule).
    COMPLIANCE_MIN_SCORE = 0.55
    top_candidate = result["rules"][0] if result["rules"] else None
    confidently_relevant = (
        top_candidate is not None and top_candidate["score"] >= COMPLIANCE_MIN_SCORE
    )
    if not result["found_confident_match"] or not result["rules"] or not confidently_relevant:

        
        # Honest gap (F3 pattern). Cultural room types (majlis) predictably
        # land here — the codes are silent on them (F4), not a system failure.
        note = f"Not specified in code. ({result['advice']})"
        if room_type == "majlis":
            note += " Cultural requirement outside code coverage (see F4)."
        return {
            "room_type": room_type, "query": query, "status": "not_in_code",
            "rule_text": None, "score": None, "note": note,
        }

    top = result["rules"][0]
    return {
        "room_type": room_type, "query": query, "status": "found",
        "rule_text": top["text"][:220],   # trimmed for display
        "score": round(top["score"], 2),
        "note": f"Rule retrieved (confidence {top['score']:.2f}); "
                f"compare stated minimum against the design's drawn area "
                f"({sample_area:.1f} m\u00b2) manually until numeric "
                f"extraction is added.",
    }


def check_compliance(layout, country):
    """
    Run the compliance check for every room TYPE present in a layout.

    Returns a list of check_room_type() results, one per distinct room type.
    """
    seen_types = {}
    for room in layout["rooms"]:
        rt = room["type"]
        if rt not in seen_types:
            seen_types[rt] = room["w"] * room["h"]   # a representative drawn area

    return [check_room_type(rt, country, area) for rt, area in seen_types.items()]


def format_compliance_report(checks):
    """Human-readable compliance summary."""
    lines = []
    for c in checks:
        icon = {"found": "[FOUND]", "not_in_code": "[NOT IN CODE]"}.get(c["status"], "[?]")
        lines.append(f"{icon} {c['room_type'].upper()}")
        lines.append(f"   query: {c['query']}")
        if c["status"] == "found":
            lines.append(f"   rule (score {c['score']}): {c['rule_text']}")
        lines.append(f"   note: {c['note']}")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    from arqa.design_agent import generate_layout

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

    layout = generate_layout(sample)
    checks = check_compliance(layout, sample["country"])

    print("=" * 64)
    print("ARQA Compliance Checker (Day 16)")
    print("=" * 64)
    print(f"Country: {sample['country']}\n")
    print(format_compliance_report(checks))