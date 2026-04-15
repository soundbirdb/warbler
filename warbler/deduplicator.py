"""Deduplication utilities for finding duplicate audio files by fingerprint."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from warbler.tagger import read_fingerprint


@dataclass
class DuplicateGroup:
    """A group of audio files that share the same spectral fingerprint."""

    fingerprint: str
    paths: List[Path] = field(default_factory=list)

    @property
    def size(self) -> int:
        return len(self.paths)

    @property
    def is_duplicate(self) -> bool:
        return self.size > 1


@dataclass
class DeduplicationReport:
    """Summary of a deduplication scan."""

    scanned: int
    untagged: int
    duplicate_groups: List[DuplicateGroup]

    @property
    def duplicate_file_count(self) -> int:
        return sum(g.size for g in self.duplicate_groups if g.is_duplicate)

    @property
    def wasted_copies(self) -> int:
        """Number of files that are redundant (all but one per group)."""
        return sum(g.size - 1 for g in self.duplicate_groups if g.is_duplicate)


def find_duplicates(paths: List[Path]) -> DeduplicationReport:
    """Scan *paths* for audio files with matching fingerprints.

    Files without a fingerprint tag are counted but excluded from grouping.

    Args:
        paths: Iterable of audio file paths to inspect.

    Returns:
        A :class:`DeduplicationReport` describing the results.
    """
    groups: Dict[str, List[Path]] = defaultdict(list)
    untagged = 0

    for path in paths:
        fp: Optional[str] = read_fingerprint(path)
        if fp is None:
            untagged += 1
        else:
            groups[fp].append(path)

    duplicate_groups = [
        DuplicateGroup(fingerprint=fp, paths=file_paths)
        for fp, file_paths in groups.items()
        if len(file_paths) > 1
    ]

    return DeduplicationReport(
        scanned=len(paths),
        untagged=untagged,
        duplicate_groups=duplicate_groups,
    )
