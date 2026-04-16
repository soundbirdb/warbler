"""Filter audio files by fingerprint metadata criteria."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from warbler.tagger import read_fingerprint


@dataclass
class FilterCriteria:
    tagged_only: bool = False
    untagged_only: bool = False
    extension: Optional[str] = None  # e.g. ".mp3"

    def validate(self) -> None:
        if self.tagged_only and self.untagged_only:
            raise ValueError("tagged_only and untagged_only are mutually exclusive")


@dataclass
class FilterResult:
    path: Path
    fingerprint: Optional[str]

    @property
    def is_tagged(self) -> bool:
        return self.fingerprint is not None


def apply_filter(
    paths: Iterable[Path],
    criteria: FilterCriteria,
) -> list[FilterResult]:
    """Return FilterResult entries matching *criteria*."""
    criteria.validate()
    results: list[FilterResult] = []
    for path in paths:
        if criteria.extension and path.suffix.lower() != criteria.extension.lower():
            continue
        try:
            fp = read_fingerprint(path)
        except Exception:
            fp = None
        if criteria.tagged_only and fp is None:
            continue
        if criteria.untagged_only and fp is not None:
            continue
        results.append(FilterResult(path=path, fingerprint=fp))
    return results
