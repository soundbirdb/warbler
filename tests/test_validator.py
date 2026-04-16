"""Tests for warbler.validator."""
from __future__ import annotations

from pathlib import Path

import pytest

from warbler.validator import (
    ValidationResult,
    ValidationReport,
    validate_file,
    validate_batch,
    MIN_FILE_SIZE_BYTES,
)


def _write(tmp_path: Path, name: str, size: int = 1024) -> Path:
    p = tmp_path / name
    p.write_bytes(b"x" * size)
    return p


class TestValidateFile:
    def test_valid_mp3(self, tmp_path):
        p = _write(tmp_path, "track.mp3")
        result = validate_file(p)
        assert result.valid
        assert result.errors == []

    def test_valid_flac(self, tmp_path):
        p = _write(tmp_path, "track.flac")
        assert validate_file(p).valid

    def test_unsupported_extension(self, tmp_path):
        p = _write(tmp_path, "track.avi")
        result = validate_file(p)
        assert not result.valid
        assert any("unsupported" in e for e in result.errors)

    def test_file_too_small(self, tmp_path):
        p = _write(tmp_path, "tiny.mp3", size=MIN_FILE_SIZE_BYTES - 1)
        result = validate_file(p)
        assert not result.valid
        assert any("too small" in e for e in result.errors)

    def test_file_too_large(self, tmp_path):
        p = _write(tmp_path, "big.mp3", size=1024)
        result = validate_file(p, max_size_mb=0.0001)
        assert not result.valid
        assert any("too large" in e for e in result.errors)

    def test_missing_file(self, tmp_path):
        p = tmp_path / "ghost.mp3"
        result = validate_file(p)
        assert not result.valid
        assert any("does not exist" in e for e in result.errors)

    def test_bool_true_when_valid(self, tmp_path):
        p = _write(tmp_path, "ok.mp3")
        assert bool(validate_file(p)) is True

    def test_bool_false_when_invalid(self, tmp_path):
        p = tmp_path / "missing.mp3"
        assert bool(validate_file(p)) is False


class TestValidateBatch:
    def test_counts_valid_and_invalid(self, tmp_path):
        good = _write(tmp_path, "a.mp3")
        bad = tmp_path / "b.mp3"
        report = validate_batch([good, bad])
        assert report.valid_count == 1
        assert report.invalid_count == 1

    def test_invalid_paths_list(self, tmp_path):
        bad = tmp_path / "missing.flac"
        report = validate_batch([bad])
        assert bad in report.invalid_paths

    def test_empty_batch(self):
        report = validate_batch([])
        assert report.valid_count == 0
        assert report.invalid_count == 0
