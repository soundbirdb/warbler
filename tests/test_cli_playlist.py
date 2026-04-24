"""Unit tests for warbler.cli_playlist."""
from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from warbler.cli_playlist import add_playlist_subcommand, _run_playlist


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    add_playlist_subcommand(sub)
    return p


class TestAddPlaylistSubcommand:
    def test_registers_playlist_parser(self):
        p = _parser()
        ns = p.parse_args(["playlist", "/tmp"])
        assert hasattr(ns, "func")

    def test_default_recursive_false(self):
        p = _parser()
        ns = p.parse_args(["playlist", "/tmp"])
        assert ns.recursive is False

    def test_recursive_flag(self):
        p = _parser()
        ns = p.parse_args(["playlist", "/tmp", "--recursive"])
        assert ns.recursive is True

    def test_default_name_is_warbler(self):
        p = _parser()
        ns = p.parse_args(["playlist", "/tmp"])
        assert ns.name == "warbler"

    def test_custom_name(self):
        p = _parser()
        ns = p.parse_args(["playlist", "/tmp", "--name", "my-mix"])
        assert ns.name == "my-mix"

    def test_group_by_album_flag(self):
        p = _parser()
        ns = p.parse_args(["playlist", "/tmp", "--group-by-album"])
        assert ns.group_by_album is True

    def test_default_group_by_album_false(self):
        p = _parser()
        ns = p.parse_args(["playlist", "/tmp"])
        assert ns.group_by_album is False


class TestRunPlaylist:
    def _ns(self, tmp_path, group=False, name="demo", recursive=False):
        ns = argparse.Namespace(
            directory=tmp_path,
            output=tmp_path,
            name=name,
            recursive=recursive,
            group_by_album=group,
            func=_run_playlist,
        )
        return ns

    def test_single_playlist_written(self, tmp_path, capsys):
        paths = [tmp_path / "a.mp3"]
        fake_pl = MagicMock(size=1)
        with patch("warbler.cli_playlist._collect_audio_files", return_value=paths), \
             patch("warbler.cli_playlist.build_playlist", return_value=fake_pl) as bp, \
             patch("warbler.cli_playlist.export_m3u") as em:
            _run_playlist(self._ns(tmp_path))
            bp.assert_called_once_with("demo", paths)
            em.assert_called_once()

    def test_group_by_album_emits_multiple_files(self, tmp_path):
        sub1 = MagicMock(size=2)
        sub2 = MagicMock(size=1)
        fake_groups = {"Alpha": sub1, "Beta": sub2}
        fake_pl = MagicMock()
        with patch("warbler.cli_playlist._collect_audio_files", return_value=[]), \
             patch("warbler.cli_playlist.build_playlist", return_value=fake_pl), \
             patch("warbler.cli_playlist.group_by_album", return_value=fake_groups), \
             patch("warbler.cli_playlist.export_m3u") as em:
            _run_playlist(self._ns(tmp_path, group=True))
            assert em.call_count == 2
