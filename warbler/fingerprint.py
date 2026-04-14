"""Spectral fingerprinting module for audio files."""

import hashlib
import numpy as np
from pathlib import Path
from typing import Optional

try:
    import librosa
except ImportError as e:
    raise ImportError("librosa is required for fingerprinting: pip install librosa") from e


DEFAULT_SR = 22050
DEFAULT_HOP_LENGTH = 512
DEFAULT_N_MELS = 128
FINGERPRINT_DURATION = 30  # seconds to sample for fingerprint


def compute_spectral_fingerprint(
    audio_path: str | Path,
    duration: Optional[float] = FINGERPRINT_DURATION,
    sr: int = DEFAULT_SR,
    n_mels: int = DEFAULT_N_MELS,
    hop_length: int = DEFAULT_HOP_LENGTH,
) -> str:
    """Compute a spectral fingerprint for an audio file.

    Loads up to `duration` seconds of audio, computes a mel spectrogram,
    reduces it to a condensed feature vector, and returns a hex digest.

    Args:
        audio_path: Path to the audio file.
        duration: Seconds of audio to analyse (None = full file).
        sr: Target sample rate.
        n_mels: Number of mel bands.
        hop_length: Hop length for the STFT.

    Returns:
        A 64-character hex string representing the fingerprint.
    """
    audio_path = Path(audio_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    y, _ = librosa.load(str(audio_path), sr=sr, duration=duration, mono=True)

    mel_spec = librosa.feature.melspectrogram(
        y=y, sr=sr, n_mels=n_mels, hop_length=hop_length
    )
    mel_db = librosa.power_to_db(mel_spec, ref=np.max)

    # Condense to a 1-D feature vector: mean + std across time frames per band
    mean_vec = mel_db.mean(axis=1)
    std_vec = mel_db.std(axis=1)
    feature_vec = np.concatenate([mean_vec, std_vec])

    # Quantise to 8-bit integers for a stable, compact representation
    quantised = np.clip(((feature_vec + 80) / 80 * 255), 0, 255).astype(np.uint8)

    digest = hashlib.sha256(quantised.tobytes()).hexdigest()
    return digest


def fingerprints_match(fp1: str, fp2: str, *, strict: bool = True) -> bool:
    """Compare two fingerprint hex strings.

    Args:
        fp1: First fingerprint.
        fp2: Second fingerprint.
        strict: If True, require exact match; otherwise compare first 16 chars.

    Returns:
        True if fingerprints are considered equal.
    """
    if strict:
        return fp1 == fp2
    return fp1[:16] == fp2[:16]
