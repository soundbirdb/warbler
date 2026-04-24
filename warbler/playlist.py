"""Playlist generation: group audio files into ordered playlists by metadata or fingerprint criteria."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from warbler.tagger import read_fingerprint
from warbler.metadata import read_metadata


@dataclass
class PlaylistEntry:
    path: Path
    fingerprint: Optional[str]
    artist: Optional[str]
    title: Optional[str]
    album: Optional[str]


@dataclass
class Playlist:
    name: str
    entries: List[PlaylistEntry] = field(default_factory=list)

    @property
    def size(self) -> int:
        return len(self.entries)

    def tagged_entries(self) -> List[PlaylistEntry]:
        return [e for e in self.entries if e.fingerprint is not None]


def _build_entry(path: Path) -> PlaylistEntry:
    fp = read_fingerprint(path)
    try:
        meta = read_metadata(path)
    except Exception:
        meta = None
    return PlaylistEntry(
        path=path,
        fingerprint=fp,
        artist=meta.artist if meta else None,
        title=meta.title if meta else None,
        album=meta.album if meta else None,
    )


def build_playlist(name: str, paths: List[Path]) -> Playlist:
    """Build a Playlist from a list of audio file paths."""
    entries = [_build_entry(p) for p in paths]
    return Playlist(name=name, entries=entries)


def group_by_album(playlist: Playlist) -> dict[str, Playlist]:
    """Split a playlist into per-album sub-playlists."""
    groups: dict[str, list[PlaylistEntry]] = {}
    for entry in playlist.entries:
        key = entry.album or "Unknown Album"
        groups.setdefault(key, []).append(entry)
    return {
        album: Playlist(name=album, entries=entries)
        for album, entries in groups.items()
    }


def export_m3u(playlist: Playlist, dest: Path) -> None:
    """Write an M3U playlist file to *dest*."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8") as fh:
        fh.write("#EXTM3U\n")
        for entry in playlist.entries:
            label = " - ".join(filter(None, [entry.artist, entry.title])) or entry.path.name
            fh.write(f"#EXTINF:-1,{label}\n")
            fh.write(f"{entry.path}\n")
