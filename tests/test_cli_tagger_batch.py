"""Tests for warbler.cli_tagger_batch."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from warbler.cli_tagger_batch import add_tagger_batch_subcommand, _run_tagger_batch


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")
    add_tagger_batch_subcommand(sub)
    return p


class TestAddTaggerBatchSubcommand:
    def test_registers_batch_tag_parser(self):
        p = _parser()
        ns = p.parse_args(["batch-tag", "/some/manifest.json"])
        assert ns.cmd == "batch-tag"

    def test_default_dry_run_is_false(self):
        p = _parser()
        ns = p.parse_args(["batch-tag", "/m.json"])
        assert ns.dry_run is False

    def test_dry_run_flag(self):
        p = _parser()
        ns = p.parse_args(["batch-tag", "/m.json", "--dry-run"])
        assert ns.dry_run is True

    def test_func_is_set(self):
        p = _parser()
        ns = p.parse_args(["batch-tag", "/m.json"])
        assert callable(ns.func)


class TestRunTaggerBatch:
    def test_exits_1_when_manifest_missing(self, tmp_path):
        ns = argparse.Namespace(
            manifest=tmp_path / "nope.json",
            dry_run=False,
        )
        with pytest.raises(SystemExit) as exc:
            _run_tagger_batch(ns)
        assert exc.value.code == 1

    def test_exits_1_on_invalid_json(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("not json", encoding="utf-8")
        ns = argparse.Namespace(manifest=bad, dry_run=False)
        with pytest.raises(SystemExit) as exc:
            _run_tagger_batch(ns)
        assert exc.value.code == 1

    def test_calls_batch_write_with_mapping(self, tmp_path):
        manifest = tmp_path / "manifest.json"
        manifest.write_text(
            json.dumps({"/a.mp3": "fp1", "/b.flac": "fp2"}),
            encoding="utf-8",
        )
        ns = argparse.Namespace(manifest=manifest, dry_run=False)
        mock_report = MagicMock(written_count=2, error_count=0, failed_paths=[])
        with patch("warbler.cli_tagger_batch.batch_write_fingerprints", return_value=mock_report) as mock_bw:
            _run_tagger_batch(ns)
        called_mapping = mock_bw.call_args.args[0]
        assert Path("/a.mp3") in called_mapping
        assert called_mapping[Path("/a.mp3")] == "fp1"

    def test_exits_2_on_errors(self, tmp_path):
        manifest = tmp_path / "manifest.json"
        manifest.write_text(json.dumps({"/bad.mp3": "fp"}), encoding="utf-8")
        ns = argparse.Namespace(manifest=manifest, dry_run=False)
        mock_report = MagicMock(
            written_count=0,
            error_count=1,
            failed_paths=[Path("/bad.mp3")],
        )
        with patch("warbler.cli_tagger_batch.batch_write_fingerprints", return_value=mock_report):
            with pytest.raises(SystemExit) as exc:
                _run_tagger_batch(ns)
        assert exc.value.code == 2
