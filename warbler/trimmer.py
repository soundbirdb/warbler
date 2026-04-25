"""Silence-trimming utilities for audio files."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

SUPPORTED_EXTENSIONS = {".mp3", ".flac", ".wav", ".ogg", ".m4a"}


@dataclass(frozen=True)
class TrimResult:
    path: Path
    output_path: Optional[Path]
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None


@dataclass
class TrimReport:
    results: List[TrimResult] = field(default_factory=list)

    @property
    def trimmed_count(self) -> int:
        return sum(1 for r in self.results if r.success)

    @property
    def skipped_count(self) -> int:
        return sum(1 for r in self.results if not r.success and r.output_path is None)

    @property
    def error_count(self) -> int:
        return sum(1 for r in self.results if r.error is not None)


def _build_ffmpeg_trim_cmd(
    input_path: Path,
    output_path: Path,
    silence_threshold: float = -50.0,
    silence_duration: float = 0.5,
) -> List[str]:
    af = (
        f"silenceremove=start_periods=1:start_threshold={silence_threshold}dB"
        f":start_duration={silence_duration}"
        f",areverse"
        f",silenceremove=start_periods=1:start_threshold={silence_threshold}dB"
        f":start_duration={silence_duration}"
        f",areverse"
    )
    return [
        "ffmpeg", "-y", "-i", str(input_path),
        "-af", af,
        str(output_path),
    ]


def trim_file(
    path: Path,
    output_path: Optional[Path] = None,
    silence_threshold: float = -50.0,
    silence_duration: float = 0.5,
    dry_run: bool = False,
) -> TrimResult:
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return TrimResult(path=path, output_path=None, error=f"Unsupported format: {path.suffix}")

    dest = output_path or path.with_stem(path.stem + "_trimmed")

    if dry_run:
        return TrimResult(path=path, output_path=dest)

    cmd = _build_ffmpeg_trim_cmd(path, dest, silence_threshold, silence_duration)
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=120)
        if proc.returncode != 0:
            return TrimResult(path=path, output_path=None, error=proc.stderr.decode().strip())
        return TrimResult(path=path, output_path=dest)
    except Exception as exc:  # noqa: BLE001
        return TrimResult(path=path, output_path=None, error=str(exc))


def batch_trim(
    paths: List[Path],
    output_dir: Optional[Path] = None,
    silence_threshold: float = -50.0,
    silence_duration: float = 0.5,
    dry_run: bool = False,
) -> TrimReport:
    report = TrimReport()
    for p in paths:
        dest = (output_dir / p.name) if output_dir else None
        result = trim_file(p, dest, silence_threshold, silence_duration, dry_run)
        report.results.append(result)
    return report
