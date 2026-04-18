"""Remove duplicate or orphaned fingerprint tags from audio files."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from warbler.tagger import read_fingerprint, write_fingerprint, _get_extension


@dataclass
class CleanResult:
    path: Path
    cleaned: bool
    reason: str = ""
    error: str = ""

    @property
    def success(self) -> bool:
        return not self.error


@dataclass
class CleanReport:
    results: list[CleanResult] = field(default_factory=list)

    @property
    def cleaned_count(self) -> int:
        return sum(1 for r in self.results if r.cleaned)

    @property
    def skipped_count(self) -> int:
        return sum(1 for r in self.results if r.success and not r.cleaned)

    @property
    def error_count(self) -> int:
        return sum(1 for r in self.results if not r.success)


SUPPORTED = {".mp3", ".flac", ".ogg", ".m4a"}


def clean_file(path: Path, *, dry_run: bool = False) -> CleanResult:
    """Remove the fingerprint tag from *path* if one exists."""
    if path.suffix.lower() not in SUPPORTED:
        return CleanResult(path=path, cleaned=False, reason="unsupported format")
    try:
        existing = read_fingerprint(path)
    except Exception as exc:  # noqa: BLE001
        return CleanResult(path=path, cleaned=False, error=str(exc))

    if existing is None:
        return CleanResult(path=path, cleaned=False, reason="no fingerprint present")

    if dry_run:
        return CleanResult(path=path, cleaned=True, reason="dry-run")

    try:
        _remove_fingerprint(path)
    except Exception as exc:  # noqa: BLE001
        return CleanResult(path=path, cleaned=False, error=str(exc))

    return CleanResult(path=path, cleaned=True)


def _remove_fingerprint(path: Path) -> None:
    ext = _get_extension(path)
    if ext == ".mp3":
        from mutagen.id3 import ID3
        tags = ID3(path)
        tags.delall("TXXX:WARBLER_FINGERPRINT")
        tags.save(path)
    elif ext in (".flac", ".ogg"):
        from mutagen import File as MutagenFile
        audio = MutagenFile(path)
        audio.pop("warbler_fingerprint", None)
        audio.save()
    elif ext == ".m4a":
        from mutagen.mp4 import MP4
        audio = MP4(path)
        audio.tags.pop("----:com.apple.iTunes:WARBLER_FINGERPRINT", None)
        audio.save()


def batch_clean(paths: Sequence[Path], *, dry_run: bool = False) -> CleanReport:
    report = CleanReport()
    for p in paths:
        report.results.append(clean_file(p, dry_run=dry_run))
    return report
