"""Tests for warbler.comparator."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import pytest

from warbler.comparator import (
    ComparisonReport,
    ComparisonResult,
    batch_compare,
    compare_file,
)

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

FP_A = "a" * 64
FP_B = "b" * 64
FP_NEAR_A = "a" * 63 + "b"  # 1 char different — very similar to FP_A


def _make_read(mapping: Dict[Path, str]):
    def _read(path: Path) -> Optional[str]:
        return mapping.get(path)

    return _read


REF = Path("ref.mp3")
FILE_B = Path("b.mp3")
FILE_C = Path("c.mp3")


# ---------------------------------------------------------------------------
# ComparisonResult
# ---------------------------------------------------------------------------


class TestComparisonResult:
    def test_has_matches_false_when_empty(self):
        r = ComparisonResult(reference=REF, reference_fingerprint=FP_A)
        assert r.has_matches is False

    def test_best_match_none_when_empty(self):
        r = ComparisonResult(reference=REF, reference_fingerprint=FP_A)
        assert r.best_match is None


# ---------------------------------------------------------------------------
# compare_file
# ---------------------------------------------------------------------------


class TestCompareFile:
    def test_returns_error_when_reference_has_no_fingerprint(self):
        read = _make_read({})
        result = compare_file(REF, [FILE_B], _read=read)
        assert result.error is not None
        assert "ref.mp3" in result.error

    def test_skips_reference_in_corpus(self):
        read = _make_read({REF: FP_A})
        result = compare_file(REF, [REF], _read=read)
        assert result.error is None
        assert result.matches == []

    def test_finds_similar_file(self):
        read = _make_read({REF: FP_A, FILE_B: FP_NEAR_A})
        result = compare_file(REF, [FILE_B], threshold=0.90, _read=read)
        assert result.has_matches
        assert result.best_match is not None
        assert result.best_match.path == FILE_B

    def test_excludes_dissimilar_file(self):
        read = _make_read({REF: FP_A, FILE_B: FP_B})
        result = compare_file(REF, [FILE_B], threshold=0.90, _read=read)
        assert not result.has_matches

    def test_skips_corpus_files_without_fingerprint(self):
        read = _make_read({REF: FP_A})  # FILE_B has no fingerprint
        result = compare_file(REF, [FILE_B], _read=read)
        assert result.matches == []
        assert result.error is None


# ---------------------------------------------------------------------------
# batch_compare / ComparisonReport
# ---------------------------------------------------------------------------


class TestBatchCompare:
    def test_report_match_count(self):
        read = _make_read({REF: FP_A, FILE_B: FP_NEAR_A, FILE_C: FP_B})
        report = batch_compare([REF], [FILE_B, FILE_C], threshold=0.90, _read=read)
        assert report.match_count == 1

    def test_report_error_count(self):
        read = _make_read({})  # no fingerprints anywhere
        report = batch_compare([REF, FILE_B], [FILE_C], _read=read)
        assert report.error_count == 2

    def test_results_length_matches_references(self):
        read = _make_read({REF: FP_A, FILE_B: FP_B})
        report = batch_compare([REF, FILE_B], [FILE_C], _read=read)
        assert len(report.results) == 2
