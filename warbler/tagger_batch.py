"""Batch metadata writing utilities for warbler."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

from warbler.tagger import write_fingerprint, read_fingerprint


@dataclass
class BatchWriteResult:
    path: Path
    ok: bool
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.ok


@dataclass
class BatchWriteReport:
    results: List[BatchWriteResult] = field(default_factory=list)

    @property
    def written_count(self) -> int:
        return sum(1 for r in self.results if r.ok)

    @property
    def error_count(self) -> int:
        return sum(1 for r in self.results if not r.ok)

    @property
    def failed_paths(self) -> List[Path]:
        return [r.path for r in self.results if not r.ok]


def write_fingerprint_to_file(
    path: Path,
    fingerprint: str,
    *,
    dry_run: bool = False,
    _write: Callable[[Path, str], None] = write_fingerprint,
) -> BatchWriteResult:
    """Write a fingerprint to a single file, returning a result."""
    try:
        if not dry_run:
            _write(path, fingerprint)
        return BatchWriteResult(path=path, ok=True)
    except Exception as exc:  # noqa: BLE001
        return BatchWriteResult(path=path, ok=False, error=str(exc))


def batch_write_fingerprints(
    mapping: Dict[Path, str],
    *,
    dry_run: bool = False,
    _write: Callable[[Path, str], None] = write_fingerprint,
) -> BatchWriteReport:
    """Write fingerprints to multiple files from a path→fingerprint mapping."""
    report = BatchWriteReport()
    for path, fp in mapping.items():
        result = write_fingerprint_to_file(
            path, fp, dry_run=dry_run, _write=_write
        )
        report.results.append(result)
    return report
