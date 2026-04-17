"""CLI subcommand: rename audio files using fingerprint metadata."""
from __future__ import annotations

import argparse
from pathlib import Path

from warbler.cli import _collect_audio_files
from warbler.renamer import batch_rename


def add_rename_subcommand(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "rename",
        help="Rename audio files by appending their spectral fingerprint.",
    )
    parser.add_argument("directory", type=Path, help="Directory of audio files.")
    parser.add_argument(
        "--template",
        default="{stem}_{fingerprint}",
        help="Filename template. Available vars: {stem}, {fingerprint}.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Preview renames without applying them.",
    )
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        default=False,
        help="Recurse into subdirectories.",
    )
    parser.set_defaults(func=_run_rename)


def _run_rename(args: argparse.Namespace) -> None:
    paths = _collect_audio_files(args.directory, recursive=args.recursive)
    report = batch_rename(paths, template=args.template, dry_run=args.dry_run)

    mode = "[DRY RUN] " if args.dry_run else ""
    for result in report.results:
        if result.error:
            print(f"  ERROR   {result.source}: {result.error}")
        elif result.renamed:
            print(f"  {mode}RENAMED {result.source} -> {result.destination}")
        else:
            print(f"  SKIPPED {result.source}")

    print(
        f"\nDone. renamed={report.renamed_count} "
        f"skipped={report.skipped_count} "
        f"errors={report.error_count}"
    )
