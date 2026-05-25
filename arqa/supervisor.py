"""
ARQA Phase 1 — Supervisor

The orchestrator of the multi-agent system. Holds the shared 'blackboard'
state, runs the Communication Agent, and — when an essential field is
missing — runs the CLARIFICATION LOOP: ask the client, fill the gap,
re-check. The "ask, never guess" principle made real.

Phase 1 scope: state management (blackboard) + brief validation /
clarification. The Design and Report agents will plug into the same
blackboard in later days.

Author: Muhammad Irfan
"""

from arqa.communication_agent import extract_requirements

# A human-readable question for each essential field the Supervisor
# might need to ask the client about.
QUESTION_FOR_FIELD = {
    "country": "Which country or city is the project located in?",
    "project_type": "What type of building is it? (e.g. villa, house, apartment)",
    "rooms": "How many rooms do you need? (e.g. bedrooms, bathrooms, kitchen)",
}

# How to frame the client's answer as a clear statement for re-extraction,
# so the appended text is unambiguous (raw concatenation confuses the LLM).
ANSWER_FRAMING = {
    "country": "The project location is: {answer}.",
    "project_type": "The building type is: {answer}.",
    "rooms": "The rooms required are: {answer}.",
}

def make_blackboard(brief):
    """Create a fresh shared-state object for one project request."""
    return {
        "brief": brief,
        "requirements": None,     # filled by the Communication Agent
        "status": "new",          # new -> extracted -> ready / incomplete
        "clarifications": [],     # audit trail of questions asked + answers
    }


def question_for(field):
    """Return a client-friendly question for a missing field."""
    return QUESTION_FOR_FIELD.get(field, f"Please provide the {field}.")


def process_brief(brief, answer_fn, max_rounds=3, verbose=True):
    """
    Orchestrate one project request from raw brief to a complete blackboard.

    Steps:
      1. Create the blackboard.
      2. Run the Communication Agent -> requirements on the blackboard.
      3. If not ready_for_design, run the CLARIFICATION LOOP:
           - ask the client (via answer_fn) about each missing essential field
           - append answers to the accumulated brief, re-extract, re-check
         up to max_rounds.
      4. Set final status: 'ready' or 'incomplete'.

    answer_fn(field, question) -> str : supplies the client's answer.
      (canned in tests, input() in a terminal, a form in a web app.)

    Returns the final blackboard dict.
    """
    bb = make_blackboard(brief)

    # Step 2: first extraction
    accumulated = brief
    reqs = extract_requirements(accumulated)
    bb["requirements"] = reqs
    bb["status"] = "extracted"

    if verbose:
        print(f"Initial extraction: ready_for_design={reqs['ready_for_design']}, "
              f"missing={reqs['missing_required']}")

    # Step 3: clarification loop
    rounds = 0
    while not reqs["ready_for_design"] and rounds < max_rounds:
        rounds += 1
        if verbose:
            print(f"\n-- Clarification round {rounds} --")

        for field in list(reqs["missing_required"]):
            q = question_for(field)
            answer = answer_fn(field, q)            # <- ask via injected function
            bb["clarifications"].append(
                {"round": rounds, "field": field, "question": q, "answer": answer}
            )
            framing = ANSWER_FRAMING.get(field, "{answer}")
            accumulated += " " + framing.format(answer=str(answer))
            if verbose:
                print(f"   ASK [{field}]: {q}")
                print(f"   ANS: {answer}")

        # Re-extract with the accumulated information, then re-check
        reqs = extract_requirements(accumulated)
        bb["requirements"] = reqs
        if verbose:
            print(f"   -> re-check: ready_for_design={reqs['ready_for_design']}, "
                  f"missing={reqs['missing_required']}")

    # Step 4: final status
    bb["status"] = "ready" if reqs["ready_for_design"] else "incomplete"
    return bb


if __name__ == "__main__":
    import json

    # ----- A simple canned answer function for testing -----
    # Maps a field -> the answer a test 'client' would give.
    def canned_answers(answers):
        def _fn(field, question):
            return answers.get(field, "")
        return _fn

    # TEST 1: a COMPLETE brief — no clarification should be needed.
    print("=" * 64)
    print("TEST 1 — complete brief (expect: ready immediately, no questions)")
    print("=" * 64)
    complete = (
        "I want a 4 bedroom villa in Riyadh, budget around 1.5 million riyals, "
        "with a separate majlis for guests."
    )
    bb1 = process_brief(complete, canned_answers({}))
    print(f"\nFINAL STATUS: {bb1['status']}")
    print(f"Clarifications asked: {len(bb1['clarifications'])}")

    # TEST 2: an INCOMPLETE brief (no country) — loop should ask, then resolve.
    print("\n" + "=" * 64)
    print("TEST 2 — incomplete brief (no country; expect: asks, then ready)")
    print("=" * 64)
    incomplete = (
        "looking for a family home, maybe 3 or 4 beds, with privacy from the "
        "street and a place to receive male guests."
    )
    # The test 'client' answers 'Lahore' when asked about country.
    bb2 = process_brief(incomplete, canned_answers({"country": "in Lahore"}))
    print(f"\nFINAL STATUS: {bb2['status']}")
    print(f"Clarifications asked: {len(bb2['clarifications'])}")
    print("\nFinal requirements (country should now be filled):")
    r = bb2["requirements"]
    print(f"   country = {r.get('country')}")
    print(f"   ready_for_design = {r.get('ready_for_design')}")