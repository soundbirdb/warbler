"""Split audio files into segments based on silence or fixed duration."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

SUPPORTED_FORMATS = {".mp3", ".flac", ".wav", ".ogg", ".m4a"}


@dataclass
class SplitResult:
    source: Path
    segments: List[Path] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None

    @property
    def segment_count(self) -> int:
        return len(self.segments)


@dataclass
class SplitReport:
    results: List[SplitResult] = field(default_factory=list)

    @property
    def total_segments(self) -> int:
        return sum(r.segment_count for r in self.results)

    @property
    def error_count(self) -> int:
        return sum(1 for r in self.results if not r.success)

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.results if r.success)


def _build_split_cmd(
    source: Path,
    output_dir: Path,
    segment_duration: int,
) -> List[str]:
    stem = source.stem
    suffix = source.suffix
    pattern = str(output_dir / f"{stem}_%03d{suffix}")
    return [
        "ffmpeg",
        "-i", str(source),
        "-f", "segment",
        "-segment_time", str(segment_duration),
        "-reset_timestamps", "1",
        "-c", "copy",
        pattern,
    ]


def split_file(
    source: Path,
    output_dir: Path,
    segment_duration: int = 30,
    *,
    run: callable = subprocess.run,
) -> SplitResult:
    if source.suffix.lower() not in SUPPORTED_FORMATS:
        return SplitResult(source=source, error=f"Unsupported format: {source.suffix}")

    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = _build_split_cmd(source, output_dir, segment_duration)

    try:
        proc = run(cmd, capture_output=True)
    except FileNotFoundError:
        return SplitResult(source=source, error="ffmpeg not found")

    if proc.returncode != 0:
        msg = proc.stderr.decode(errors="replace").strip()
        return SplitResult(source=source, error=msg or "ffmpeg error")

    segments = sorted(output_dir.glob(f"{source.stem}_*{source.suffix}"))
    return SplitResult(source=source, segments=segments)


def batch_split(
    sources: List[Path],
    output_dir: Path,
    segment_duration: int = 30,
) -> SplitReport:
    report = SplitReport()
    for src in sources:
        result = split_file(src, output_dir / src.stem, segment_duration)
        report.results.append(result)
    return report
