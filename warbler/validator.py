"""Audio file validation: checks file integrity and metadata before processing."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

SUPPORTED_EXTENSIONS = {".mp3", ".flac", ".ogg", ".wav", ".m4a"}
MIN_FILE_SIZE_BYTES = 128
MAX_FILE_SIZE_MB = 500


@dataclass
class ValidationResult:
    path: Path
    valid: bool
    errors: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.valid


@dataclass
class ValidationReport:
    results: List[ValidationResult] = field(default_factory=list)

    @property
    def valid_count(self) -> int:
        return sum(1 for r in self.results if r.valid)

    @property
    def invalid_count(self) -> int:
        return sum(1 for r in self.results if not r.valid)

    @property
    def invalid_paths(self) -> List[Path]:
        return [r.path for r in self.results if not r.valid]


def validate_file(path: Path, max_size_mb: Optional[float] = None) -> ValidationResult:
    errors: List[str] = []
    max_bytes = (max_size_mb or MAX_FILE_SIZE_MB) * 1024 * 1024

    if not path.exists():
        errors.append("file does not exist")
        return ValidationResult(path=path, valid=False, errors=errors)

    if not path.is_file():
        errors.append("path is not a file")
        return ValidationResult(path=path, valid=False, errors=errors)

    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        errors.append(f"unsupported extension: {ext!r}")

    size = os.path.getsize(path)
    if size < MIN_FILE_SIZE_BYTES:
        errors.append(f"file too small: {size} bytes")
    if size > max_bytes:
        errors.append(f"file too large: {size / (1024*1024):.1f} MB")

    return ValidationResult(path=path, valid=len(errors) == 0, errors=errors)


def validate_batch(paths: List[Path], max_size_mb: Optional[float] = None) -> ValidationReport:
    return ValidationReport(results=[validate_file(p, max_size_mb) for p in paths])
