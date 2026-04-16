"""CLI sub-command: filter audio files by tagging status."""
from __future__ import annotations

import argparse
from pathlib import Path

from warbler.filter import FilterCriteria, apply_filter
from warbler.cli import _collect_audio_files


def add_filter_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("filter", help="Filter audio files by fingerprint status")
    p.add_argument("directory", type=Path, help="Directory to search")
    p.add_argument("--recursive", action="store_true", default=False)
    p.add_argument("--extension", default=None, help="Limit to extension, e.g. .mp3")
    group = p.add_mutually_exclusive_group()
    group.add_argument("--tagged", action="store_true", default=False)
    group.add_argument("--untagged", action="store_true", default=False)
    p.set_defaults(func=_run_filter)


def _run_filter(ns: argparse.Namespace) -> None:
    paths = _collect_audio_files(ns.directory, recursive=ns.recursive)
    criteria = FilterCriteria(
        tagged_only=ns.tagged,
        untagged_only=ns.untagged,
        extension=ns.extension,
    )
    results = apply_filter(paths, criteria)
    for r in results:
        status = "tagged" if r.is_tagged else "untagged"
        print(f"{r.path}  [{status}]")
    print(f"\n{len(results)} file(s) matched.")
