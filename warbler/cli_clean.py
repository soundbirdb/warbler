"""CLI subcommand: warbler clean — strip fingerprint tags from audio files."""
from __future__ import annotations

import argparse
from pathlib import Path

from warbler.cleaner import batch_clean
from warbler.cli import _collect_audio_files


def add_clean_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    parser = subparsers.add_parser(
        "clean",
        help="Remove warbler fingerprint tags from audio files.",
    )
    parser.add_argument("directory", type=Path, help="Directory to scan.")
    parser.add_argument("-r", "--recursive", action="store_true", default=False)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Report what would be cleaned without modifying files.",
    )
    parser.set_defaults(func=_run_clean)


def _run_clean(args: argparse.Namespace) -> None:
    files = _collect_audio_files(args.directory, recursive=args.recursive)
    report = batch_clean(files, dry_run=args.dry_run)

    prefix = "[dry-run] " if args.dry_run else ""
    for result in report.results:
        if result.error:
            print(f"  ERROR   {result.path}: {result.error}")
        elif result.cleaned:
            print(f"  {prefix}CLEANED {result.path}")
        else:
            print(f"  SKIP    {result.path} ({result.reason})")

    print(
        f"\nDone. cleaned={report.cleaned_count} "
        f"skipped={report.skipped_count} errors={report.error_count}"
    )
