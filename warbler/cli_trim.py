"""CLI subcommand for silence-trimming audio files."""
from __future__ import annotations

import argparse
from pathlib import Path

from warbler.cli import _collect_audio_files
from warbler.trimmer import batch_trim


def add_trim_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    parser = subparsers.add_parser(
        "trim",
        help="Remove leading/trailing silence from audio files.",
    )
    parser.add_argument("directory", type=Path, help="Directory containing audio files.")
    parser.add_argument(
        "--output-dir", type=Path, default=None,
        help="Directory for trimmed files. Defaults to alongside originals.",
    )
    parser.add_argument(
        "--threshold", type=float, default=-50.0,
        help="Silence threshold in dBFS (default: -50.0).",
    )
    parser.add_argument(
        "--duration", type=float, default=0.5,
        help="Minimum silence duration in seconds (default: 0.5).",
    )
    parser.add_argument(
        "--recursive", action="store_true", default=False,
        help="Recurse into subdirectories.",
    )
    parser.add_argument(
        "--dry-run", action="store_true", default=False,
        help="Show what would be trimmed without modifying files.",
    )
    parser.set_defaults(func=_run_trim)


def _run_trim(args: argparse.Namespace) -> None:
    paths = _collect_audio_files(args.directory, recursive=args.recursive)

    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)

    report = batch_trim(
        paths,
        output_dir=args.output_dir,
        silence_threshold=args.threshold,
        silence_duration=args.duration,
        dry_run=args.dry_run,
    )

    mode = "[dry-run] " if args.dry_run else ""
    for result in report.results:
        if result.success:
            print(f"{mode}trimmed: {result.path} -> {result.output_path}")
        else:
            print(f"error:   {result.path}: {result.error}")

    print(
        f"\nDone. trimmed={report.trimmed_count} "
        f"errors={report.error_count}"
    )
