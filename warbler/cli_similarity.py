"""CLI sub-command: warbler similarity <fingerprint> <paths…>"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from warbler.similarity import find_similar


def add_similarity_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    parser = subparsers.add_parser(
        "similarity",
        help="Find audio files similar to a given spectral fingerprint.",
    )
    parser.add_argument("fingerprint", help="64-char hex fingerprint to search for")
    parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        help="Directories to search",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.85,
        help="Minimum similarity score 0–1 (default: 0.85)",
    )
    parser.add_argument(
        "--no-recurse",
        action="store_true",
        default=False,
        help="Do not recurse into subdirectories",
    )
    parser.set_defaults(func=_run_similarity)


def _run_similarity(args: argparse.Namespace) -> None:
    matches = find_similar(
        query=args.fingerprint,
        search_paths=args.paths,
        threshold=args.threshold,
        recursive=not args.no_recurse,
    )
    if not matches:
        print("No similar files found.")
        return
    print(f"Found {len(matches)} similar file(s):\n")
    for m in matches:
        print(f"  {m.path}  score={m.score:.3f}  distance={m.distance}")
