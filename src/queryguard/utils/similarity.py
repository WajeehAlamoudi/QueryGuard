from __future__ import annotations
from difflib import get_close_matches


def find_similar(name: str, candidates: list[str], n: int = 3, cutoff: float = 0.6) -> list[str]:
    return get_close_matches(name, candidates, n=n, cutoff=cutoff)
