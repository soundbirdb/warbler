"""Processing-time profiler: measures per-file and batch durations."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class FileProfile:
    path: Path
    duration_ms: float


@dataclass
class ProfileReport:
    profiles: List[FileProfile] = field(default_factory=list)

    @property
    def total_ms(self) -> float:
        return sum(p.duration_ms for p in self.profiles)

    @property
    def average_ms(self) -> Optional[float]:
        if not self.profiles:
            return None
        return self.total_ms / len(self.profiles)

    @property
    def slowest(self) -> Optional[FileProfile]:
        if not self.profiles:
            return None
        return max(self.profiles, key=lambda p: p.duration_ms)

    @property
    def fastest(self) -> Optional[FileProfile]:
        if not self.profiles:
            return None
        return min(self.profiles, key=lambda p: p.duration_ms)


class Profiler:
    """Context-manager based profiler for individual files."""

    def __init__(self) -> None:
        self._report = ProfileReport()
        self._current_path: Optional[Path] = None
        self._start: float = 0.0

    def begin(self, path: Path) -> None:
        self._current_path = path
        self._start = time.perf_counter()

    def end(self) -> FileProfile:
        if self._current_path is None:
            raise RuntimeError("end() called without a matching begin()")
        duration_ms = (time.perf_counter() - self._start) * 1000
        profile = FileProfile(path=self._current_path, duration_ms=duration_ms)
        self._report.profiles.append(profile)
        self._current_path = None
        return profile

    @property
    def report(self) -> ProfileReport:
        return self._report
