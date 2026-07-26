"""Pure vector similarity helpers — no I/O, no LLM calls."""

from __future__ import annotations

import math


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError("Vectors must be the same length to compare")
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def top_k_similar(
    query_vector: list[float],
    candidates: dict[str, list[float]],
    k: int,
) -> list[tuple[str, float]]:
    """Return the top ``k`` (task_id, similarity) pairs, highest first."""
    scored = [(task_id, cosine_similarity(query_vector, vector)) for task_id, vector in candidates.items()]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:k]
