"""Integration tests for the rename workflow."""
from pathlib import Path
from unittest.mock import patch

import pytest

from warbler.renamer import batch_rename, RenameReport

_FP = "deadbeef0000" + "a" * 52


class TestRenamerIntegration:
    def test_full_rename_cycle(self, tmp_path):
        """Files with fingerprints are renamed; those without are skipped."""
        tagged = tmp_path / "tagged.mp3"
        untagged = tmp_path / "untagged.mp3"
        tagged.touch()
        untagged.touch()

        def fake_read(p):
            return _FP if p.name.startswith("tagged") else None

        with patch("warbler.renamer.read_fingerprint", side_effect=fake_read):
            report = batch_rename([tagged, untagged])

        assert report.renamed_count == 1
        assert report.skipped_count == 1
        assert report.error_count == 0
        assert (tmp_path / "tagged_deadbeef0000.mp3").exists()
        assert untagged.exists()

    def test_dry_run_leaves_files_intact(self, tmp_path):
        src = tmp_path / "song.flac"
        src.touch()
        with patch("warbler.renamer.read_fingerprint", return_value=_FP):
            report = batch_rename([src], dry_run=True)
        assert report.renamed_count == 1
        assert src.exists()  # not actually moved

    def test_error_does_not_abort_batch(self, tmp_path):
        good = tmp_path / "good.mp3"
        bad = tmp_path / "bad.mp3"
        good.touch()
        bad.touch()

        def fake_read(p):
            if p.name == "bad.mp3":
                raise ValueError("corrupt tag")
            return _FP

        with patch("warbler.renamer.read_fingerprint", side_effect=fake_read):
            report = batch_rename([bad, good])

        assert report.error_count == 1
        assert report.renamed_count == 1
