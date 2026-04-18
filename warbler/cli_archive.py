"""CLI subcommand: warbler archive."""
from __future__ import annotations

import argparse
from pathlib import Path

from warbler.archiver import batch_archive
from warbler.cli import _collect_audio_files


def add_archive_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    parser = subparsers.add_parser(
        "archive",
        help="Move or copy audio files into an organised archive directory.",
    )
    parser.add_argument("input", type=Path, help="Source directory of audio files.")
    parser.add_argument("output", type=Path, help="Root of the archive directory.")
    parser.add_argument("-r", "--recursive", action="store_true", default=False)
    parser.add_argument(
        "--copy",
        action="store_true",
        default=False,
        help="Copy files instead of moving them.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite existing files in the archive.",
    )
    parser.set_defaults(func=_run_archive)


def _run_archive(args: argparse.Namespace) -> None:
    files = _collect_audio_files(args.input, recursive=args.recursive)
    if not files:
        print("No audio files found.")
        return

    report = batch_archive(
        files,
        args.output,
        copy=args.copy,
        overwrite=args.overwrite,
    )

    print(f"Archived : {report.moved_count}")
    print(f"Skipped  : {report.skipped_count}")
    print(f"Errors   : {report.error_count}")

    if report.error_count:
        print("\nFailed files:")
        for r in report.results:
            if r.error:
                print(f"  {r.source}: {r.error}")
