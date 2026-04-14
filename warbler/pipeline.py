"""High-level pipeline that ties fingerprinting and tagging together.

Provides a single entry-point function for processing one or more audio
files: compute their spectral fingerprint and persist it as metadata.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Sequence

import numpy as np

from warbler.fingerprint import compute_spectral_fingerprint
from warbler.tagger import read_fingerprint, write_fingerprint

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".mp3", ".flac"}


@dataclass
class ProcessingResult:
    path: str
    fingerprint: str
    skipped: bool = False  # True when file already had an up-to-date tag
    error: str | None = None


@dataclass
class BatchReport:
    results: List[ProcessingResult] = field(default_factory=list)

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.results if r.error is None)

    @property
    def error_count(self) -> int:
        return sum(1 for r in self.results if r.error is not None)

    @property
    def skipped_count(self) -> int:
        return sum(1 for r in self.results if r.skipped)


def process_file(
    audio_path: str,
    mel_spectrogram: np.ndarray,
    *,
    force: bool = False,
) -> ProcessingResult:
    """Fingerprint a single audio file and write the tag.

    Args:
        audio_path: Path to the audio file on disk.
        mel_spectrogram: Pre-computed mel spectrogram array for the file.
        force: If True, overwrite an existing fingerprint tag.

    Returns:
        A ProcessingResult describing the outcome.
    """
    try:
        if not force:
            existing = read_fingerprint(audio_path)
            if existing:
                logger.debug("Skipping %s — fingerprint already present.", audio_path)
                return ProcessingResult(path=audio_path, fingerprint=existing, skipped=True)

        fp = compute_spectral_fingerprint(mel_spectrogram)
        write_fingerprint(audio_path, fp)
        logger.info("Tagged %s with fingerprint %s", audio_path, fp)
        return ProcessingResult(path=audio_path, fingerprint=fp)
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Failed to process %s: %s", audio_path, exc)
        return ProcessingResult(path=audio_path, fingerprint="", error=str(exc))


def process_batch(
    items: Sequence[tuple[str, np.ndarray]],
    *,
    force: bool = False,
) -> BatchReport:
    """Process a batch of (path, mel_spectrogram) pairs.

    Args:
        items: Sequence of (audio_path, mel_spectrogram) tuples.
        force: Passed through to process_file.

    Returns:
        A BatchReport summarising all outcomes.
    """
    report = BatchReport()
    for audio_path, mel in items:
        result = process_file(audio_path, mel, force=force)
        report.results.append(result)
    return report
