"""warbler.mixer — Combine multiple audio files into a single output using ffmpeg.

Provides utilities for merging a list of audio files (concatenation) and
producing a basic mix-down, with optional fingerprint tagging of the result.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence

# Supported output formats for the mixer
_SUPPORTED_FORMATS = {".mp3", ".flac", ".wav", ".ogg", ".m4a"}


@dataclass(frozen=True)
class MixResult:
    """Outcome of a single mix operation."""

    source_files: List[Path]
    output_file: Path
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        """Return True when no error was recorded."""
        return self.error is None


@dataclass
class MixReport:
    """Aggregate report for a batch mix session."""

    results: List[MixResult] = field(default_factory=list)

    @property
    def success_count(self) -> int:
        """Number of successful mix operations."""
        return sum(1 for r in self.results if r.success)

    @property
    def error_count(self) -> int:
        """Number of failed mix operations."""
        return sum(1 for r in self.results if not r.success)

    def add(self, result: MixResult) -> None:
        """Append a result to the report."""
        self.results.append(result)


def _build_concat_filter(n: int) -> str:
    """Return an ffmpeg filter_complex string that concatenates *n* audio streams."""
    inputs = "".join(f"[{i}:a]" for i in range(n))
    return f"{inputs}concat=n={n}:v=0:a=1[out]"


def _build_ffmpeg_concat_cmd(
    sources: Sequence[Path],
    output: Path,
    extra_args: Optional[List[str]] = None,
) -> List[str]:
    """Build the ffmpeg command list for concatenating *sources* into *output*."""
    cmd: List[str] = ["ffmpeg", "-y"]
    for src in sources:
        cmd += ["-i", str(src)]
    cmd += ["-filter_complex", _build_concat_filter(len(sources))]
    cmd += ["-map", "[out]"]
    if extra_args:
        cmd.extend(extra_args)
    cmd.append(str(output))
    return cmd


def mix_files(
    sources: Sequence[Path],
    output: Path,
    extra_args: Optional[List[str]] = None,
) -> MixResult:
    """Concatenate *sources* into *output* using ffmpeg.

    Parameters
    ----------
    sources:
        Ordered list of audio files to concatenate.
    output:
        Destination file path.  Its extension determines the codec.
    extra_args:
        Optional extra ffmpeg arguments inserted before the output path.

    Returns
    -------
    MixResult
        Contains the source list, output path, and any error message.
    """
    if not sources:
        return MixResult(
            source_files=list(sources),
            output_file=output,
            error="No source files provided.",
        )

    suffix = output.suffix.lower()
    if suffix not in _SUPPORTED_FORMATS:
        return MixResult(
            source_files=list(sources),
            output_file=output,
            error=f"Unsupported output format: '{suffix}'.",
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = _build_ffmpeg_concat_cmd(sources, output, extra_args)

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except FileNotFoundError:
        return MixResult(
            source_files=list(sources),
            output_file=output,
            error="ffmpeg executable not found.",
        )

    if proc.returncode != 0:
        stderr_text = proc.stderr.decode(errors="replace").strip()
        return MixResult(
            source_files=list(sources),
            output_file=output,
            error=stderr_text or f"ffmpeg exited with code {proc.returncode}.",
        )

    return MixResult(source_files=list(sources), output_file=output)


def batch_mix(
    jobs: Sequence[tuple[Sequence[Path], Path]],
    extra_args: Optional[List[str]] = None,
) -> MixReport:
    """Run multiple mix jobs and collect results into a :class:`MixReport`.

    Parameters
    ----------
    jobs:
        Iterable of ``(sources, output)`` pairs.
    extra_args:
        Optional extra ffmpeg arguments forwarded to every job.
    """
    report = MixReport()
    for sources, output in jobs:
        result = mix_files(sources, output, extra_args=extra_args)
        report.add(result)
    return report
