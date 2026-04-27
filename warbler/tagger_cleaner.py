"""tagger_cleaner.py – remove stale or duplicate fingerprint tags from audio files."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, List, Optional

from warbler.tagger import _get_extension, read_fingerprint


@dataclass
class TagCleanResult:
    path: Path
    removed: bool
    dry_run: bool
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None


@dataclass
class TagCleanReport:
    results: List[TagCleanResult] = field(default_factory=list)

    @property
    def removed_count(self) -> int:
        return sum(1 for r in self.results if r.removed and r.success)

    @property
    def skipped_count(self) -> int:
        return sum(1 for r in self.results if not r.removed and r.success)

    @property
    def error_count(self) -> int:
        return sum(1 for r in self.results if not r.success)


_SUPPORTED = {".mp3", ".flac"}


def _remove_tag_mp3(path: Path) -> None:
    from mutagen.id3 import ID3
    tags = ID3(path)
    keys = [k for k in tags.keys() if k.startswith("TXXX:SPECTRAL_FINGERPRINT")]
    for k in keys:
        tags.delall(k)
    tags.save(path)


def _remove_tag_flac(path: Path) -> None:
    from mutagen.flac import FLAC
    audio = FLAC(path)
    audio.pop("spectral_fingerprint", None)
    audio.save()


_REMOVERS: dict = {
    ".mp3": _remove_tag_mp3,
    ".flac": _remove_tag_flac,
}


def clean_tag(
    path: Path,
    *,
    dry_run: bool = False,
    read_fn: Callable[[Path], Optional[str]] = read_fingerprint,
) -> TagCleanResult:
    ext = _get_extension(path)
    if ext not in _SUPPORTED:
        return TagCleanResult(path=path, removed=False, dry_run=dry_run,
                              error=f"Unsupported format: {ext}")
    try:
        existing = read_fn(path)
        if existing is None:
            return TagCleanResult(path=path, removed=False, dry_run=dry_run)
        if not dry_run:
            _REMOVERS[ext](path)
        return TagCleanResult(path=path, removed=True, dry_run=dry_run)
    except Exception as exc:  # noqa: BLE001
        return TagCleanResult(path=path, removed=False, dry_run=dry_run, error=str(exc))


def batch_clean(
    paths: Iterable[Path],
    *,
    dry_run: bool = False,
    read_fn: Callable[[Path], Optional[str]] = read_fingerprint,
) -> TagCleanReport:
    report = TagCleanReport()
    for p in paths:
        report.results.append(clean_tag(p, dry_run=dry_run, read_fn=read_fn))
    return report
