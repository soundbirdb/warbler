"""Tests for warbler.scorer."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from warbler.metadata import FileMetadata
from warbler.scorer import FileScore, ScoreReport, batch_score, score_file


_FULL_META = FileMetadata(
    path=Path("a.mp3"),
    title="Song",
    artist="Artist",
    album="Album",
    year="2024",
    genre="Jazz",
)

_EMPTY_META = FileMetadata(
    path=Path("a.mp3"),
    title=None,
    artist=None,
    album=None,
    year=None,
    genre=None,
)


def _patch(fp, meta):
    return (
        patch("warbler.scorer.read_fingerprint", return_value=fp),
        patch("warbler.scorer.read_metadata", return_value=meta),
    )


class TestScoreFile:
    def test_perfect_score_when_all_present(self):
        with patch("warbler.scorer.read_fingerprint", return_value="abc"), \
             patch("warbler.scorer.read_metadata", return_value=_FULL_META):
            result = score_file(Path("a.mp3"))
        assert result.score == 1.0
        assert result.reasons == []

    def test_zero_score_when_nothing_present(self):
        with patch("warbler.scorer.read_fingerprint", return_value=None), \
             patch("warbler.scorer.read_metadata", return_value=_EMPTY_META):
            result = score_file(Path("a.mp3"))
        assert result.score == 0.0
        assert "missing fingerprint" in result.reasons

    def test_partial_score_missing_fingerprint(self):
        with patch("warbler.scorer.read_fingerprint", return_value=None), \
             patch("warbler.scorer.read_metadata", return_value=_FULL_META):
            result = score_file(Path("a.mp3"))
        assert 0.0 < result.score < 1.0
        assert "missing fingerprint" in result.reasons

    def test_partial_score_missing_metadata_fields(self):
        with patch("warbler.scorer.read_fingerprint", return_value="fp"), \
             patch("warbler.scorer.read_metadata", return_value=_EMPTY_META):
            result = score_file(Path("a.mp3"))
        assert 0.0 < result.score < 1.0
        assert any("missing field" in r for r in result.reasons)

    def test_is_tagged_true_when_fingerprint_present(self):
        with patch("warbler.scorer.read_fingerprint", return_value="fp"), \
             patch("warbler.scorer.read_metadata", return_value=_FULL_META):
            result = score_file(Path("a.mp3"))
        assert result.is_tagged is True

    def test_is_tagged_false_when_no_fingerprint(self):
        with patch("warbler.scorer.read_fingerprint", return_value=None), \
             patch("warbler.scorer.read_metadata", return_value=_FULL_META):
            result = score_file(Path("a.mp3"))
        assert result.is_tagged is False

    def test_exception_in_read_fingerprint_treated_as_missing(self):
        with patch("warbler.scorer.read_fingerprint", side_effect=Exception("boom")), \
             patch("warbler.scorer.read_metadata", return_value=_FULL_META):
            result = score_file(Path("a.mp3"))
        assert result.fingerprint is None


class TestScoreReport:
    def _report(self, scores):
        entries = [
            FileScore(path=Path(f"{i}.mp3"), fingerprint=None, metadata=None, score=s)
            for i, s in enumerate(scores)
        ]
        return ScoreReport(entries=entries)

    def test_average_score_none_when_empty(self):
        assert ScoreReport().average_score is None

    def test_average_score_correct(self):
        report = self._report([0.0, 0.5, 1.0])
        assert abs(report.average_score - 0.5) < 1e-9

    def test_fully_scored_filters_correctly(self):
        report = self._report([0.5, 1.0, 1.0])
        assert len(report.fully_scored) == 2

    def test_unscored_filters_correctly(self):
        report = self._report([0.0, 0.5, 0.0])
        assert len(report.unscored) == 2


def test_batch_score_returns_one_entry_per_path():
    paths = [Path("a.mp3"), Path("b.mp3")]
    with patch("warbler.scorer.read_fingerprint", return_value=None), \
         patch("warbler.scorer.read_metadata", return_value=_EMPTY_META):
        report = batch_score(paths)
    assert len(report.entries) == 2
