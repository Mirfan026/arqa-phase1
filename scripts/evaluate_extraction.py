"""
ARQA Phase 1 — Day 9
Evaluation harness: run the Communication Agent on the annotated
test set and score extraction against ground truth.

Reports:
  - language detection: correct vs detected (exposes romanized gap)
  - field-level accuracy per brief
  - aggregate accuracy by input type

Usage:  python -m scripts.evaluate_extraction
"""

from arqa.communication_agent import extract_requirements
from scripts.test_briefs import TEST_BRIEFS


def get_room_min(data, room):
    """Safely read rooms.<room>.min, or None if absent."""
    rooms = data.get("rooms") or {}
    r = rooms.get(room)
    if isinstance(r, dict):
        return r.get("min")
    return None


def score_brief(expected, data):
    """
    Compare extracted data against expected ground truth for the
    KEY fields. Returns (correct_count, total_count, details list).
    """
    checks = []   # (field_name, passed, expected_val, got_val)

    # country
    if "country" in expected:
        got = data.get("country")
        checks.append(("country", got == expected["country"], expected["country"], got))

    # project_type
    if "project_type" in expected:
        got = data.get("project_type")
        checks.append(("project_type", got == expected["project_type"], expected["project_type"], got))

    # currency
    if "currency" in expected:
        budget = data.get("budget") or {}
        got = budget.get("currency") if isinstance(budget, dict) else None
        checks.append(("currency", got == expected["currency"], expected["currency"], got))

    # bedrooms (min)
    if "bedrooms" in expected:
        got = get_room_min(data, "bedrooms")
        checks.append(("bedrooms", got == expected["bedrooms"], expected["bedrooms"], got))

    # has_majlis (a majlis room present with a count)
    if "has_majlis" in expected:
        got = get_room_min(data, "majlis") is not None
        checks.append(("has_majlis", got == expected["has_majlis"], expected["has_majlis"], got))

    # cultural_flags_any (at least one flag)
    if "cultural_flags_any" in expected:
        flags = data.get("cultural_flags") or []
        got = len(flags) > 0
        checks.append(("cultural_flags_any", got == expected["cultural_flags_any"],
                       expected["cultural_flags_any"], got))

    # ready_for_design
    if "ready_for_design" in expected:
        got = data.get("ready_for_design")
        checks.append(("ready_for_design", got == expected["ready_for_design"],
                       expected["ready_for_design"], got))

    correct = sum(1 for _, passed, _, _ in checks if passed)
    return correct, len(checks), checks


if __name__ == "__main__":
    total_correct = 0
    total_checks = 0
    lang_detect_correct = 0

    print("=" * 72)
    print("ARQA Extraction Evaluation — 10 briefs (EN/UR/AR; pure, mixed, roman)")
    print("=" * 72)

    for tb in TEST_BRIEFS:
        data = extract_requirements(tb["brief"])

        # Language detection check
        detected = data.get("language")
        lang_ok = (detected == tb["language"])
        if lang_ok:
            lang_detect_correct += 1

        # Field scoring
        correct, total, checks = score_brief(tb["expected"], data)
        total_correct += correct
        total_checks += total

        print(f"\n[{tb['id']}]  type={tb['type']}")
        lang_mark = "OK" if lang_ok else "WRONG"
        print(f"  language: expected={tb['language']}  detected={detected}  [{lang_mark}]")
        print(f"  fields:   {correct}/{total} correct")
        for field, passed, exp, got in checks:
            if not passed:
                print(f"      MISS {field}: expected={exp}  got={got}")

    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(f"Language detection: {lang_detect_correct}/{len(TEST_BRIEFS)} correct")
    print(f"Field extraction:   {total_correct}/{total_checks} correct "
          f"({100 * total_correct / total_checks:.1f}%)")