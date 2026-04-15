"""CLI entry-point for warbler."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import List

import click

from warbler.pipeline import BatchReport, process_file
from warbler.reporter import format_summary, write_csv_report, write_json_report
from warbler.watcher import AudioWatcher

logger = logging.getLogger(__name__)

AUDIO_EXTENSIONS = {".mp3", ".flac", ".ogg", ".wav", ".m4a"}


def _collect_audio_files(directory: Path, recursive: bool) -> List[Path]:
    """Return all supported audio files under *directory*."""
    pattern = "**/*" if recursive else "*"
    return [
        p for p in directory.glob(pattern)
        if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS
    ]


@click.group()
@click.option("--verbose", "-v", is_flag=True, default=False, help="Enable debug logging.")
def main(verbose: bool) -> None:
    """Warbler — batch audio fingerprinting tool."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s %(message)s")


@main.command("run")
@click.argument("directory", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--recursive", "-r", is_flag=True, default=True, show_default=True)
@click.option("--force", "-f", is_flag=True, default=False, help="Overwrite existing fingerprints.")
@click.option("--json-report", type=click.Path(path_type=Path), default=None)
@click.option("--csv-report", type=click.Path(path_type=Path), default=None)
def run(
    directory: Path,
    recursive: bool,
    force: bool,
    json_report: Path | None,
    csv_report: Path | None,
) -> None:
    """Fingerprint all audio files in DIRECTORY."""
    files = _collect_audio_files(directory, recursive)
    click.echo(f"Found {len(files)} audio file(s).")

    results = [process_file(f, force=force) for f in files]
    report = BatchReport(results)

    click.echo(format_summary(report))

    if json_report:
        write_json_report(report, json_report)
        click.echo(f"JSON report written to {json_report}")
    if csv_report:
        write_csv_report(report, csv_report)
        click.echo(f"CSV report written to {csv_report}")

    if report.error_count:
        sys.exit(1)


@main.command("watch")
@click.argument("directory", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--recursive", "-r", is_flag=True, default=True, show_default=True)
@click.option("--force", "-f", is_flag=True, default=False, help="Overwrite existing fingerprints.")
def watch(directory: Path, recursive: bool, force: bool) -> None:
    """Watch DIRECTORY and fingerprint audio files as they arrive."""
    click.echo(f"Watching {directory} for new audio files. Press Ctrl+C to stop.")

    def _on_result(result):
        icon = {"success": "✓", "skipped": "–", "error": "✗"}.get(result.status, "?")
        click.echo(f"  {icon} {result.path.name}  [{result.status}]")

    watcher = AudioWatcher(directory, recursive=recursive, force=force, on_result=_on_result)
    watcher.run_forever()
