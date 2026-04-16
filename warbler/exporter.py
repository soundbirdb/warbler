"""Export fingerprint data to various formats for external consumption."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable, Sequence

from warbler.tagger import read_fingerprint


def collect_fingerprint_records(paths: Iterable[Path]) -> list[dict]:
    """Read fingerprints from a collection of audio files.

    Files that have no fingerprint tag are silently skipped.
    """
    records: list[dict] = []
    for path in paths:
        fp = read_fingerprint(path)
        if fp is not None:
            records.append({"file": str(path), "fingerprint": fp})
    return records


def export_to_json(records: Sequence[dict], dest: Path) -> None:
    """Write fingerprint records to a JSON file."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8") as fh:
        json.dump(records, fh, indent=2)


def export_to_csv(records: Sequence[dict], dest: Path) -> None:
    """Write fingerprint records to a CSV file with headers 'file' and 'fingerprint'."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["file", "fingerprint"])
        writer.writeheader()
        writer.writerows(records)


def export(paths: Iterable[Path], dest: Path, fmt: str = "json") -> int:
    """High-level export helper.  Returns the number of records written.

    Args:
        paths: Audio files to inspect.
        dest:  Destination file path (extension ignored; *fmt* controls format).
        fmt:   ``'json'`` or ``'csv'``.

    Raises:
        ValueError: If *fmt* is not supported.
    """
    if fmt not in {"json", "csv"}:
        raise ValueError(f"Unsupported export format: {fmt!r}")

    records = collect_fingerprint_records(paths)
    if fmt == "json":
        export_to_json(records, dest)
    else:
        export_to_csv(records, dest)
    return len(records)
