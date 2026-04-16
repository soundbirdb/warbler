"""Tests for warbler.normalizer."""
from pathlib import Path

import pytest

from warbler.normalizer import (
    NormalizeResult,
    _normalize_stem,
    apply_normalization,
    normalize_filename,
)


class TestNormalizeStem:
    def test_lowercases(self):
        assert _normalize_stem("Hello") == "hello"

    def test_replaces_spaces_with_underscores(self):
        assert _normalize_stem("my track") == "my_track"

    def test_strips_special_chars(self):
        assert _normalize_stem("track!@#1") == "track1"

    def test_collapses_multiple_underscores(self):
        assert _normalize_stem("a  b   c") == "a_b_c"

    def test_empty_stem_returns_unnamed(self):
        assert _normalize_stem("!!!") == "unnamed"

    def test_preserves_hyphens(self):
        assert _normalize_stem("lo-fi beat") == "lo-fi_beat"


class TestNormalizeFilename:
    def test_already_normalized_not_renamed(self):
        p = Path("/music/cool_track.mp3")
        r = normalize_filename(p)
        assert not r.renamed
        assert r.error is None

    def test_uppercase_extension_lowercased(self):
        p = Path("/music/track.MP3")
        r = normalize_filename(p)
        assert r.normalized.suffix == ".mp3"
        assert r.renamed

    def test_spaces_in_stem_renamed(self):
        p = Path("/music/My Track.flac")
        r = normalize_filename(p)
        assert r.normalized.name == "my_track.flac"
        assert r.renamed

    def test_unsupported_extension_returns_error(self):
        p = Path("/docs/notes.txt")
        r = normalize_filename(p)
        assert r.error is not None
        assert not r.renamed

    def test_normalized_path_same_directory(self):
        p = Path("/music/sub/Track 01.flac")
        r = normalize_filename(p)
        assert r.normalized.parent == p.parent


class TestApplyNormalization:
    def test_dry_run_does_not_rename(self, tmp_path):
        src = tmp_path / "My Song.mp3"
        src.touch()
        result = normalize_filename(src)
        apply_normalization(result, dry_run=True)
        assert src.exists()

    def test_renames_file_on_disk(self, tmp_path):
        src = tmp_path / "My Song.mp3"
        src.touch()
        result = normalize_filename(src)
        apply_normalization(result, dry_run=False)
        assert (tmp_path / "my_song.mp3").exists()
        assert not src.exists()

    def test_no_op_when_already_normalized(self, tmp_path):
        src = tmp_path / "my_song.mp3"
        src.touch()
        result = normalize_filename(src)
        out = apply_normalization(result, dry_run=False)
        assert not out.renamed
        assert src.exists()

    def test_error_result_passed_through(self):
        bad = NormalizeResult(Path("a.txt"), Path("a.txt"), False, error="bad")
        out = apply_normalization(bad)
        assert out.error == "bad"
