"""CLI sub-command: profile — run a batch and report timing statistics."""
from __future__ import annotations

import argparse
from pathlib import Path

from warbler.cli import _collect_audio_files
from warbler.fingerprint import compute_spectral_fingerprint
from warbler.profiler import Profiler
from warbler.tagger import read_fingerprint, write_fingerprint


def add_profile_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "profile",
        help="Measure per-file processing time across a directory.",
    )
    parser.add_argument("directory", type=Path, help="Root directory to scan.")
    parser.add_argument(
        "--recurse", "-r", action="store_true", help="Recurse into subdirectories."
    )
    parser.add_argument(
        "--top", type=int, default=5, metavar="N", help="Show N slowest files (default 5)."
    )
    parser.set_defaults(func=_run_profile)


def _run_profile(args: argparse.Namespace) -> None:
    files = _collect_audio_files(args.directory, recurse=args.recurse)
    if not files:
        print("No audio files found.")
        return

    profiler = Profiler()
    for path in files:
        profiler.begin(path)
        try:
            fp = read_fingerprint(path)
            if fp is None:
                import librosa  # type: ignore
                y, sr = librosa.load(str(path), sr=None, mono=True)
                fp = compute_spectral_fingerprint(y, sr)
                write_fingerprint(path, fp)
        except Exception as exc:  # noqa: BLE001
            print(f"  ERROR {path.name}: {exc}")
        finally:
            profiler.end()

    report = profiler.report
    print(f"\nProfiled {len(report.profiles)} file(s).")
    print(f"  Total   : {report.total_ms:.1f} ms")
    print(f"  Average : {report.average_ms:.1f} ms")

    top_n = sorted(report.profiles, key=lambda p: p.duration_ms, reverse=True)[: args.top]
    print(f"\nTop {args.top} slowest:")
    for prof in top_n:
        print(f"  {prof.duration_ms:8.1f} ms  {prof.path}")
