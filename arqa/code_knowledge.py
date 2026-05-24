"""
ARQA Phase 1 — Building-Code Knowledge Interface (Day 7)

The clean, production interface the agents call. Loads the cached
section-chunk embeddings and answers: "what building rules are
relevant to this query?" — with an honest confidence verdict.

This hides ALL retrieval internals (embeddings, cosine similarity,
chunk metadata) behind one function: get_relevant_rules().

Usage:
    from arqa.code_knowledge import get_relevant_rules
    resp = get_relevant_rules("minimum ceiling height", country="saudi_arabia")
    if resp["found_confident_match"]:
        use resp["rules"]

Author: Muhammad Irfan
"""

import json
import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"
PROD_CHUNKS_PATH = "data/rag_index/prod_chunks.json"
PROD_EMB_PATH    = "data/rag_index/prod_embeddings.npy"

# Confidence cutoff, chosen from observed data:
#   confident correct answers scored 0.66-0.83
#   the weak privacy query scored 0.42
# So 0.45 cleanly separates "trustworthy" from "unsure".
DEFAULT_MIN_SCORE = 0.45


class CodeKnowledge:
    """
    Loads the cached embeddings + chunks and serves rule lookups.
    Build it ONCE, then call .query() many times.
    """

    def __init__(self):
        # Load cached chunks (text + metadata)
        with open(PROD_CHUNKS_PATH, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)

        # Load cached embedding vectors (instant — no re-embedding)
        self.embeddings = np.load(PROD_EMB_PATH)

        # Load the model (needed only to embed incoming QUERIES)
        self.model = SentenceTransformer(MODEL_NAME)

        print(f"CodeKnowledge ready: {len(self.chunks)} rules loaded")

    def query(self, query, country=None, top_k=5, min_score=DEFAULT_MIN_SCORE):
        # Embed the incoming query
        q_vec = self.model.encode(
            [query], convert_to_numpy=True, normalize_embeddings=True
        )[0]

        # Cosine similarity against all chunks (vectors are normalized)
        scores = self.embeddings @ q_vec

        # Pair scores with positions, optionally filter by country
        scored = list(zip(scores, range(len(self.chunks))))
        if country:
            scored = [(s, i) for s, i in scored
                      if self.chunks[i]["country"] == country]

        scored.sort(reverse=True)

        results = []
        for score, idx in scored[:top_k]:
            c = self.chunks[idx]
            s = round(float(score), 3)
            results.append({
                "score": s,
                "confident": s >= min_score,   # did this clear the bar?
                "country": c["country"],
                "source_file": c["source_file"],
                "pdf_page": c["pdf_page"],
                "section": c.get("section"),
                "text": c["text"],
            })
        return results


# ── Module-level singleton so agents don't rebuild the index ──
_knowledge = None


def get_relevant_rules(query, country=None, top_k=5, min_score=DEFAULT_MIN_SCORE):
    """
    THE function agents call. Returns relevant building rules for a
    query, with an honest confidence verdict.

    Returns a dict:
      {
        "query": <the query>,
        "country": <filter or None>,
        "found_confident_match": <bool>,   # is the top result trustworthy?
        "advice": <str>,                    # what the agent should do
        "rules": [ <rule dicts, each with a 'confident' flag> ],
      }
    """
    global _knowledge
    if _knowledge is None:
        _knowledge = CodeKnowledge()

    rules = _knowledge.query(query, country=country,
                             top_k=top_k, min_score=min_score)

    # Is the BEST result confident? (rules are sorted, so check the first)
    top_confident = bool(rules) and rules[0]["confident"]

    if top_confident:
        advice = "Confident match found. Safe to use the top rule(s)."
    else:
        advice = ("No confident match. The codes in scope may not cover "
                  "this topic. Advise the user to verify with local "
                  "authorities rather than relying on these results.")

    return {
        "query": query,
        "country": country,
        "found_confident_match": top_confident,
        "advice": advice,
        "rules": rules,
    }