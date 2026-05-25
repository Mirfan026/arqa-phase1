"""
ARQA Phase 1 — Day 12
End-to-end pipeline test: brief -> Supervisor (Communication Agent +
clarification) -> Design Agent -> floor plan. Proves the agents connect
through the blackboard.

Usage:  python -m scripts.test_pipeline
"""

from arqa.supervisor import process_brief
from arqa.design_agent import generate_layout, ascii_floorplan


def no_answers(field, question):
    """This brief is complete, so no clarification is expected."""
    return ""


if __name__ == "__main__":
    brief = (
        "I want a 4 bedroom villa in Riyadh with 2 bathrooms, a kitchen, "
        "a living room, and a separate majlis for guests."
    )

    print("=" * 64)
    print("STEP 1 — Supervisor: brief -> requirements (blackboard)")
    print("=" * 64)
    bb = process_brief(brief, no_answers)
    print(f"status: {bb['status']}")

    if bb["status"] != "ready":
        print("Brief not ready for design; would clarify first.")
    else:
        print("\n" + "=" * 64)
        print("STEP 2 — Design Agent: requirements -> floor plan")
        print("=" * 64)
        layout = generate_layout(bb["requirements"])
        bb["design"] = layout          # write the layout back to the blackboard
        print(layout["summary"])
        print()
        print(ascii_floorplan(layout))
        print("\nBlackboard now holds: " + ", ".join(bb.keys()))