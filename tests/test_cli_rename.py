"""Tests for warbler.cli_rename."""
import argparse
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from warbler.cli_rename import add_rename_subcommand, _run_rename
from warbler.renamer import RenameReport, RenameResult


def _parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    add_rename_subcommand(sub)
    return p


class TestAddRenameSubcommand:
    def test_registers_rename_parser(self):
        p = _parser()
        args = p.parse_args(["rename", "/tmp"])
        assert hasattr(args, "func")

    def test_default_template(self):
        args = _parser().parse_args(["rename", "/tmp"])
        assert args.template == "{stem}_{fingerprint}"

    def test_custom_template(self):
        args = _parser().parse_args(["rename", "/tmp", "--template", "fp_{fingerprint}"])
        assert args.template == "fp_{fingerprint}"

    def test_dry_run_default_false(self):
        args = _parser().parse_args(["rename", "/tmp"])
        assert args.dry_run is False

    def test_dry_run_flag(self):
        args = _parser().parse_args(["rename", "/tmp", "--dry-run"])
        assert args.dry_run is True

    def test_recursive_default_false(self):
        args = _parser().parse_args(["rename", "/tmp"])
        assert args.recursive is False


class TestRunRename:
    def _make_namespace(self, tmp_path, dry_run=False, recursive=False):
        ns = argparse.Namespace(
            directory=tmp_path,
            template="{stem}_{fingerprint}",
            dry_run=dry_run,
            recursive=recursive,
        )
        return ns

    def test_calls_batch_rename(self, tmp_path, capsys):
        report = RenameReport(results=[
            RenameResult(source=tmp_path / "a.mp3", destination=tmp_path / "a_abc.mp3", renamed=True),
        ])
        with patch("warbler.cli_rename._collect_audio_files", return_value=[tmp_path / "a.mp3"]) as mc, \
             patch("warbler.cli_rename.batch_rename", return_value=report) as mb:
            _run_rename(self._make_namespace(tmp_path))
            mb.assert_called_once()
        out = capsys.readouterr().out
        assert "RENAMED" in out

    def test_dry_run_label_in_output(self, tmp_path, capsys):
        report = RenameReport(results=[
            RenameResult(source=tmp_path / "a.mp3", destination=tmp_path / "a_abc.mp3", renamed=True),
        ])
        with patch("warbler.cli_rename._collect_audio_files", return_value=[]), \
             patch("warbler.cli_rename.batch_rename", return_value=report):
            _run_rename(self._make_namespace(tmp_path, dry_run=True))
        out = capsys.readouterr().out
        assert "DRY RUN" in out
