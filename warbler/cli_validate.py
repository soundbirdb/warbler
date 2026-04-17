"""CLI subcommand for batch-validating audio file fingerprint tags."""

from __future__ import annotations

import argparse
from pathlib import Path

from warbler.cli import _collect_audio_files
from warbler.validator import ValidationReport, validate_file


def add_validate_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the *validate* subcommand on *subparsers*."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "validate",
        help="Check that audio files carry a valid spectral-fingerprint tag.",
    )
    parser.add_argument(
        "directory",
        type=Path,
        help="Root directory to scan for audio files.",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        default=False,
        help="Recurse into subdirectories (default: False).",
    )
    parser.add_argument(
        "--json",
        dest="json_report",
        metavar="FILE",
        type=Path,
        default=None,
        help="Write a JSON report to FILE.",
    )
    parser.add_argument(
        "--csv",
        dest="csv_report",
        metavar="FILE",
        type=Path,
        default=None,
        help="Write a CSV report to FILE.",
    )
    parser.set_defaults(func=_run_validate)


def _run_validate(args: argparse.Namespace) -> None:
    """Execute the validate subcommand."""
    paths = _collect_audio_files(args.directory, recursive=args.recursive)

    if not paths:
        print("No supported audio files found.")
        return

    results = [validate_file(p) for p in paths]
    report = ValidationReport(results=results)

    valid = report.valid_count
    invalid = report.invalid_count
    total = valid + invalid

    print(f"Validated {total} file(s): {valid} valid, {invalid} invalid.")

    if invalid:
        print("\nInvalid files:")
        for result in report.results:
            if not result:
                print(f"  {result.path}: {result.reason}")

    if args.json_report is not None:
        import json

        payload = [
            {
                "path": str(r.path),
                "valid": bool(r),
                "reason": r.reason,
            }
            for r in report.results
        ]
        args.json_report.write_text(json.dumps(payload, indent=2))
        print(f"\nJSON report written to {args.json_report}")

    if args.csv_report is not None:
        import csv

        with args.csv_report.open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=["path", "valid", "reason"])
            writer.writeheader()
            for r in report.results:
                writer.writerow(
                    {"path": str(r.path), "valid": bool(r), "reason": r.reason or ""}
                )
        print(f"CSV report written to {args.csv_report}")
