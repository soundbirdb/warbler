"""Command-line interface for warbler."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from warbler.pipeline import process_file, BatchReport
from warbler.reporter import format_summary, write_json_report, write_csv_report

SUPPORTED_EXTENSIONS = {".mp3", ".flac", ".ogg", ".m4a"}


def _collect_audio_files(root: Path) -> list[Path]:
    """Recursively collect audio files under *root*."""
    return [
        p
        for p in sorted(root.rglob("*"))
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    ]


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="warbler",
        description="Batch-process and fingerprint audio files.",
    )
    parser.add_argument("directory", type=Path, help="Root directory to scan.")
    parser.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Overwrite existing fingerprints.",
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        metavar="FILE",
        help="Write a JSON report to FILE.",
    )
    parser.add_argument(
        "--report-csv",
        type=Path,
        metavar="FILE",
        help="Write a CSV report to FILE.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        default=False,
        help="Suppress per-file output.",
    )

    args = parser.parse_args(argv)

    if not args.directory.is_dir():
        print(f"error: {args.directory} is not a directory", file=sys.stderr)
        return 2

    files = _collect_audio_files(args.directory)
    if not files:
        print("No supported audio files found.")
        return 0

    results = []
    for path in files:
        result = process_file(path, force=args.force)
        results.append(result)
        if not args.quiet:
            print(f"[{result.status:8s}] {result.path}")

    report = BatchReport(results=results)
    print()
    print(format_summary(report))

    if args.report_json:
        write_json_report(report, args.report_json)
        print(f"JSON report written to {args.report_json}")

    if args.report_csv:
        write_csv_report(report, args.report_csv)
        print(f"CSV report written to {args.report_csv}")

    return 1 if report.error_count else 0


def main() -> None:  # pragma: no cover
    sys.exit(run())
