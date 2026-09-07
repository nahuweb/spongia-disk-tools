# 🧽 Spongia — Disk Tools

[![Tests](https://github.com/cryptonahue/spongia-disk-tools/actions/workflows/tests.yml/badge.svg)](https://github.com/cryptonahue/spongia-disk-tools/actions/workflows/tests.yml)

Command-line tools to analyze disk usage and safely remove files and folders.

Current release: **0.1.1**. See [CHANGELOG.md](CHANGELOG.md) for the release history.

## Features

- Find the largest files in a directory.
- Find the largest top-level folders.
- Send files and folders to the system trash.
- Permanently delete files only when explicitly requested.
- Protect the user profile and system directories.
- Require `--recursive` before deleting folders.
- Exclude files or folders with repeatable glob patterns.
- English, Spanish, and Brazilian Portuguese messages.

## Usage

Running `spongia` without arguments opens a guided interactive menu. It asks
for the language (Spanish, English, or Portuguese) and uses Spanish by default.
Press `Ctrl+C` during a scan to cancel safely. The command-line subcommands
remain available for scripted and non-interactive use.

```bash
# Open the interactive menu
spongia
```

### Find large files

```bash
# Files of at least 10 MB, top 20
spongia find

# Analyze a specific directory
spongia find --dir D:\Downloads

# Custom minimum size and result count
spongia find --dir . --min-size 100MB --top 50

# Find the largest top-level folders
spongia find dirs --dir .

# Exclude folders or files; --exclude can be repeated
spongia find --dir . --exclude .git --exclude "*.pyc"
```

### Remove files and folders

By default, Spongia sends the target to the system trash and asks for confirmation.

```bash
# Select results interactively and send them to the trash
spongia find --dir . --interactive

# Send a file to the trash
spongia remove locked_file.pdf

# Send a folder to the trash
spongia remove ./folder --recursive

# Permanently delete a file
spongia remove file.txt --permanent

# Skip confirmation (use with care)
spongia remove file.txt --force
```

> ⚠️ **Safety:** confirmation is required unless `--force` is used. The user-profile root cannot be deleted, and the Windows directory plus its descendants are protected; files inside the user profile remain removable. Install `send2trash` to enable safe trash operations.

## Installation

### From the repository

```bash
pip install .
```

### From GitHub (without cloning)

```bash
python -m pip install "git+https://github.com/nahuweb/spongia-disk-tools.git"
```

### Optional trash support

For a local checkout:

```bash
python -m pip install ".[trash]"
```

From GitHub, including trash support:

```bash
python -m pip install "spongia-disk-tools[trash] @ git+https://github.com/nahuweb/spongia-disk-tools.git"
```

### Development tests

```bash
python -m unittest discover -s . -p "test_*.py" -v
```

## Dependencies

| Package | Required for |
| --- | --- |
| `send2trash` | Sending files to the system trash (optional) |

## Command reference

### `find`

| Argument | Default | Description |
| --- | --- | --- |
| `mode` | `files` | `files` for files or `dirs` for folders |
| `--dir, -d` | `.` | Directory to analyze |
| `--min-size` | `10MB` | Minimum file size, such as `50MB` or `1GB` |
| `--top` | `20` | Number of results |
| `--exclude` | — | Exclusion pattern; can be repeated |
| `--extension` | — | File extension to include; can be repeated |
| `--interactive` | off | Select displayed results for the trash |
| `--lang, -L` | `en` | `en`, `es`, or `pt` |

### `remove`

| Argument | Default | Description |
| --- | --- | --- |
| `ruta` | — | File or folder to remove |
| `--recursive, -r` | off | Allow folder removal |
| `--permanent` | off | Permanently delete instead of using the trash |
| `--force, -f` | off | Skip confirmation |
| `--lang, -L` | `en` | `en`, `es`, or `pt` |

## Project files

```text
spongia.py          # CLI and menu entry point
spongia_common.py   # Shared parsing, colors, and terminal helpers
spongia_scan.py     # File and directory scanners
spongia_remove.py   # Safe removal and trash handling
spongia_translations.py # English, Spanish, and Portuguese messages
test_spongia.py     # Unit tests
pyproject.toml      # Package, lint, and build configuration
pyrightconfig.json  # Static type-checking scope
requirements.txt    # Runtime dependency note
CHANGELOG.md        # Release history
LICENSE             # MIT license
```

## License

MIT — see [LICENSE](LICENSE).
