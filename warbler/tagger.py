"""Audio file tagging module for warbler.

Handles reading and writing metadata tags (ID3/Vorbis) to audio files,
storing spectral fingerprints and other computed metadata.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

try:
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, TXXX, ID3NoHeaderError
    from mutagen.flac import FLAC
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "mutagen is required for tagging support: pip install mutagen"
    ) from exc

FINGERPRINT_TAG_KEY = "WARBLER_FINGERPRINT"


def _get_extension(path: Path) -> str:
    return path.suffix.lower()


def write_fingerprint(audio_path: str | os.PathLike, fingerprint: str) -> None:
    """Write a spectral fingerprint string into the audio file's metadata.

    Supports MP3 (ID3) and FLAC (Vorbis comment) files.

    Args:
        audio_path: Path to the audio file.
        fingerprint: 64-character hex fingerprint string.

    Raises:
        ValueError: If the file format is not supported.
    """
    path = Path(audio_path)
    ext = _get_extension(path)

    if ext == ".mp3":
        try:
            tags = ID3(str(path))
        except ID3NoHeaderError:
            tags = ID3()
        tags.add(TXXX(encoding=3, desc=FINGERPRINT_TAG_KEY, text=fingerprint))
        tags.save(str(path))
    elif ext == ".flac":
        audio = FLAC(str(path))
        audio[FINGERPRINT_TAG_KEY.lower()] = fingerprint
        audio.save()
    else:
        raise ValueError(f"Unsupported audio format: {ext!r}. Supported: .mp3, .flac")


def read_fingerprint(audio_path: str | os.PathLike) -> Optional[str]:
    """Read a previously stored spectral fingerprint from an audio file's metadata.

    Args:
        audio_path: Path to the audio file.

    Returns:
        The fingerprint string if present, otherwise None.

    Raises:
        ValueError: If the file format is not supported.
    """
    path = Path(audio_path)
    ext = _get_extension(path)

    if ext == ".mp3":
        try:
            tags = ID3(str(path))
        except ID3NoHeaderError:
            return None
        for tag in tags.getall("TXXX"):
            if tag.desc == FINGERPRINT_TAG_KEY:
                return str(tag.text[0])
        return None
    elif ext == ".flac":
        audio = FLAC(str(path))
        values = audio.get(FINGERPRINT_TAG_KEY.lower())
        return values[0] if values else None
    else:
        raise ValueError(f"Unsupported audio format: {ext!r}. Supported: .mp3, .flac")
