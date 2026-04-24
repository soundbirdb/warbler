"""Integration tests: build a playlist from real temp files and export to M3U."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from warbler.playlist import build_playlist, group_by_album, export_m3u, PlaylistEntry


def _fake_read_factory(fp_map: dict, meta_map: dict):
    def _read_fp(path):
        return fp_map.get(str(path))

    def _read_meta(path):
        from unittest.mock import MagicMock
        data = meta_map.get(str(path), {})
        m = MagicMock()
        m.artist = data.get("artist")
        m.title = data.get("title")
        m.album = data.get("album")
        return m

    return _read_fp, _read_meta


class TestPlaylistIntegration:
    def test_m3u_round_trip_contains_all_paths(self, tmp_path):
        files = [tmp_path / "a.mp3", tmp_path / "b.flac"]
        for f in files:
            f.touch()
        fp_map = {str(f): "abc" for f in files}
        meta_map = {str(f): {"artist": "X", "title": f.stem, "album": "Rec"} for f in files}
        rfp, rmeta = _fake_read_factory(fp_map, meta_map)
        with patch("warbler.playlist.read_fingerprint", side_effect=rfp), \
             patch("warbler.playlist.read_metadata", side_effect=rmeta):
            pl = build_playlist("test", files)
        dest = tmp_path / "test.m3u"
        export_m3u(pl, dest)
        content = dest.read_text()
        for f in files:
            assert str(f) in content

    def test_group_by_album_creates_separate_playlists(self, tmp_path):
        files = {
            tmp_path / "a.mp3": "AlbumA",
            tmp_path / "b.mp3": "AlbumA",
            tmp_path / "c.mp3": "AlbumB",
        }
        for f in files:
            f.touch()
        fp_map = {str(f): "fp" for f in files}
        meta_map = {str(f): {"album": album} for f, album in files.items()}
        rfp, rmeta = _fake_read_factory(fp_map, meta_map)
        with patch("warbler.playlist.read_fingerprint", side_effect=rfp), \
             patch("warbler.playlist.read_metadata", side_effect=rmeta):
            pl = build_playlist("all", list(files.keys()))
        groups = group_by_album(pl)
        assert groups["AlbumA"].size == 2
        assert groups["AlbumB"].size == 1
        for album, sub in groups.items():
            dest = tmp_path / f"{album}.m3u"
            export_m3u(sub, dest)
            assert dest.exists()

    def test_untagged_files_included_but_no_fingerprint(self, tmp_path):
        f = tmp_path / "x.mp3"
        f.touch()
        with patch("warbler.playlist.read_fingerprint", return_value=None), \
             patch("warbler.playlist.read_metadata", side_effect=Exception):
            pl = build_playlist("u", [f])
        assert pl.size == 1
        assert pl.entries[0].fingerprint is None
        assert pl.tagged_entries() == []
