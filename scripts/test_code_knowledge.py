"""
ARQA Phase 1 — Day 7
Test the production interface exactly as an agent would call it.
Now shows the confidence verdict for each query.
"""

from arqa.code_knowledge import get_relevant_rules


def show(query, country=None):
    print("\n" + "=" * 70)
    label = query + (f"   [country={country}]" if country else "")
    print(f"QUERY: {label}")
    print("=" * 70)

    response = get_relevant_rules(query, country=country, top_k=3)

    verdict = "CONFIDENT" if response["found_confident_match"] else "LOW CONFIDENCE"
    print(f"VERDICT: {verdict}")
    print(f"ADVICE:  {response['advice']}")

    for rank, r in enumerate(response["rules"], start=1):
        flag = "OK" if r["confident"] else "weak"
        sec = f" §{r['section']}" if r["section"] else ""
        print(f"\n[{rank}] ({flag}) score={r['score']} | {r['country']} | "
              f"{r['source_file']} p.{r['pdf_page']}{sec}")
        preview = " ".join(r["text"].split())[:180]
        print(f"    {preview}")


if __name__ == "__main__":
    # 1. General query (all countries)
    show("minimum ceiling height for a habitable room")

    # 2. Same query, filtered to one country
    show("minimum ceiling height for a habitable room", country="saudi_arabia")

    # 3. A different rule type
    show("minimum width of a pedestrian walkway")

    # 4. The conceptual query that exposed the privacy gap
    show("privacy requirements for windows overlooking neighbours")
