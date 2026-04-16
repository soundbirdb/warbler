"""Tests for warbler.cli_schedule."""
from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from warbler.cli_schedule import add_schedule_subcommand, _run_schedule


def _make_namespace(**kwargs) -> argparse.Namespace:
    defaults = dict(
        directory=Path("/tmp/music"),
        interval=30.0,
        recursive=True,
        force=False,
        func=_run_schedule,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestAddScheduleSubcommand:
    def _parser(self):
        p = argparse.ArgumentParser()
        sub = p.add_subparsers()
        add_schedule_subcommand(sub)
        return p

    def test_registers_schedule_parser(self):
        p = self._parser()
        ns = p.parse_args(["schedule", "/tmp"])
        assert ns.func is _run_schedule

    def test_default_interval_is_60(self):
        p = self._parser()
        ns = p.parse_args(["schedule", "/tmp"])
        assert ns.interval == 60.0

    def test_custom_interval_accepted(self):
        p = self._parser()
        ns = p.parse_args(["schedule", "/tmp", "--interval", "120"])
        assert ns.interval == 120.0

    def test_force_flag(self):
        p = self._parser()
        ns = p.parse_args(["schedule", "/tmp", "--force"])
        assert ns.force is True

    def test_no_recursive_flag(self):
        p = self._parser()
        ns = p.parse_args(["schedule", "/tmp", "--no-recursive"])
        assert ns.recursive is False


class TestRunSchedule:
    def test_creates_scheduler_with_correct_config(self):
        ns = _make_namespace()
        mock_scheduler = MagicMock()
        with patch("warbler.cli_schedule.BatchScheduler", return_value=mock_scheduler) as MockSched, \
             patch("warbler.cli_schedule.signal"), \
             patch("warbler.cli_schedule.signal.pause"):
            mock_scheduler.start = MagicMock()
            _run_schedule(ns)
            call_cfg = MockSched.call_args[0][0]
            assert call_cfg.interval_seconds == 30.0
            assert call_cfg.recursive is True
            assert call_cfg.force is False

    def test_on_report_prints_summary(self, capsys):
        from warbler.pipeline import BatchReport
        report = BatchReport(results=[])
        with patch("warbler.cli_schedule.format_summary", return_value="SUMMARY") as mock_fmt:
            ns = _make_namespace()
            with patch("warbler.cli_schedule.BatchScheduler") as MockSched, \
                 patch("warbler.cli_schedule.signal"), \
                 patch("warbler.cli_schedule.signal.pause"):
                instance = MockSched.return_value
                _run_schedule(ns)
                on_report = MockSched.call_args[0][0].on_report
                on_report(report)
            captured = capsys.readouterr()
            assert "SUMMARY" in captured.out
