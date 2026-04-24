"""CLI sub-command: inspect — report tag health across a directory."""
from __future__ import annotations

import argparse
from pathlib import Path

from warbler.cli import _collect_audio_files
from warbler.inspector import inspect_files, InspectionReport


def add_inspect_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    parser = subparsers.add_parser(
        "inspect",
        help="Report tag health and metadata completeness for audio files.",
    )
    parser.add_argument("directory", type=Path, help="Directory to inspect.")
    parser.add_argument(
        "-r", "--recursive", action="store_true", default=False,
        help="Recurse into sub-directories.",
    )
    parser.add_argument(
        "--show-errors", action="store_true", default=False,
        help="Print files that could not be inspected.",
    )
    parser.set_defaults(func=_run_inspect)


def _run_inspect(args: argparse.Namespace) -> None:
    paths = _collect_audio_files(args.directory, recursive=args.recursive)
    report = inspect_files(paths)
    _print_report(report, show_errors=args.show_errors)


def _print_report(report: InspectionReport, *, show_errors: bool = False) -> None:
    print(f"Files inspected : {report.total}")
    print(f"Tagged          : {report.tagged_count}")
    print(f"Fully complete  : {report.complete_count}")
    print(f"Errors          : {report.error_count}")

    incomplete = [
        i for i in report.inspections
        if not i.is_complete and i.error is None
    ]
    if incomplete:
        print("\nIncomplete files:")
        for insp in incomplete:
            missing = []
            if not insp.is_tagged:
                missing.append("fingerprint")
            if not insp.has_title:
                missing.append("title")
            if not insp.has_artist:
                missing.append("artist")
            if not insp.has_album:
                missing.append("album")
            print(f"  {insp.path}  missing={missing}")

    if show_errors:
        errors = [i for i in report.inspections if i.error is not None]
        if errors:
            print("\nErrors:")
            for insp in errors:
                print(f"  {insp.path}: {insp.error}")
