"""Inspector: summarise the tag health and metadata completeness of a file set."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from warbler.tagger import read_fingerprint
from warbler.metadata import read_metadata


@dataclass
class FileInspection:
    path: Path
    fingerprint: Optional[str]
    has_title: bool
    has_artist: bool
    has_album: bool
    error: Optional[str] = None

    @property
    def is_tagged(self) -> bool:
        return self.fingerprint is not None

    @property
    def is_complete(self) -> bool:
        return self.is_tagged and self.has_title and self.has_artist and self.has_album


@dataclass
class InspectionReport:
    inspections: List[FileInspection] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.inspections)

    @property
    def tagged_count(self) -> int:
        return sum(1 for i in self.inspections if i.is_tagged)

    @property
    def complete_count(self) -> int:
        return sum(1 for i in self.inspections if i.is_complete)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.inspections if i.error is not None)


def inspect_file(path: Path) -> FileInspection:
    """Inspect a single audio file and return a FileInspection."""
    try:
        fingerprint = read_fingerprint(path)
        meta = read_metadata(path)
        return FileInspection(
            path=path,
            fingerprint=fingerprint,
            has_title=bool(meta.title),
            has_artist=bool(meta.artist),
            has_album=bool(meta.album),
        )
    except Exception as exc:  # noqa: BLE001
        return FileInspection(
            path=path,
            fingerprint=None,
            has_title=False,
            has_artist=False,
            has_album=False,
            error=str(exc),
        )


def inspect_files(paths: List[Path]) -> InspectionReport:
    """Inspect a collection of audio files and return an InspectionReport."""
    report = InspectionReport()
    for path in paths:
        report.inspections.append(inspect_file(path))
    return report
