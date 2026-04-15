"""File-system watcher that triggers pipeline processing on new audio files."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Callable, Optional

from watchdog.events import FileCreatedEvent, FileSystemEventHandler
from watchdog.observers import Observer

from warbler.pipeline import ProcessingResult, process_file

logger = logging.getLogger(__name__)

AUDIO_EXTENSIONS = {".mp3", ".flac", ".ogg", ".wav", ".m4a"}


class _AudioEventHandler(FileSystemEventHandler):
    """Watchdog handler that processes newly created audio files."""

    def __init__(
        self,
        on_result: Optional[Callable[[ProcessingResult], None]] = None,
        force: bool = False,
    ) -> None:
        super().__init__()
        self._on_result = on_result
        self._force = force

    def on_created(self, event: FileCreatedEvent) -> None:  # type: ignore[override]
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() not in AUDIO_EXTENSIONS:
            return
        logger.info("Detected new audio file: %s", path)
        result = process_file(path, force=self._force)
        logger.debug("Processing result: %s", result)
        if self._on_result is not None:
            self._on_result(result)


class AudioWatcher:
    """Watch a directory and fingerprint audio files as they arrive."""

    def __init__(
        self,
        watch_dir: Path,
        recursive: bool = True,
        force: bool = False,
        on_result: Optional[Callable[[ProcessingResult], None]] = None,
    ) -> None:
        self.watch_dir = watch_dir
        self.recursive = recursive
        self._handler = _AudioEventHandler(on_result=on_result, force=force)
        self._observer: Optional[Observer] = None

    def start(self) -> None:
        """Start watching the directory (non-blocking)."""
        self._observer = Observer()
        self._observer.schedule(self._handler, str(self.watch_dir), recursive=self.recursive)
        self._observer.start()
        logger.info("Watching %s (recursive=%s)", self.watch_dir, self.recursive)

    def stop(self) -> None:
        """Stop the watcher and join the background thread."""
        if self._observer is not None:
            self._observer.stop()
            self._observer.join()
            self._observer = None
            logger.info("Watcher stopped.")

    def run_forever(self, poll_interval: float = 1.0) -> None:
        """Start watching and block until interrupted."""
        self.start()
        try:
            while True:
                time.sleep(poll_interval)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
