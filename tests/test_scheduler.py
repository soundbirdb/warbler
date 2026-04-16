"""Tests for warbler.scheduler."""
from __future__ import annotations

import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from warbler.pipeline import BatchReport, ProcessingResult
from warbler.scheduler import BatchScheduler, SchedulerConfig


def _make_config(tmp_path: Path, **kwargs) -> SchedulerConfig:
    return SchedulerConfig(directory=tmp_path, interval_seconds=0.05, **kwargs)


def _fake_report() -> BatchReport:
    return BatchReport(results=[])


class TestBatchScheduler:
    def test_starts_and_stops(self, tmp_path):
        cfg = _make_config(tmp_path)
        with patch("warbler.scheduler._collect_audio_files", return_value=[]), \
             patch("warbler.scheduler.process_file"):
            s = BatchScheduler(cfg)
            s.start()
            assert s.is_running()
            s.stop()
            assert not s.is_running()

    def test_raises_if_started_twice(self, tmp_path):
        cfg = _make_config(tmp_path)
        with patch("warbler.scheduler._collect_audio_files", return_value=[]), \
             patch("warbler.scheduler.process_file"):
            s = BatchScheduler(cfg)
            s.start()
            try:
                with pytest.raises(RuntimeError, match="already running"):
                    s.start()
            finally:
                s.stop()

    def test_calls_on_report_callback(self, tmp_path):
        reports = []
        cfg = _make_config(tmp_path, on_report=reports.append)
        with patch("warbler.scheduler._collect_audio_files", return_value=[]), \
             patch("warbler.scheduler.process_file"):
            s = BatchScheduler(cfg)
            s.start()
            time.sleep(0.15)
            s.stop()
        assert len(reports) >= 1
        assert all(isinstance(r, BatchReport) for r in reports)

    def test_passes_force_to_process_file(self, tmp_path):
        fake_file = tmp_path / "a.mp3"
        fake_file.touch()
        cfg = _make_config(tmp_path, force=True)
        mock_process = MagicMock(return_value=ProcessingResult(path=fake_file, status="success"))
        with patch("warbler.scheduler._collect_audio_files", return_value=[fake_file]), \
             patch("warbler.scheduler.process_file", mock_process):
            s = BatchScheduler(cfg)
            s._run_once()
        mock_process.assert_called_once_with(fake_file, force=True)

    def test_run_once_returns_batch_report(self, tmp_path):
        cfg = _make_config(tmp_path)
        with patch("warbler.scheduler._collect_audio_files", return_value=[]), \
             patch("warbler.scheduler.process_file"):
            s = BatchScheduler(cfg)
            report = s._run_once()
        assert isinstance(report, BatchReport)
