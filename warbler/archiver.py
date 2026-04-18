"""Move or copy processed audio files into an organised archive directory."""
from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional

from warbler.tagger import read_fingerprint


@dataclass
class ArchiveResult:
    source: Path
    destination: Optional[Path]
    skipped: bool = False
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None and not self.skipped


@dataclass
class ArchiveReport:
    results: List[ArchiveResult] = field(default_factory=list)

    @property
    def moved_count(self) -> int:
        return sum(1 for r in self.results if r.success)

    @property
    def skipped_count(self) -> int:
        return sum(1 for r in self.results if r.skipped)

    @property
    def error_count(self) -> int:
        return sum(1 for r in self.results if r.error is not None)


def _build_destination(source: Path, archive_root: Path) -> Path:
    """Place file under archive_root/<first2_of_fingerprint>/<filename>."""
    fp = read_fingerprint(source)
    if fp:
        bucket = fp[:2]
    else:
        bucket = "untagged"
    return archive_root / bucket / source.name


def archive_file(
    source: Path,
    archive_root: Path,
    *,
    copy: bool = False,
    overwrite: bool = False,
    _read: Callable[[Path], Optional[str]] = read_fingerprint,
) -> ArchiveResult:
    try:
        fp = _read(source)
        bucket = fp[:2] if fp else "untagged"
        dest = archive_root / bucket / source.name
        if dest.exists() and not overwrite:
            return ArchiveResult(source=source, destination=dest, skipped=True)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if copy:
            shutil.copy2(source, dest)
        else:
            shutil.move(str(source), dest)
        return ArchiveResult(source=source, destination=dest)
    except Exception as exc:  # noqa: BLE001
        return ArchiveResult(source=source, destination=None, error=str(exc))


def batch_archive(
    sources: List[Path],
    archive_root: Path,
    *,
    copy: bool = False,
    overwrite: bool = False,
) -> ArchiveReport:
    report = ArchiveReport()
    for src in sources:
        result = archive_file(src, archive_root, copy=copy, overwrite=overwrite)
        report.results.append(result)
    return report
