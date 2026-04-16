"""Tests for warbler.similarity."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from warbler.similarity import SimilarityMatch, _hamming, find_similar

FP_A = "a" * 64  # 64 hex chars = 32 bytes
FP_B = "b" * 64
FP_CLOSE = "a" * 62 + "ab"  # one nibble different


class TestHamming:
    def test_identical_strings_zero_distance(self):
        assert _hamming(FP_A, FP_A) == 0

    def test_different_strings_nonzero(self):
        assert _hamming(FP_A, FP_B) > 0

    def test_raises_on_length_mismatch(self):
        with pytest.raises(ValueError):
            _hamming(FP_A, "aa")


class TestSimilarityMatch:
    def test_score_one_for_zero_distance(self):
        m = SimilarityMatch(path=Path("f.mp3"), fingerprint=FP_A, distance=0)
        assert m.score == pytest.approx(1.0)

    def test_score_zero_for_max_distance(self):
        m = SimilarityMatch(path=Path("f.mp3"), fingerprint=FP_A, distance=256)
        assert m.score == pytest.approx(0.0)


class TestFindSimilar:
    def _records(self):
        return [
            {"path": "/music/a.mp3", "fingerprint": FP_A},
            {"path": "/music/b.mp3", "fingerprint": FP_B},
            {"path": "/music/c.mp3", "fingerprint": ""},
        ]

    @patch("warbler.similarity.collect_fingerprint_records")
    def test_returns_exact_match(self, mock_collect):
        mock_collect.return_value = self._records()
        results = find_similar(FP_A, [Path("/music")], threshold=1.0)
        assert len(results) == 1
        assert results[0].path == Path("/music/a.mp3")

    @patch("warbler.similarity.collect_fingerprint_records")
    def test_threshold_filters_distant_matches(self, mock_collect):
        mock_collect.return_value = self._records()
        results = find_similar(FP_A, [Path("/music")], threshold=0.0)
        assert len(results) == 2  # empty fingerprint skipped

    @patch("warbler.similarity.collect_fingerprint_records")
    def test_results_sorted_by_distance(self, mock_collect):
        mock_collect.return_value = self._records()
        results = find_similar(FP_A, [Path("/music")], threshold=0.0)
        distances = [r.distance for r in results]
        assert distances == sorted(distances)

    @patch("warbler.similarity.collect_fingerprint_records")
    def test_skips_records_without_fingerprint(self, mock_collect):
        mock_collect.return_value = [{"path": "/music/x.mp3", "fingerprint": ""}]
        results = find_similar(FP_A, [Path("/music")], threshold=0.0)
        assert results == []
