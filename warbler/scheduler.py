"""Scheduled/recurring batch processing for warbler."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from warbler.cli import _collect_audio_files
from warbler.pipeline import BatchReport, process_file


@dataclass
class SchedulerConfig:
    directory: Path
    interval_seconds: float
    recursive: bool = True
    force: bool = False
    on_report: Optional[Callable[[BatchReport], None]] = None


class BatchScheduler:
    """Runs batch processing on a directory at a fixed interval."""

    def __init__(self, config: SchedulerConfig) -> None:
        self._config = config
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            raise RuntimeError("Scheduler is already running.")
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=timeout)

    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            report = self._run_once()
            if self._config.on_report:
                self._config.on_report(report)
            self._stop_event.wait(timeout=self._config.interval_seconds)

    def _run_once(self) -> BatchReport:
        files = _collect_audio_files(self._config.directory, self._config.recursive)
        results = [process_file(f, force=self._config.force) for f in files]
        return BatchReport(results=results)
