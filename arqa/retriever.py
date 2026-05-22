"""
ARQA Phase 1 — BM25 Retriever (Day 5)

Loads the cached building-code chunks, builds a BM25 keyword index,
and retrieves the most relevant chunks for a query.

This is the "retrieval" half of RAG: given a question, find the
building-code passages most likely to contain the answer.

Author: Muhammad Irfan
"""

import re
from rank_bm25 import BM25Okapi
from arqa.rag_pipeline import load_chunks


def tokenize(text):
    """
    Split text into lowercase word tokens for BM25.

    Building codes are full of terms like 'ceiling height' and
    'minimum area' — simple word tokenization works well.
    """
    # Lowercase, then grab sequences of letters/digits as words
    return re.findall(r"[a-z0-9]+", text.lower())

class CodeRetriever:
    """
    Builds a BM25 index over building-code chunks and retrieves
    the most relevant chunks for a query.
    """

    def __init__(self, chunks):
        """
        Build the BM25 index from a list of chunk dicts.
        """
        self.chunks = chunks

        # Tokenize every chunk's text into a list of words
        tokenized_corpus = [tokenize(chunk["text"]) for chunk in chunks]

        # Build the BM25 index over the tokenized chunks
        self.bm25 = BM25Okapi(tokenized_corpus)
        print(f"BM25 index built over {len(chunks)} chunks")

    def search(self, query, top_k=5, country=None):
        """
        Return the top_k most relevant chunks for a query.

        Args:
            query:   the question text
            top_k:   how many results to return
            country: optional filter, e.g. "saudi_arabia" — only
                     search within that country's code
        """
        tokenized_query = tokenize(query)

        # Get a BM25 relevance score for every chunk
        scores = self.bm25.get_scores(tokenized_query)

        # Pair each chunk with its score and its position
        scored = list(zip(scores, range(len(self.chunks))))

        # Optionally filter by country
        if country:
            scored = [
                (s, i) for s, i in scored
                if self.chunks[i]["country"] == country
            ]

        # Sort by score, highest first
        scored.sort(reverse=True)

        # Take the top_k and attach the score to each chunk
        results = []
        for score, idx in scored[:top_k]:
            chunk = self.chunks[idx]
            results.append({
                "score": round(float(score), 3),
                "country": chunk["country"],
                "source_file": chunk["source_file"],
                "pdf_page": chunk["pdf_page"],
                "text": chunk["text"],
            })
        return results
    
    # ─────────────────────────────────────────────────────────────
# Self-test: run with  python arqa/retriever.py
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Load cached chunks and build the index
    chunks = load_chunks()
    retriever = CodeRetriever(chunks)

    # Real building-code questions to test retrieval
    test_queries = [
        "minimum width of a pedestrian walkway",
        "natural ventilation requirements for habitable rooms",
        "minimum ceiling height for a room",
        "means of egress exit door width",
    ]

    for query in test_queries:
        print("\n" + "=" * 70)
        print(f"QUERY: {query}")
        print("=" * 70)

        results = retriever.search(query, top_k=3)

        for rank, r in enumerate(results, start=1):
            print(f"\n[{rank}] score={r['score']} | {r['country']} | "
                  f"{r['source_file']} p.{r['pdf_page']}")
            # Show a short preview of the matched text
            preview = " ".join(r["text"].split())[:280]
            print(f"    {preview}")