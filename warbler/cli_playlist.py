"""CLI sub-command: playlist — generate M3U playlists from audio directories."""
from __future__ import annotations

import argparse
from pathlib import Path

from warbler.cli import _collect_audio_files
from warbler.playlist import build_playlist, group_by_album, export_m3u


def add_playlist_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    parser = subparsers.add_parser("playlist", help="Generate M3U playlists from audio files")
    parser.add_argument("directory", type=Path, help="Root directory to scan")
    parser.add_argument("--output", "-o", type=Path, default=Path("."), help="Output directory for .m3u files")
    parser.add_argument("--name", default="warbler", help="Base name for the generated playlist")
    parser.add_argument("--recursive", "-r", action="store_true", default=False)
    parser.add_argument(
        "--group-by-album",
        action="store_true",
        default=False,
        help="Emit one playlist per album instead of a single file",
    )
    parser.set_defaults(func=_run_playlist)


def _run_playlist(args: argparse.Namespace) -> None:
    paths = _collect_audio_files(args.directory, recursive=args.recursive)
    playlist = build_playlist(args.name, paths)

    if args.group_by_album:
        groups = group_by_album(playlist)
        for album, sub in groups.items():
            safe = album.replace(" ", "_").replace("/", "-")
            dest = args.output / f"{safe}.m3u"
            export_m3u(sub, dest)
            print(f"  wrote {dest}  ({sub.size} tracks)")
    else:
        dest = args.output / f"{args.name}.m3u"
        export_m3u(playlist, dest)
        print(f"Playlist written to {dest}  ({playlist.size} tracks)")
