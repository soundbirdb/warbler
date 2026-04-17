"""Audio format conversion utilities for warbler."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_TARGETS = {"mp3", "flac", "wav", "ogg"}


@dataclass
class ConversionResult:
    source: Path
    destination: Path
    success: bool
    error: str | None = None


def _build_ffmpeg_cmd(source: Path, destination: Path) -> list[str]:
    return ["ffmpeg", "-y", "-i", str(source), str(destination)]


def convert_file(source: Path, destination: Path) -> ConversionResult:
    """Convert *source* to *destination* using ffmpeg.

    The output format is inferred from *destination*'s suffix.
    Raises ``ValueError`` for unsupported target formats.
    """
    ext = destination.suffix.lstrip(".").lower()
    if ext not in SUPPORTED_TARGETS:
        raise ValueError(
            f"Unsupported target format '{ext}'. "
            f"Choose from: {', '.join(sorted(SUPPORTED_TARGETS))}"
        )

    cmd = _build_ffmpeg_cmd(source, destination)
    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        return ConversionResult(source=source, destination=destination, success=True)
    except subprocess.CalledProcessError as exc:
        return ConversionResult(
            source=source,
            destination=destination,
            success=False,
            error=exc.stderr.decode(errors="replace").strip(),
        )


def batch_convert(
    sources: list[Path],
    output_dir: Path,
    target_format: str,
) -> list[ConversionResult]:
    """Convert each file in *sources* to *target_format* inside *output_dir*."""
    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[ConversionResult] = []
    for src in sources:
        dest = output_dir / src.with_suffix(f".{target_format.lower()}").name
        results.append(convert_file(src, dest))
    return results
