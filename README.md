# warbler

A CLI tool for batch-processing and tagging audio files using spectral fingerprinting.

---

## Installation

```bash
pip install warbler
```

Or install from source:

```bash
git clone https://github.com/yourname/warbler.git && cd warbler && pip install .
```

---

## Usage

```bash
warbler [OPTIONS] <input>
```

**Examples:**

Process a single file:
```bash
warbler tag audio/track.mp3
```

Batch-process a directory:
```bash
warbler tag --recursive ./music/ --output ./tagged/
```

Run spectral fingerprinting only (no tagging):
```bash
warbler fingerprint ./music/ --format json
```

Preview changes without writing anything:
```bash
warbler tag --recursive ./music/ --dry-run
```

**Common options:**

| Flag | Description |
|------|-------------|
| `--recursive` | Process directories recursively |
| `--output` | Destination directory for processed files |
| `--dry-run` | Preview changes without writing |
| `--format` | Output format for fingerprint data (`json`, `csv`) |
| `--workers` | Number of parallel workers (default: 4) |
| `--verbose` | Enable verbose logging output |

---

## Supported Formats

warbler currently supports the following audio formats:

- MP3 (`.mp3`)
- FLAC (`.flac`)
- WAV (`.wav`)
- AAC (`.aac`, `.m4a`)
- OGG Vorbis (`.ogg`)

---

## Requirements

- Python 3.8+
- `ffmpeg` installed and available on your `PATH`

---

## License

MIT © 2024 yourname
