"""Rename audio files based on their fingerprint metadata."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from warbler.tagger import read_fingerprint


@dataclass
class RenameResult:
    source: Path
    destination: Optional[Path]
    renamed: bool
    error: Optional[str] = None


@dataclass
class RenameReport:
    results: List[RenameResult] = field(default_factory=list)

    @property
    def renamed_count(self) -> int:
        return sum(1 for r in self.results if r.renamed)

    @property
    def skipped_count(self) -> int:
        return sum(1 for r in self.results if not r.renamed and r.error is None)

    @property
    def error_count(self) -> int:
        return sum(1 for r in self.results if r.error is not None)


def _build_destination(source: Path, fingerprint: str, template: str) -> Path:
    stem = re.sub(r"[^a-zA-Z0-9_\-]", "", template.format(
        stem=source.stem,
        fingerprint=fingerprint[:12],
    ))
    return source.with_name(stem + source.suffix)


def rename_file(
    path: Path,
    template: str = "{stem}_{fingerprint}",
    dry_run: bool = False,
) -> RenameResult:
    try:
        fp = read_fingerprint(path)
    except Exception as exc:
        return RenameResult(source=path, destination=None, renamed=False, error=str(exc))

    if fp is None:
        return RenameResult(source=path, destination=None, renamed=False, error=None)

    dest = _build_destination(path, fp, template)
    if dest == path:
        return RenameResult(source=path, destination=dest, renamed=False, error=None)

    if not dry_run:
        path.rename(dest)

    return RenameResult(source=path, destination=dest, renamed=True, error=None)


def batch_rename(
    paths: List[Path],
    template: str = "{stem}_{fingerprint}",
    dry_run: bool = False,
) -> RenameReport:
    report = RenameReport()
    for p in paths:
        report.results.append(rename_file(p, template=template, dry_run=dry_run))
    return report
