"""Integration test: scheduler runs pipeline end-to-end."""
from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import patch

from warbler.pipeline import BatchReport, ProcessingResult
from warbler.scheduler import BatchScheduler, SchedulerConfig


def _make_result(path: Path, status: str = "success") -> ProcessingResult:
    return ProcessingResult(path=path, status=status)


class TestSchedulerIntegration:
    def test_scheduler_accumulates_reports_over_multiple_runs(self, tmp_path):
        fake_file = tmp_path / "song.mp3"
        fake_file.touch()
        reports = []

        cfg = SchedulerConfig(
            directory=tmp_path,
            interval_seconds=0.05,
            recursive=False,
            on_report=reports.append,
        )

        with patch("warbler.scheduler._collect_audio_files", return_value=[fake_file]), \
             patch("warbler.scheduler.process_file",
                   return_value=_make_result(fake_file)):
            s = BatchScheduler(cfg)
            s.start()
            time.sleep(0.22)
            s.stop()

        assert len(reports) >= 2
        for r in reports:
            assert isinstance(r, BatchReport)
            assert r.success_count == 1

    def test_scheduler_report_reflects_errors(self, tmp_path):
        fake_file = tmp_path / "bad.mp3"
        fake_file.touch()
        reports = []

        cfg = SchedulerConfig(
            directory=tmp_path,
            interval_seconds=0.05,
            on_report=reports.append,
        )

        err_result = _make_result(fake_file, status="error")
        with patch("warbler.scheduler._collect_audio_files", return_value=[fake_file]), \
             patch("warbler.scheduler.process_file", return_value=err_result):
            s = BatchScheduler(cfg)
            s.start()
            time.sleep(0.12)
            s.stop()

        assert any(r.error_count >= 1 for r in reports)
