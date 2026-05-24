"""
ARQA Phase 1 — Build Embedding Cache (Day 7)

Embeds the section-chunks ONCE with the semantic model and saves:
  - the filtered chunks      -> data/rag_index/prod_chunks.json
  - their embedding vectors  -> data/rag_index/prod_embeddings.npy

Run this once. The production retriever then loads the cache instantly
instead of re-embedding (which takes ~20 min on CPU).

Usage:  python -m arqa.build_embeddings

Author: Muhammad Irfan
"""

import os
import json
import time
import numpy as np
from sentence_transformers import SentenceTransformer
from arqa.rag_pipeline import load_chunks

MODEL_NAME = "all-MiniLM-L6-v2"
MIN_CHARS = 80   # drop chunks shorter than this (covers, labels, fragments)

SECTION_CHUNKS_PATH = "data/rag_index/section_chunks.json"
PROD_CHUNKS_PATH    = "data/rag_index/prod_chunks.json"
PROD_EMB_PATH       = "data/rag_index/prod_embeddings.npy"


def filter_chunks(chunks):
    """Keep only chunks long enough to hold a real rule."""
    kept = [c for c in chunks if len(c["text"].strip()) >= MIN_CHARS]
    print(f"Filtered: {len(chunks)} -> {len(kept)} chunks "
          f"(dropped {len(chunks) - len(kept)} short ones < {MIN_CHARS} chars)")
    return kept


def build_embedding_cache():
    # 1. Load section-chunks and filter out noise
    chunks = load_chunks(SECTION_CHUNKS_PATH)
    chunks = filter_chunks(chunks)

    # 2. Load the embedding model
    print(f"Loading model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    # 3. Embed every chunk's text (the slow, one-time step)
    texts = [c["text"] for c in chunks]
    print(f"Embedding {len(texts)} chunks (one-time, ~15-20 min on CPU)...")
    start = time.time()
    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,   # so dot product = cosine similarity
    )
    print(f"Embedded in {time.time() - start:.0f} seconds")

    # 4. Save both the chunks and their vectors
    os.makedirs(os.path.dirname(PROD_CHUNKS_PATH), exist_ok=True)
    with open(PROD_CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    np.save(PROD_EMB_PATH, embeddings)

    print(f"\nSaved {len(chunks)} chunks  -> {PROD_CHUNKS_PATH}")
    print(f"Saved embeddings {embeddings.shape} -> {PROD_EMB_PATH}")
    print("Embedding cache built. The production retriever can now load instantly.")


if __name__ == "__main__":
    build_embedding_cache()