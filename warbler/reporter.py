"""Reporting utilities for batch processing results."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import TextIO

from warbler.pipeline import BatchReport


def _result_to_dict(result) -> dict:
    return {
        "path": str(result.path),
        "status": result.status,
        "fingerprint": result.fingerprint,
        "error": str(result.error) if result.error else None,
    }


def format_summary(report: BatchReport) -> str:
    """Return a human-readable summary string for a BatchReport."""
    lines = [
        f"Processed : {report.success_count}",
        f"Skipped   : {report.skipped_count}",
        f"Errors    : {report.error_count}",
        f"Total     : {len(report.results)}",
    ]
    if report.error_count:
        lines.append("\nFailed files:")
        for r in report.results:
            if r.status == "error":
                lines.append(f"  {r.path}: {r.error}")
    return "\n".join(lines)


def write_json_report(report: BatchReport, dest: Path | TextIO) -> None:
    """Serialise a BatchReport to JSON, writing to a file path or file-like object."""
    payload = {
        "summary": {
            "processed": report.success_count,
            "skipped": report.skipped_count,
            "errors": report.error_count,
            "total": len(report.results),
        },
        "results": [_result_to_dict(r) for r in report.results],
    }
    if isinstance(dest, (str, Path)):
        with open(dest, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
    else:
        json.dump(payload, dest, indent=2)


def write_csv_report(report: BatchReport, dest: Path | TextIO) -> None:
    """Serialise a BatchReport to CSV, writing to a file path or file-like object."""
    import csv

    fieldnames = ["path", "status", "fingerprint", "error"]
    rows = [_result_to_dict(r) for r in report.results]

    if isinstance(dest, (str, Path)):
        with open(dest, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    else:
        writer = csv.DictWriter(dest, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
