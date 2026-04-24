"""CLI subcommand: batch-write fingerprints from a JSON/CSV manifest."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from warbler.tagger_batch import batch_write_fingerprints


def add_tagger_batch_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "batch-tag",
        help="Write fingerprints to audio files from a JSON manifest.",
    )
    parser.add_argument(
        "manifest",
        type=Path,
        help="Path to a JSON file mapping audio paths to fingerprints.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Validate the manifest without writing any tags.",
    )
    parser.set_defaults(func=_run_tagger_batch)


def _run_tagger_batch(args: argparse.Namespace) -> None:
    manifest_path: Path = args.manifest
    if not manifest_path.exists():
        print(f"[error] manifest not found: {manifest_path}", file=sys.stderr)
        sys.exit(1)

    try:
        raw: dict = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[error] could not read manifest: {exc}", file=sys.stderr)
        sys.exit(1)

    mapping = {Path(k): v for k, v in raw.items()}
    report = batch_write_fingerprints(mapping, dry_run=args.dry_run)

    verb = "would write" if args.dry_run else "wrote"
    print(f"{verb} {report.written_count} fingerprint(s), {report.error_count} error(s).")

    for path in report.failed_paths:
        print(f"  [failed] {path}", file=sys.stderr)

    if report.error_count:
        sys.exit(2)
