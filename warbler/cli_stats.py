"""CLI sub-command: warbler stats — show tagging statistics for a directory."""
from __future__ import annotations

import argparse
from pathlib import Path

from warbler.cli import _collect_audio_files
from warbler.tagger_stats import collect_stats, format_stats


def add_stats_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    parser = subparsers.add_parser("stats", help="Show tagging statistics")
    parser.add_argument("directory", type=Path, help="Directory to inspect")
    parser.add_argument(
        "-r", "--recursive", action="store_true", default=False,
        help="Recurse into sub-directories",
    )
    parser.add_argument(
        "--json", action="store_true", default=False,
        help="Output raw counts as JSON",
    )
    parser.set_defaults(func=_run_stats)


def _run_stats(args: argparse.Namespace) -> None:
    paths = _collect_audio_files(args.directory, recursive=args.recursive)
    stats = collect_stats(paths)

    if args.json:
        import json
        print(json.dumps({
            "total": stats.total,
            "tagged": stats.tagged,
            "untagged": stats.untagged,
            "tagged_ratio": round(stats.tagged_ratio, 4),
            "by_extension": stats.by_extension,
        }))
    else:
        print(format_stats(stats))
