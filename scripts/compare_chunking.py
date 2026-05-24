"""
ARQA Phase 1 — Day 6
Compare retrieval quality: PAGE-chunks vs SECTION-chunks.

Same BM25 retriever, same queries — only the chunk granularity differs.
Goal: does section-level chunking surface more precise rules?
"""

from arqa.rag_pipeline import load_chunks
from arqa.retriever import CodeRetriever

QUERIES = [
    "minimum width of a pedestrian walkway",
    "minimum ceiling height for a room",
    "natural ventilation for habitable rooms",
]


def show_top(label, retriever, query, k=2):
    print(f"\n  --- {label} ---")
    results = retriever.search(query, top_k=k)
    for rank, r in enumerate(results, start=1):
        section = r.get("section")
        sec_str = f" sec.{section}" if section else ""
        preview = " ".join(r["text"].split())[:160]
        print(f"  [{rank}] score={r['score']} | {r['country']} "
              f"p.{r['pdf_page']}{sec_str}")
        print(f"      {preview}")


if __name__ == "__main__":
    print("Loading PAGE-chunks...")
    page_chunks = load_chunks("data/rag_index/chunks.json")
    page_retriever = CodeRetriever(page_chunks)

    print("\nLoading SECTION-chunks...")
    section_chunks = load_chunks("data/rag_index/section_chunks.json")
    section_retriever = CodeRetriever(section_chunks)

    for query in QUERIES:
        print("\n" + "=" * 70)
        print(f"QUERY: {query}")
        print("=" * 70)
        show_top("PAGE-chunks (Day 5)", page_retriever, query)
        show_top("SECTION-chunks (Day 6)", section_retriever, query)