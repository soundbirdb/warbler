"""CLI sub-commands for exporting fingerprint data."""

from __future__ import annotations

import argparse
from pathlib import Path

from warbler.cli import _collect_audio_files
from warbler.exporter import export


def add_export_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the *export* sub-command on an existing subparsers group."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "export",
        help="Export fingerprint tags to JSON or CSV.",
    )
    parser.add_argument(
        "directory",
        type=Path,
        help="Root directory containing audio files.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("fingerprints.json"),
        metavar="FILE",
        help="Destination file (default: fingerprints.json).",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "csv"],
        default="json",
        dest="fmt",
        help="Output format (default: json).",
    )
    parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        default=False,
        help="Recurse into sub-directories.",
    )
    parser.set_defaults(func=_run_export)


def _run_export(args: argparse.Namespace) -> int:
    """Execute the export command; returns an exit code."""
    audio_files = _collect_audio_files(args.directory, recursive=args.recursive)
    if not audio_files:
        print("No audio files found.")
        return 0

    count = export(audio_files, args.output, fmt=args.fmt)
    print(f"Exported {count} fingerprint(s) to {args.output} [{args.fmt}]")
    return 0
