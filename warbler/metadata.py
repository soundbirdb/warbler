"""Read and summarise embedded metadata fields from audio files."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC

_COMMON_FIELDS = ("title", "artist", "album", "date", "genre", "tracknumber")


@dataclass
class FileMetadata:
    path: Path
    fields: Dict[str, str] = field(default_factory=dict)
    error: Optional[str] = None

    @property
    def is_complete(self) -> bool:
        """True when all common fields are present and non-empty."""
        return all(self.fields.get(f) for f in _COMMON_FIELDS)

    @property
    def missing_fields(self) -> List[str]:
        return [f for f in _COMMON_FIELDS if not self.fields.get(f)]


def read_metadata(path: Path) -> FileMetadata:
    """Return a FileMetadata for *path*, tolerating unsupported formats."""
    ext = path.suffix.lower()
    try:
        if ext == ".mp3":
            audio = EasyID3(path)
            fields = {k: audio[k][0] for k in _COMMON_FIELDS if k in audio}
        elif ext == ".flac":
            audio = FLAC(path)
            fields = {k: audio[k][0] for k in _COMMON_FIELDS if k in audio}
        else:
            return FileMetadata(path=path, error=f"Unsupported format: {ext}")
    except Exception as exc:  # noqa: BLE001
        return FileMetadata(path=path, error=str(exc))
    return FileMetadata(path=path, fields=fields)


def batch_read_metadata(paths: List[Path]) -> List[FileMetadata]:
    return [read_metadata(p) for p in paths]


def format_metadata_report(records: List[FileMetadata]) -> str:
    lines: List[str] = []
    complete = sum(1 for r in records if r.is_complete)
    errors = sum(1 for r in records if r.error)
    lines.append(f"Files scanned : {len(records)}")
    lines.append(f"Complete      : {complete}")
    lines.append(f"Errors        : {errors}")
    incomplete = [r for r in records if not r.error and not r.is_complete]
    if incomplete:
        lines.append("\nIncomplete files:")
        for r in incomplete:
            missing = ", ".join(r.missing_fields)
            lines.append(f"  {r.path}  missing: {missing}")
    return "\n".join(lines)
