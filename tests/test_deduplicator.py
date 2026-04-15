"""Tests for warbler.deduplicator."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from warbler.deduplicator import (
    DeduplicationReport,
    DuplicateGroup,
    find_duplicates,
)


FP_A = "aabbccdd" * 8  # 64-char hex string
FP_B = "11223344" * 8


def _paths(*names: str) -> list[Path]:
    return [Path(n) for n in names]


# ---------------------------------------------------------------------------
# DuplicateGroup
# ---------------------------------------------------------------------------

class TestDuplicateGroup:
    def test_is_duplicate_true_for_multiple_paths(self):
        g = DuplicateGroup(fingerprint=FP_A, paths=_paths("a.mp3", "b.mp3"))
        assert g.is_duplicate is True

    def test_is_duplicate_false_for_single_path(self):
        g = DuplicateGroup(fingerprint=FP_A, paths=_paths("a.mp3"))
        assert g.is_duplicate is False

    def test_size_reflects_path_count(self):
        g = DuplicateGroup(fingerprint=FP_A, paths=_paths("a.mp3", "b.mp3", "c.mp3"))
        assert g.size == 3


# ---------------------------------------------------------------------------
# DeduplicationReport
# ---------------------------------------------------------------------------

class TestDeduplicationReport:
    def _report(self) -> DeduplicationReport:
        return DeduplicationReport(
            scanned=5,
            untagged=1,
            duplicate_groups=[
                DuplicateGroup(FP_A, _paths("a.mp3", "b.mp3", "c.mp3")),
                DuplicateGroup(FP_B, _paths("d.flac", "e.flac")),
            ],
        )

    def test_duplicate_file_count(self):
        assert self._report().duplicate_file_count == 5

    def test_wasted_copies(self):
        # group A wastes 2, group B wastes 1
        assert self._report().wasted_copies == 3


# ---------------------------------------------------------------------------
# find_duplicates
# ---------------------------------------------------------------------------

class TestFindDuplicates:
    def _run(self, fingerprint_map: dict):
        """Helper: patch read_fingerprint to return values from *fingerprint_map*."""
        paths = [Path(k) for k in fingerprint_map]

        def _fake_read(path: Path):
            return fingerprint_map[str(path)]

        with patch("warbler.deduplicator.read_fingerprint", side_effect=_fake_read):
            return find_duplicates(paths)

    def test_no_duplicates_returns_empty_groups(self):
        report = self._run({"a.mp3": FP_A, "b.mp3": FP_B})
        assert report.duplicate_groups == []
        assert report.scanned == 2

    def test_detects_duplicate_pair(self):
        report = self._run({"a.mp3": FP_A, "b.mp3": FP_A, "c.mp3": FP_B})
        assert len(report.duplicate_groups) == 1
        assert report.duplicate_groups[0].size == 2

    def test_untagged_files_are_counted(self):
        report = self._run({"a.mp3": FP_A, "b.mp3": None})
        assert report.untagged == 1
        assert report.scanned == 2

    def test_all_untagged_no_groups(self):
        report = self._run({"a.mp3": None, "b.mp3": None})
        assert report.duplicate_groups == []
        assert report.untagged == 2
