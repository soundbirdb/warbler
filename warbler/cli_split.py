"""CLI subcommand for splitting audio files into segments."""

from __future__ import annotations

import argparse
from pathlib import Path

from warbler.cli import _collect_audio_files
from warbler.splitter import SplitReport, batch_split


def add_split_subcommand(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "split",
        help="Split audio files into fixed-duration segments.",
    )
    parser.add_argument("directory", type=Path, help="Directory containing audio files.")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Root output directory (default: <directory>/splits).",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=30,
        metavar="SECONDS",
        help="Segment duration in seconds (default: 30).",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        default=False,
        help="Recurse into subdirectories.",
    )
    parser.set_defaults(func=_run_split)


def _run_split(args: argparse.Namespace) -> None:
    directory: Path = args.directory
    output_root: Path = args.output or directory / "splits"
    duration: int = args.duration
    recursive: bool = args.recursive

    sources = _collect_audio_files(directory, recursive=recursive)
    if not sources:
        print("No audio files found.")
        return

    report: SplitReport = batch_split(sources, output_root, segment_duration=duration)

    for result in report.results:
        if result.success:
            print(f"[OK]    {result.source.name}  ({result.segment_count} segments)")
        else:
            print(f"[ERROR] {result.source.name}  {result.error}")

    print(
        f"\nDone. {report.success_count} split, "
        f"{report.error_count} errors, "
        f"{report.total_segments} total segments."
    )
