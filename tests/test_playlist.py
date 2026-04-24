"""Unit tests for warbler.playlist."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from warbler.playlist import (
    PlaylistEntry,
    Playlist,
    build_playlist,
    group_by_album,
    export_m3u,
    _build_entry,
)


def _entry(path: str, fp=None, artist=None, title=None, album=None) -> PlaylistEntry:
    return PlaylistEntry(Path(path), fingerprint=fp, artist=artist, title=title, album=album)


class TestPlaylist:
    def test_size_reflects_entry_count(self):
        pl = Playlist("test", [_entry("a.mp3"), _entry("b.mp3")])
        assert pl.size == 2

    def test_tagged_entries_filters_none_fingerprints(self):
        pl = Playlist("test", [_entry("a.mp3", fp="abc"), _entry("b.mp3")])
        assert len(pl.tagged_entries()) == 1

    def test_empty_playlist_size_zero(self):
        pl = Playlist("empty")
        assert pl.size == 0


class TestBuildPlaylist:
    def test_returns_playlist_with_correct_name(self):
        with patch("warbler.playlist.read_fingerprint", return_value=None), \
             patch("warbler.playlist.read_metadata", side_effect=Exception):
            pl = build_playlist("my-list", [Path("a.mp3")])
        assert pl.name == "my-list"

    def test_entry_count_matches_paths(self):
        paths = [Path("a.mp3"), Path("b.flac")]
        with patch("warbler.playlist.read_fingerprint", return_value="fp"), \
             patch("warbler.playlist.read_metadata", side_effect=Exception):
            pl = build_playlist("x", paths)
        assert pl.size == 2

    def test_fingerprint_stored_on_entry(self):
        with patch("warbler.playlist.read_fingerprint", return_value="deadbeef"), \
             patch("warbler.playlist.read_metadata", side_effect=Exception):
            pl = build_playlist("x", [Path("a.mp3")])
        assert pl.entries[0].fingerprint == "deadbeef"

    def test_metadata_fields_stored(self):
        meta = MagicMock(artist="Arca", title="Piel", album="Kick")
        with patch("warbler.playlist.read_fingerprint", return_value=None), \
             patch("warbler.playlist.read_metadata", return_value=meta):
            pl = build_playlist("x", [Path("a.mp3")])
        e = pl.entries[0]
        assert e.artist == "Arca" and e.title == "Piel" and e.album == "Kick"


class TestGroupByAlbum:
    def test_groups_entries_by_album(self):
        pl = Playlist("all", [
            _entry("a.mp3", album="Alpha"),
            _entry("b.mp3", album="Beta"),
            _entry("c.mp3", album="Alpha"),
        ])
        groups = group_by_album(pl)
        assert groups["Alpha"].size == 2
        assert groups["Beta"].size == 1

    def test_unknown_album_fallback(self):
        pl = Playlist("all", [_entry("a.mp3")])
        groups = group_by_album(pl)
        assert "Unknown Album" in groups


class TestExportM3U:
    def test_creates_file(self, tmp_path):
        pl = Playlist("demo", [_entry(str(tmp_path / "a.mp3"), artist="X", title="Y")])
        dest = tmp_path / "out" / "demo.m3u"
        export_m3u(pl, dest)
        assert dest.exists()

    def test_file_contains_extm3u_header(self, tmp_path):
        pl = Playlist("demo", [_entry(str(tmp_path / "a.mp3"))])
        dest = tmp_path / "demo.m3u"
        export_m3u(pl, dest)
        assert dest.read_text().startswith("#EXTM3U")

    def test_entry_label_uses_artist_and_title(self, tmp_path):
        pl = Playlist("demo", [_entry(str(tmp_path / "a.mp3"), artist="Burial", title="Archangel")])
        dest = tmp_path / "demo.m3u"
        export_m3u(pl, dest)
        assert "Burial - Archangel" in dest.read_text()
