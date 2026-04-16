"""Tests for warbler.filter."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from warbler.filter import FilterCriteria, FilterResult, apply_filter


def _paths(*names: str) -> list[Path]:
    return [Path(n) for n in names]


class TestFilterCriteria:
    def test_validate_raises_when_both_flags_set(self):
        c = FilterCriteria(tagged_only=True, untagged_only=True)
        with pytest.raises(ValueError):
            c.validate()

    def test_validate_passes_for_tagged_only(self):
        FilterCriteria(tagged_only=True).validate()

    def test_validate_passes_for_untagged_only(self):
        FilterCriteria(untagged_only=True).validate()


class TestApplyFilter:
    def _run(self, paths, criteria, fp_map):
        def fake_read(p):
            val = fp_map.get(str(p))
            if val is None:
                raise ValueError("no tag")
            return val

        with patch("warbler.filter.read_fingerprint", side_effect=fake_read):
            return apply_filter(paths, criteria)

    def test_returns_all_when_no_criteria(self):
        ps = _paths("a.mp3", "b.flac")
        results = self._run(ps, FilterCriteria(), {"a.mp3": "abc", "b.flac": None})
        assert len(results) == 2

    def test_tagged_only_excludes_untagged(self):
        ps = _paths("a.mp3", "b.mp3")
        results = self._run(ps, FilterCriteria(tagged_only=True), {"a.mp3": "fp1", "b.mp3": None})
        assert len(results) == 1
        assert results[0].path == Path("a.mp3")

    def test_untagged_only_excludes_tagged(self):
        ps = _paths("a.mp3", "b.mp3")
        results = self._run(ps, FilterCriteria(untagged_only=True), {"a.mp3": "fp1", "b.mp3": None})
        assert len(results) == 1
        assert results[0].path == Path("b.mp3")

    def test_extension_filter(self):
        ps = _paths("a.mp3", "b.flac")
        results = self._run(ps, FilterCriteria(extension=".mp3"), {"a.mp3": "fp", "b.flac": "fp2"})
        assert all(r.path.suffix == ".mp3" for r in results)

    def test_is_tagged_property(self):
        r_tagged = FilterResult(path=Path("x.mp3"), fingerprint="abc")
        r_untagged = FilterResult(path=Path("y.mp3"), fingerprint=None)
        assert r_tagged.is_tagged is True
        assert r_untagged.is_tagged is False
