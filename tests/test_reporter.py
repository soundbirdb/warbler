"""Tests for warbler.reporter."""

from __future__ import annotations

import io
import json
import csv
from pathlib import Path

import pytest

from warbler.pipeline import BatchReport, ProcessingResult
from warbler.reporter import format_summary, write_json_report, write_csv_report


def _make_report():
    results = [
        ProcessingResult(path=Path("a.mp3"), status="success", fingerprint="abc123"),
        ProcessingResult(path=Path("b.flac"), status="skipped", fingerprint="def456"),
        ProcessingResult(
            path=Path("c.mp3"),
            status="error",
            fingerprint=None,
            error=ValueError("boom"),
        ),
    ]
    return BatchReport(results=results)


class TestFormatSummary:
    def test_contains_counts(self):
        report = _make_report()
        summary = format_summary(report)
        assert "Processed : 1" in summary
        assert "Skipped   : 1" in summary
        assert "Errors    : 1" in summary
        assert "Total     : 3" in summary

    def test_lists_failed_files_when_errors_present(self):
        report = _make_report()
        summary = format_summary(report)
        assert "c.mp3" in summary
        assert "boom" in summary

    def test_no_failed_section_when_no_errors(self):
        results = [
            ProcessingResult(path=Path("a.mp3"), status="success", fingerprint="abc"),
        ]
        report = BatchReport(results=results)
        summary = format_summary(report)
        assert "Failed files" not in summary


class TestWriteJsonReport:
    def test_json_structure(self):
        report = _make_report()
        buf = io.StringIO()
        write_json_report(report, buf)
        buf.seek(0)
        data = json.load(buf)
        assert data["summary"]["total"] == 3
        assert data["summary"]["errors"] == 1
        assert len(data["results"]) == 3

    def test_writes_to_path(self, tmp_path):
        report = _make_report()
        out = tmp_path / "report.json"
        write_json_report(report, out)
        data = json.loads(out.read_text())
        assert data["summary"]["processed"] == 1

    def test_error_field_is_string_or_none(self):
        report = _make_report()
        buf = io.StringIO()
        write_json_report(report, buf)
        buf.seek(0)
        results = json.load(buf)["results"]
        statuses = {r["status"]: r["error"] for r in results}
        assert statuses["error"] == "boom"
        assert statuses["success"] is None


class TestWriteCsvReport:
    def test_csv_has_header_and_rows(self):
        report = _make_report()
        buf = io.StringIO()
        write_csv_report(report, buf)
        buf.seek(0)
        reader = list(csv.DictReader(buf))
        assert len(reader) == 3
        assert "path" in reader[0]
        assert "status" in reader[0]

    def test_writes_to_path(self, tmp_path):
        report = _make_report()
        out = tmp_path / "report.csv"
        write_csv_report(report, out)
        lines = out.read_text().splitlines()
        assert lines[0].startswith("path")
        assert len(lines) == 4  # header + 3 rows
