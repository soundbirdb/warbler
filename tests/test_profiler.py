"""Tests for warbler.profiler."""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from warbler.profiler import FileProfile, ProfileReport, Profiler


P1 = Path("a/b/track01.mp3")
P2 = Path("a/b/track02.flac")


def _make_report(*durations_ms: float) -> ProfileReport:
    profiles = [
        FileProfile(path=Path(f"file{i}.mp3"), duration_ms=d)
        for i, d in enumerate(durations_ms)
    ]
    return ProfileReport(profiles=profiles)


class TestProfileReport:
    def test_total_ms_sums_durations(self):
        r = _make_report(10.0, 20.0, 30.0)
        assert r.total_ms == pytest.approx(60.0)

    def test_average_ms(self):
        r = _make_report(10.0, 30.0)
        assert r.average_ms == pytest.approx(20.0)

    def test_average_ms_none_when_empty(self):
        assert ProfileReport().average_ms is None

    def test_slowest_returns_max(self):
        r = _make_report(5.0, 50.0, 15.0)
        assert r.slowest is not None
        assert r.slowest.duration_ms == pytest.approx(50.0)

    def test_fastest_returns_min(self):
        r = _make_report(5.0, 50.0, 15.0)
        assert r.fastest is not None
        assert r.fastest.duration_ms == pytest.approx(5.0)

    def test_slowest_none_when_empty(self):
        assert ProfileReport().slowest is None


class TestProfiler:
    def test_records_profile_after_end(self):
        p = Profiler()
        p.begin(P1)
        time.sleep(0.01)
        profile = p.end()
        assert profile.path == P1
        assert profile.duration_ms > 0

    def test_report_accumulates_entries(self):
        p = Profiler()
        for path in (P1, P2):
            p.begin(path)
            p.end()
        assert len(p.report.profiles) == 2

    def test_end_without_begin_raises(self):
        p = Profiler()
        with pytest.raises(RuntimeError, match="begin"):
            p.end()

    def test_sequential_begin_end_pairs(self):
        p = Profiler()
        p.begin(P1)
        r1 = p.end()
        p.begin(P2)
        r2 = p.end()
        assert r1.path == P1
        assert r2.path == P2
