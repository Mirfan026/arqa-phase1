"""
ARQA Phase 1 — Semantic Retriever (Day 5, embeddings comparison)

Mirrors CodeRetriever (BM25) but uses sentence-embeddings for
semantic search. Built to compare lexical vs semantic retrieval
on the same building-code chunks.

Author: Muhammad Irfan
"""

import time
import numpy as np
from sentence_transformers import SentenceTransformer
from arqa.rag_pipeline import load_chunks


class SemanticRetriever:
    """
    Builds an embedding index over building-code chunks and retrieves
    the most semantically-similar chunks for a query.
    """

    def __init__(self, chunks, model_name="all-MiniLM-L6-v2"):
        self.chunks = chunks
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)

        # Embed every chunk's text into a 384-dim vector
        texts = [chunk["text"] for chunk in chunks]
        print(f"Embedding {len(texts)} chunks (this takes a couple of minutes)...")
        start = time.time()
        self.embeddings = self.model.encode(
            texts,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True,   # so dot product = cosine similarity
        )
        elapsed = time.time() - start
        print(f"Embedded {len(texts)} chunks in {elapsed:.1f} seconds")

    def search(self, query, top_k=5, country=None):
        # Embed the query the same way
        query_vec = self.model.encode(
            [query], convert_to_numpy=True, normalize_embeddings=True
        )[0]

        # Cosine similarity = dot product (vectors are normalized)
        scores = self.embeddings @ query_vec   # one score per chunk

        scored = list(zip(scores, range(len(self.chunks))))

        if country:
            scored = [
                (s, i) for s, i in scored
                if self.chunks[i]["country"] == country
            ]

        scored.sort(reverse=True)

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


if __name__ == "__main__":
    chunks = load_chunks()
    retriever = SemanticRetriever(chunks)

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
            preview = " ".join(r["text"].split())[:280]
            print(f"    {preview}")