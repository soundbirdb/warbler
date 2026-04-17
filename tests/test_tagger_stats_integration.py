"""Integration tests for tagger_stats against real temp files."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from warbler.tagger_stats import collect_stats, format_stats


def _fake_read_factory(tagged: set[str]):
    def _read(path: Path):
        return "deadbeef" if path.name in tagged else None
    return _read


class TestTaggerStatsIntegration:
    def test_empty_directory_gives_zero_stats(self, tmp_path):
        with patch("warbler.tagger_stats.read_fingerprint", return_value=None):
            stats = collect_stats([])
        assert stats.total == 0
        assert stats.tagged_ratio == 0.0

    def test_all_tagged(self, tmp_path):
        files = [tmp_path / "a.mp3", tmp_path / "b.mp3"]
        for f in files:
            f.touch()
        tagged = {f.name for f in files}
        with patch("warbler.tagger_stats.read_fingerprint", side_effect=_fake_read_factory(tagged)):
            stats = collect_stats(files)
        assert stats.tagged == 2
        assert stats.untagged == 0
        assert stats.tagged_ratio == 1.0

    def test_mixed_tagged_and_untagged(self, tmp_path):
        mp3 = tmp_path / "song.mp3"
        flac = tmp_path / "track.flac"
        mp3.touch()
        flac.touch()
        with patch("warbler.tagger_stats.read_fingerprint", side_effect=_fake_read_factory({"song.mp3"})):
            stats = collect_stats([mp3, flac])
        assert stats.tagged == 1
        assert stats.untagged == 1
        assert stats.by_extension["mp3"] == 1
        assert stats.by_extension["flac"] == 1

    def test_format_stats_output_is_string(self, tmp_path):
        from warbler.tagger_stats import TagStats
        s = TagStats(total=3, tagged=2, untagged=1, by_extension={"mp3": 3})
        result = format_stats(s)
        assert isinstance(result, str)
        assert "\n" in result
