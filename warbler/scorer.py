"""scorer.py – compute a quality score for an audio file based on metadata completeness and tagging status."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from warbler.metadata import FileMetadata, read_metadata
from warbler.tagger import read_fingerprint

# Fields considered when calculating completeness bonus
_SCORED_FIELDS = ("title", "artist", "album", "year", "genre")


@dataclass
class FileScore:
    path: Path
    fingerprint: Optional[str]
    metadata: Optional[FileMetadata]
    score: float  # 0.0 – 1.0
    reasons: List[str] = field(default_factory=list)

    @property
    def is_tagged(self) -> bool:
        return self.fingerprint is not None


@dataclass
class ScoreReport:
    entries: List[FileScore] = field(default_factory=list)

    @property
    def average_score(self) -> Optional[float]:
        if not self.entries:
            return None
        return sum(e.score for e in self.entries) / len(self.entries)

    @property
    def fully_scored(self) -> List[FileScore]:
        return [e for e in self.entries if e.score >= 1.0]

    @property
    def unscored(self) -> List[FileScore]:
        return [e for e in self.entries if e.score == 0.0]


def score_file(path: Path) -> FileScore:
    """Compute a quality score for a single audio file."""
    reasons: List[str] = []
    points = 0.0
    total = 0.0

    # 40 % weight: fingerprint present
    total += 0.4
    try:
        fp = read_fingerprint(path)
    except Exception:
        fp = None

    if fp:
        points += 0.4
    else:
        reasons.append("missing fingerprint")

    # 60 % weight: metadata fields (12 % each)
    weight_per_field = 0.6 / len(_SCORED_FIELDS)
    total += 0.6
    try:
        meta = read_metadata(path)
    except Exception:
        meta = None

    if meta is None:
        reasons.append("could not read metadata")
    else:
        for f in _SCORED_FIELDS:
            val = getattr(meta, f, None)
            if val:
                points += weight_per_field
            else:
                reasons.append(f"missing field: {f}")

    score = round(min(points / total, 1.0), 4) if total else 0.0
    return FileScore(path=path, fingerprint=fp, metadata=meta, score=score, reasons=reasons)


def batch_score(paths: List[Path]) -> ScoreReport:
    """Score a list of audio files and return a consolidated report."""
    report = ScoreReport()
    for p in paths:
        report.entries.append(score_file(p))
    return report
