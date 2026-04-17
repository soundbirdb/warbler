"""Aggregate tagging statistics across a collection of audio files."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from warbler.tagger import read_fingerprint


@dataclass
class TagStats:
    total: int = 0
    tagged: int = 0
    untagged: int = 0
    by_extension: dict[str, int] = field(default_factory=dict)

    @property
    def tagged_ratio(self) -> float:
        if self.total == 0:
            return 0.0
        return self.tagged / self.total


def collect_stats(paths: Iterable[Path]) -> TagStats:
    """Walk *paths* and return tagging statistics."""
    stats = TagStats()
    for path in paths:
        stats.total += 1
        ext = path.suffix.lower().lstrip(".")
        stats.by_extension[ext] = stats.by_extension.get(ext, 0) + 1
        try:
            fp = read_fingerprint(path)
        except Exception:
            fp = None
        if fp:
            stats.tagged += 1
        else:
            stats.untagged += 1
    return stats


def format_stats(stats: TagStats) -> str:
    lines = [
        f"Total files : {stats.total}",
        f"Tagged      : {stats.tagged}",
        f"Untagged    : {stats.untagged}",
        f"Tagged ratio: {stats.tagged_ratio:.1%}",
        "By extension:",
    ]
    for ext, count in sorted(stats.by_extension.items()):
        lines.append(f"  .{ext}: {count}")
    return "\n".join(lines)
