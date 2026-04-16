"""CLI subcommand: warbler schedule — run batch processing on an interval."""
from __future__ import annotations

import argparse
import signal
import sys
from pathlib import Path

from warbler.reporter import format_summary
from warbler.scheduler import BatchScheduler, SchedulerConfig


def add_schedule_subcommand(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "schedule",
        help="Repeatedly process a directory at a fixed interval.",
    )
    parser.add_argument("directory", type=Path, help="Directory to scan.")
    parser.add_argument(
        "--interval", type=float, default=60.0,
        help="Seconds between runs (default: 60).",
    )
    parser.add_argument("--recursive", action="store_true", default=True)
    parser.add_argument("--no-recursive", dest="recursive", action="store_false")
    parser.add_argument("--force", action="store_true", default=False)
    parser.set_defaults(func=_run_schedule)


def _run_schedule(args: argparse.Namespace) -> None:
    def on_report(report):
        print(format_summary(report))
        sys.stdout.flush()

    config = SchedulerConfig(
        directory=args.directory,
        interval_seconds=args.interval,
        recursive=args.recursive,
        force=args.force,
        on_report=on_report,
    )
    scheduler = BatchScheduler(config)

    def _handle_signal(sig, frame):
        print("\nStopping scheduler…")
        scheduler.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    print(f"Scheduler started — interval {args.interval}s. Press Ctrl+C to stop.")
    scheduler.start()
    signal.pause()
