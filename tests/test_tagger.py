"""Tests for warbler.tagger — reading and writing fingerprint metadata tags."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch, call

from warbler.tagger import (
    write_fingerprint,
    read_fingerprint,
    FINGERPRINT_TAG_KEY,
)

FAKE_FINGERPRINT = "a" * 64


# ---------------------------------------------------------------------------
# write_fingerprint
# ---------------------------------------------------------------------------

class TestWriteFingerprint:
    def test_unsupported_format_raises(self, tmp_path):
        bad_file = tmp_path / "audio.wav"
        bad_file.touch()
        with pytest.raises(ValueError, match="Unsupported audio format"):
            write_fingerprint(bad_file, FAKE_FINGERPRINT)

    def test_mp3_writes_txxx_tag(self, tmp_path):
        mp3_file = tmp_path / "song.mp3"
        mp3_file.touch()

        mock_tags = MagicMock()
        with patch("warbler.tagger.ID3", return_value=mock_tags) as mock_id3, \
             patch("warbler.tagger.TXXX") as mock_txxx:
            write_fingerprint(mp3_file, FAKE_FINGERPRINT)

            mock_txxx.assert_called_once_with(
                encoding=3, desc=FINGERPRINT_TAG_KEY, text=FAKE_FINGERPRINT
            )
            mock_tags.add.assert_called_once()
            mock_tags.save.assert_called_once_with(str(mp3_file))

    def test_flac_writes_vorbis_comment(self, tmp_path):
        flac_file = tmp_path / "song.flac"
        flac_file.touch()

        mock_audio = MagicMock()
        with patch("warbler.tagger.FLAC", return_value=mock_audio):
            write_fingerprint(flac_file, FAKE_FINGERPRINT)

            mock_audio.__setitem__.assert_called_once_with(
                FINGERPRINT_TAG_KEY.lower(), FAKE_FINGERPRINT
            )
            mock_audio.save.assert_called_once()


# ---------------------------------------------------------------------------
# read_fingerprint
# ---------------------------------------------------------------------------

class TestReadFingerprint:
    def test_unsupported_format_raises(self, tmp_path):
        bad_file = tmp_path / "audio.ogg"
        bad_file.touch()
        with pytest.raises(ValueError, match="Unsupported audio format"):
            read_fingerprint(bad_file)

    def test_mp3_returns_none_when_no_header(self, tmp_path):
        mp3_file = tmp_path / "empty.mp3"
        mp3_file.touch()

        from mutagen.id3 import ID3NoHeaderError
        with patch("warbler.tagger.ID3", side_effect=ID3NoHeaderError):
            result = read_fingerprint(mp3_file)
        assert result is None

    def test_mp3_returns_fingerprint_when_present(self, tmp_path):
        mp3_file = tmp_path / "tagged.mp3"
        mp3_file.touch()

        mock_txxx = MagicMock()
        mock_txxx.desc = FINGERPRINT_TAG_KEY
        mock_txxx.text = [FAKE_FINGERPRINT]

        mock_tags = MagicMock()
        mock_tags.getall.return_value = [mock_txxx]

        with patch("warbler.tagger.ID3", return_value=mock_tags):
            result = read_fingerprint(mp3_file)

        assert result == FAKE_FINGERPRINT

    def test_mp3_returns_none_when_tag_absent(self, tmp_path):
        mp3_file = tmp_path / "no_tag.mp3"
        mp3_file.touch()

        mock_tags = MagicMock()
        mock_tags.getall.return_value = []

        with patch("warbler.tagger.ID3", return_value=mock_tags):
            result = read_fingerprint(mp3_file)

        assert result is None

    def test_flac_returns_fingerprint_when_present(self, tmp_path):
        flac_file = tmp_path / "tagged.flac"
        flac_file.touch()

        mock_audio = MagicMock()
        mock_audio.get.return_value = [FAKE_FINGERPRINT]

        with patch("warbler.tagger.FLAC", return_value=mock_audio):
            result = read_fingerprint(flac_file)

        assert result == FAKE_FINGERPRINT
        mock_audio.get.assert_called_once_with(FINGERPRINT_TAG_KEY.lower())

    def test_flac_returns_none_when_tag_absent(self, tmp_path):
        flac_file = tmp_path / "no_tag.flac"
        flac_file.touch()

        mock_audio = MagicMock()
        mock_audio.get.return_value = None

        with patch("warbler.tagger.FLAC", return_value=mock_audio):
            result = read_fingerprint(flac_file)

        assert result is None
