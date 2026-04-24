"""Batch fingerprint comparison: compare a reference file against a corpus."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, List, Optional

from warbler.tagger import read_fingerprint
from warbler.similarity import find_similar, SimilarityMatch


@dataclass
class ComparisonResult:
    reference: Path
    reference_fingerprint: str
    matches: List[SimilarityMatch] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def has_matches(self) -> bool:
        return bool(self.matches)

    @property
    def best_match(self) -> Optional[SimilarityMatch]:
        return self.matches[0] if self.matches else None


@dataclass
class ComparisonReport:
    results: List[ComparisonResult] = field(default_factory=list)

    @property
    def match_count(self) -> int:
        return sum(1 for r in self.results if r.has_matches)

    @property
    def error_count(self) -> int:
        return sum(1 for r in self.results if r.error)


def compare_file(
    reference: Path,
    corpus: Iterable[Path],
    threshold: float = 0.85,
    _read: Callable[[Path], Optional[str]] = read_fingerprint,
) -> ComparisonResult:
    """Compare *reference* against every path in *corpus* by fingerprint similarity."""
    ref_fp = _read(reference)
    if ref_fp is None:
        return ComparisonResult(
            reference=reference,
            reference_fingerprint="",
            error=f"No fingerprint tag found on reference file: {reference}",
        )

    fingerprints: dict[Path, str] = {}
    for path in corpus:
        if path == reference:
            continue
        fp = _read(path)
        if fp is not None:
            fingerprints[path] = fp

    matches = find_similar(ref_fp, fingerprints, threshold=threshold)
    return ComparisonResult(
        reference=reference,
        reference_fingerprint=ref_fp,
        matches=matches,
    )


def batch_compare(
    references: Iterable[Path],
    corpus: Iterable[Path],
    threshold: float = 0.85,
    _read: Callable[[Path], Optional[str]] = read_fingerprint,
) -> ComparisonReport:
    """Run :func:`compare_file` for each reference and collect results."""
    corpus_list = list(corpus)
    report = ComparisonReport()
    for ref in references:
        result = compare_file(ref, corpus_list, threshold=threshold, _read=_read)
        report.results.append(result)
    return report
