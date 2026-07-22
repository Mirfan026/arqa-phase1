"""
ARQA Phase 1 — Supervisor

The orchestrator of the multi-agent system. Holds the shared 'blackboard'
state, runs the Communication Agent, and — when an essential field is
missing — runs the CLARIFICATION LOOP: ask the client, fill the gap,
re-check. The "ask, never guess" principle made real.

Also holds run_full_pipeline() (Day 18) — the TRUE end-to-end flow: brief
-> clarification loop -> [only if ready] -> Design Agent -> Cost Estimator
-> Compliance Checker -> trilingual PDF report. "Ask, never guess" applies
here too: if the brief never reaches ready_for_design, the pipeline stops
and reports what's missing rather than handing incomplete requirements
downstream to be silently filled in.

Author: Muhammad Irfan
"""

from arqa.communication_agent import extract_requirements
from arqa.report_agent import assemble_report
from arqa.report_pdf import render_report_pdf

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


def run_full_pipeline(brief, answer_fn, language="english", out_path="report.pdf",
                       max_rounds=3, verbose=True):
    """
    The true end-to-end flow (Day 18): brief -> (Communication Agent +
    clarification loop) -> [only if ready] -> Design Agent -> Cost
    Estimator -> Compliance Checker -> trilingual PDF report.

    "Ask, never guess" extended to orchestration: if the brief never
    reaches ready_for_design (something essential stays unanswered after
    max_rounds), the pipeline STOPS and reports what's missing — it never
    hands incomplete requirements downstream to be silently filled in.

    Returns a dict:
      { "status": "ready"/"incomplete", "blackboard": {...},
        "report_path": <path or None> }
    """
    bb = process_brief(brief, answer_fn, max_rounds=max_rounds, verbose=verbose)

    if bb["status"] != "ready":
        if verbose:
            print(f"\nPIPELINE STOPPED: brief incomplete after {max_rounds} "
                  f"round(s). Missing: {bb['requirements']['missing_required']}")
        return {"status": "incomplete", "blackboard": bb, "report_path": None}

    if verbose:
        print("\n-- Requirements ready. Continuing: Design -> Cost -> "
              "Compliance -> Report --")

    report_data = assemble_report(bb["requirements"])
    bb["report"] = report_data   # write back to the blackboard

    render_report_pdf(report_data, language, out_path)

    if verbose:
        print(f"Report written: {out_path}")

    return {"status": "ready", "blackboard": bb, "report_path": out_path}


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

    # TEST 3: full pipeline, complete brief -> should produce a real PDF.
    print("\n" + "=" * 64)
    print("TEST 3 — full pipeline (complete brief -> PDF)")
    print("=" * 64)
    result = run_full_pipeline(complete, canned_answers({}), out_path="pipeline_test.pdf")
    print(f"\nPipeline status: {result['status']}")
    print(f"Report path: {result['report_path']}")

    # TEST 4: full pipeline, brief missing something the client never
    # answers -> should STOP, not guess.
    print("\n" + "=" * 64)
    print("TEST 4 — full pipeline (client never answers -> should STOP)")
    print("=" * 64)
    result2 = run_full_pipeline(incomplete, canned_answers({}), out_path="pipeline_test2.pdf")
    print(f"\nPipeline status: {result2['status']}")
    print(f"Report path: {result2['report_path']}")