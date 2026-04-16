"""CLI subcommand: normalize audio filenames in a directory."""
from __future__ import annotations

import argparse
from pathlib import Path

from warbler.normalizer import apply_normalization, normalize_filename

_SUPPORTED = {".mp3", ".flac", ".ogg", ".wav", ".m4a"}


def add_normalize_subcommand(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "normalize",
        help="Normalize audio filenames (lowercase, underscore-separated).",
    )
    parser.add_argument("directory", type=Path, help="Directory to scan.")
    parser.add_argument(
        "--recursive", "-r", action="store_true", help="Recurse into subdirectories."
    )
    parser.add_argument(
        "--dry-run", "-n", action="store_true", help="Preview changes without renaming."
    )
    parser.set_defaults(func=_run_normalize)


def _collect(directory: Path, recursive: bool) -> list[Path]:
    pattern = "**/*" if recursive else "*"
    return [
        p for p in directory.glob(pattern)
        if p.is_file() and p.suffix.lower() in _SUPPORTED
    ]


def _run_normalize(args: argparse.Namespace) -> None:
    files = _collect(args.directory, args.recursive)
    renamed = skipped = errors = 0

    for path in files:
        result = normalize_filename(path)
        if result.error:
            print(f"  ERROR  {path.name}: {result.error}")
            errors += 1
            continue
        if not result.renamed:
            skipped += 1
            continue
        apply_normalization(result, dry_run=args.dry_run)
        tag = "[dry-run] " if args.dry_run else ""
        print(f"  {tag}{result.original.name} -> {result.normalized.name}")
        renamed += 1

    print(f"\nDone. renamed={renamed} skipped={skipped} errors={errors}")
