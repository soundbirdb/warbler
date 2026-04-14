"""Tests for warbler.pipeline — batch fingerprint + tag pipeline."""

from __future__ import annotations

import numpy as np
import pytest
from unittest.mock import patch, MagicMock

from warbler.pipeline import (
    process_file,
    process_batch,
    BatchReport,
    ProcessingResult,
)

FAKE_FP = "b" * 64
FAKE_MEL = np.zeros((128, 100), dtype=np.float32)


# ---------------------------------------------------------------------------
# process_file
# ---------------------------------------------------------------------------

class TestProcessFile:
    def test_writes_fingerprint_and_returns_result(self):
        with patch("warbler.pipeline.read_fingerprint", return_value=None), \
             patch("warbler.pipeline.compute_spectral_fingerprint", return_value=FAKE_FP), \
             patch("warbler.pipeline.write_fingerprint") as mock_write:

            result = process_file("song.mp3", FAKE_MEL)

        assert result.fingerprint == FAKE_FP
        assert result.error is None
        assert result.skipped is False
        mock_write.assert_called_once_with("song.mp3", FAKE_FP)

    def test_skips_when_fingerprint_already_present(self):
        with patch("warbler.pipeline.read_fingerprint", return_value=FAKE_FP), \
             patch("warbler.pipeline.write_fingerprint") as mock_write:

            result = process_file("song.mp3", FAKE_MEL, force=False)

        assert result.skipped is True
        assert result.fingerprint == FAKE_FP
        mock_write.assert_not_called()

    def test_force_overwrites_existing_fingerprint(self):
        with patch("warbler.pipeline.read_fingerprint", return_value=FAKE_FP), \
             patch("warbler.pipeline.compute_spectral_fingerprint", return_value=FAKE_FP), \
             patch("warbler.pipeline.write_fingerprint") as mock_write:

            result = process_file("song.mp3", FAKE_MEL, force=True)

        assert result.skipped is False
        mock_write.assert_called_once()

    def test_returns_error_result_on_exception(self):
        with patch("warbler.pipeline.read_fingerprint", side_effect=ValueError("bad file")):
            result = process_file("broken.mp3", FAKE_MEL)

        assert result.error == "bad file"
        assert result.fingerprint == ""


# ---------------------------------------------------------------------------
# process_batch
# ---------------------------------------------------------------------------

class TestProcessBatch:
    def _make_items(self, n: int = 3):
        return [(f"track_{i}.mp3", FAKE_MEL) for i in range(n)]

    def test_returns_batch_report_with_correct_length(self):
        items = self._make_items(3)
        with patch("warbler.pipeline.read_fingerprint", return_value=None), \
             patch("warbler.pipeline.compute_spectral_fingerprint", return_value=FAKE_FP), \
             patch("warbler.pipeline.write_fingerprint"):

            report = process_batch(items)

        assert isinstance(report, BatchReport)
        assert len(report.results) == 3

    def test_success_and_error_counts(self):
        items = self._make_items(2)

        def fake_read(path):
            return None

        def fake_compute(mel):
            if "track_1" in str(mel):  # won't match — triggers normal flow
                raise RuntimeError("oops")
            return FAKE_FP

        side_effects = [None, Exception("boom")]

        with patch("warbler.pipeline.read_fingerprint", return_value=None), \
             patch("warbler.pipeline.compute_spectral_fingerprint",
                   side_effect=[FAKE_FP, Exception("boom")]), \
             patch("warbler.pipeline.write_fingerprint"):

            report = process_batch(items)

        assert report.success_count == 1
        assert report.error_count == 1

    def test_skipped_count(self):
        items = self._make_items(4)
        with patch("warbler.pipeline.read_fingerprint", return_value=FAKE_FP):
            report = process_batch(items, force=False)

        assert report.skipped_count == 4
        assert report.success_count == 4  # skipped files still count as no error
