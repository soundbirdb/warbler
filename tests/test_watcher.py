"""Tests for warbler.watcher."""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest
from watchdog.events import FileCreatedEvent

from warbler.pipeline import ProcessingResult
from warbler.watcher import AudioWatcher, _AudioEventHandler


def _make_result(path: Path, status: str = "success") -> ProcessingResult:
    return ProcessingResult(path=path, status=status, fingerprint="abc123", error=None)


class TestAudioEventHandler:
    def _make_event(self, src_path: str, is_directory: bool = False) -> FileCreatedEvent:
        event = FileCreatedEvent(src_path)
        event.is_directory = is_directory
        return event

    @patch("warbler.watcher.process_file")
    def test_processes_mp3_file(self, mock_process: MagicMock, tmp_path: Path) -> None:
        audio = tmp_path / "track.mp3"
        mock_process.return_value = _make_result(audio)
        callback = MagicMock()
        handler = _AudioEventHandler(on_result=callback, force=False)

        handler.on_created(self._make_event(str(audio)))

        mock_process.assert_called_once_with(audio, force=False)
        callback.assert_called_once_with(mock_process.return_value)

    @patch("warbler.watcher.process_file")
    def test_ignores_non_audio_extension(self, mock_process: MagicMock, tmp_path: Path) -> None:
        txt_file = tmp_path / "notes.txt"
        handler = _AudioEventHandler()
        handler.on_created(self._make_event(str(txt_file)))
        mock_process.assert_not_called()

    @patch("warbler.watcher.process_file")
    def test_ignores_directory_events(self, mock_process: MagicMock, tmp_path: Path) -> None:
        handler = _AudioEventHandler()
        handler.on_created(self._make_event(str(tmp_path), is_directory=True))
        mock_process.assert_not_called()

    @patch("warbler.watcher.process_file")
    def test_force_flag_passed_to_process_file(self, mock_process: MagicMock, tmp_path: Path) -> None:
        audio = tmp_path / "track.flac"
        mock_process.return_value = _make_result(audio)
        handler = _AudioEventHandler(force=True)
        handler.on_created(self._make_event(str(audio)))
        mock_process.assert_called_once_with(audio, force=True)

    @patch("warbler.watcher.process_file")
    def test_no_callback_does_not_raise(self, mock_process: MagicMock, tmp_path: Path) -> None:
        audio = tmp_path / "track.ogg"
        mock_process.return_value = _make_result(audio)
        handler = _AudioEventHandler(on_result=None)
        handler.on_created(self._make_event(str(audio)))  # should not raise


class TestAudioWatcher:
    @patch("warbler.watcher.Observer")
    def test_start_schedules_observer(self, mock_observer_cls: MagicMock, tmp_path: Path) -> None:
        mock_observer = MagicMock()
        mock_observer_cls.return_value = mock_observer

        watcher = AudioWatcher(tmp_path, recursive=True)
        watcher.start()

        mock_observer.schedule.assert_called_once()
        mock_observer.start.assert_called_once()

    @patch("warbler.watcher.Observer")
    def test_stop_joins_observer(self, mock_observer_cls: MagicMock, tmp_path: Path) -> None:
        mock_observer = MagicMock()
        mock_observer_cls.return_value = mock_observer

        watcher = AudioWatcher(tmp_path)
        watcher.start()
        watcher.stop()

        mock_observer.stop.assert_called_once()
        mock_observer.join.assert_called_once()
        assert watcher._observer is None

    @patch("warbler.watcher.Observer")
    def test_stop_before_start_is_safe(self, mock_observer_cls: MagicMock, tmp_path: Path) -> None:
        watcher = AudioWatcher(tmp_path)
        watcher.stop()  # should not raise
        mock_observer_cls.return_value.stop.assert_not_called()
