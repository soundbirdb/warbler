"""Hamming-distance based similarity search over stored fingerprints."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from warbler.exporter import collect_fingerprint_records


@dataclass
class SimilarityMatch:
    path: Path
    fingerprint: str
    distance: int

    @property
    def score(self) -> float:
        """Normalised similarity 0.0 (different) – 1.0 (identical)."""
        return 1.0 - self.distance / 256.0


def _hamming(a: str, b: str) -> int:
    """Bit-level Hamming distance between two hex fingerprint strings."""
    if len(a) != len(b):
        raise ValueError("Fingerprints must be the same length")
    dist = 0
    for ca, cb in zip(bytes.fromhex(a), bytes.fromhex(b)):
        dist += bin(ca ^ cb).count("1")
    return dist


def find_similar(
    query: str,
    search_paths: List[Path],
    threshold: float = 0.85,
    recursive: bool = True,
) -> List[SimilarityMatch]:
    """Return files whose fingerprint similarity to *query* meets *threshold*."""
    records = collect_fingerprint_records(search_paths, recursive=recursive)
    matches: List[SimilarityMatch] = []
    for record in records:
        fp = record.get("fingerprint", "")
        if not fp:
            continue
        try:
            dist = _hamming(query, fp)
        except ValueError:
            continue
        match = SimilarityMatch(
            path=Path(record["path"]),
            fingerprint=fp,
            distance=dist,
        )
        if match.score >= threshold:
            matches.append(match)
    matches.sort(key=lambda m: m.distance)
    return matches
