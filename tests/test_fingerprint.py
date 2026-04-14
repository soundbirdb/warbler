"""Tests for warbler.fingerprint module."""

import hashlib
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from warbler.fingerprint import (
    compute_spectral_fingerprint,
    fingerprints_match,
    DEFAULT_SR,
    DEFAULT_N_MELS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fake_mel(n_mels: int = DEFAULT_N_MELS, frames: int = 100) -> np.ndarray:
    rng = np.random.default_rng(42)
    return rng.uniform(-60, 0, size=(n_mels, frames)).astype(np.float32)


# ---------------------------------------------------------------------------
# compute_spectral_fingerprint
# ---------------------------------------------------------------------------

class TestComputeSpectralFingerprint:
    def test_returns_64_char_hex(self, tmp_path):
        dummy_audio = tmp_path / "test.wav"
        dummy_audio.touch()

        fake_mel = _make_fake_mel()

        with (
            patch("warbler.fingerprint.librosa.load", return_value=(np.zeros(DEFAULT_SR), DEFAULT_SR)),
            patch("warbler.fingerprint.librosa.feature.melspectrogram", return_value=fake_mel),
            patch("warbler.fingerprint.librosa.power_to_db", return_value=fake_mel),
        ):
            fp = compute_spectral_fingerprint(dummy_audio)

        assert isinstance(fp, str)
        assert len(fp) == 64
        assert all(c in "0123456789abcdef" for c in fp)

    def test_deterministic_for_same_input(self, tmp_path):
        dummy_audio = tmp_path / "test.mp3"
        dummy_audio.touch()
        fake_mel = _make_fake_mel()

        with (
            patch("warbler.fingerprint.librosa.load", return_value=(np.zeros(DEFAULT_SR), DEFAULT_SR)),
            patch("warbler.fingerprint.librosa.feature.melspectrogram", return_value=fake_mel),
            patch("warbler.fingerprint.librosa.power_to_db", return_value=fake_mel),
        ):
            fp1 = compute_spectral_fingerprint(dummy_audio)
            fp2 = compute_spectral_fingerprint(dummy_audio)

        assert fp1 == fp2

    def test_different_audio_different_fingerprint(self, tmp_path):
        dummy_audio = tmp_path / "test.flac"
        dummy_audio.touch()
        mel_a = _make_fake_mel()
        mel_b = _make_fake_mel() * 0.5  # different values

        with (
            patch("warbler.fingerprint.librosa.load", return_value=(np.zeros(DEFAULT_SR), DEFAULT_SR)),
            patch("warbler.fingerprint.librosa.feature.melspectrogram", return_value=mel_a),
            patch("warbler.fingerprint.librosa.power_to_db", return_value=mel_a),
        ):
            fp_a = compute_spectral_fingerprint(dummy_audio)

        with (
            patch("warbler.fingerprint.librosa.load", return_value=(np.zeros(DEFAULT_SR), DEFAULT_SR)),
            patch("warbler.fingerprint.librosa.feature.melspectrogram", return_value=mel_b),
            patch("warbler.fingerprint.librosa.power_to_db", return_value=mel_b),
        ):
            fp_b = compute_spectral_fingerprint(dummy_audio)

        assert fp_a != fp_b

    def test_raises_for_missing_file(self):
        with pytest.raises(FileNotFoundError, match="Audio file not found"):
            compute_spectral_fingerprint("/nonexistent/path/audio.wav")


# ---------------------------------------------------------------------------
# fingerprints_match
# ---------------------------------------------------------------------------

class TestFingerprintsMatch:
    SAMPLE_FP = hashlib.sha256(b"test").hexdigest()
    OTHER_FP = hashlib.sha256(b"other").hexdigest()

    def test_identical_fps_match_strict(self):
        assert fingerprints_match(self.SAMPLE_FP, self.SAMPLE_FP) is True

    def test_different_fps_no_match_strict(self):
        assert fingerprints_match(self.SAMPLE_FP, self.OTHER_FP) is False

    def test_prefix_match_non_strict(self):
        fp1 = "abcdef1234567890" + "x" * 48
        fp2 = "abcdef1234567890" + "y" * 48
        assert fingerprints_match(fp1, fp2, strict=False) is True

    def test_prefix_mismatch_non_strict(self):
        assert fingerprints_match(self.SAMPLE_FP, self.OTHER_FP, strict=False) is False
