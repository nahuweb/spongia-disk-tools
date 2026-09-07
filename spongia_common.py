"""Shared constants and parsing helpers for Spongia."""

import fnmatch
import shutil
import sys
from pathlib import Path

SUPPORTED_LANGS = {
    "es": "es",
    "español": "es",
    "spanish": "es",
    "en": "en",
    "english": "en",
    "inglés": "en",
    "ingles": "en",
    "pt": "pt",
    "pt-br": "pt",
    "pt_br": "pt",
    "brasil": "pt",
    "brazilian": "pt",
}


def resolve_lang(value):
    """Normaliza el valor --lang a es/en/pt (por defecto inglés)."""
    return SUPPORTED_LANGS.get(str(value).strip().lower(), "en")


class Colores:
    """ANSI colors used by the terminal interface."""

    ROJO = "\033[91m"
    VERDE = "\033[92m"
    AMARILLO = "\033[93m"
    AZUL = "\033[94m"
    MAGENTA = "\033[95m"
    CIAN = "\033[96m"
    BLANCO = "\033[97m"
    RESET = "\033[0m"
    NEGRITA = "\033[1m"
    DIM = "\033[2m"


def format_size(size: float) -> str:
    """Convierte bytes a formato legible (B, KB, MB, GB, TB...)."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def fit_terminal_line(message):
    """Keep a progress message on one terminal line."""
    try:
        width = shutil.get_terminal_size(fallback=(100, 20)).columns
    except OSError:
        width = 100
    width = max(width, 20)
    if len(message) <= width:
        return message
    return f"{message[: width - 1]}…"


def print_scan_progress(message, color):
    """Render progress without wrapping or concatenating terminal lines."""
    if not sys.stdout.isatty():
        return
    line = fit_terminal_line(message)
    print(f"\r\033[2K{color}{line}{Colores.RESET}", end="", flush=True)


def parse_size(text: str) -> int:
    """Convierte una cadena como '100MB' o '2GB' a bytes."""
    try:
        text = text.strip().upper()
        units = {
            "B": 1,
            "KB": 1024,
            "MB": 1024**2,
            "GB": 1024**3,
            "TB": 1024**4,
        }
        for unit, mult in sorted(units.items(), key=lambda x: len(x[0]), reverse=True):
            if text.endswith(unit):
                return int(float(text[: -len(unit)].strip()) * mult)
        return int(float(text))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid size: {text!r}") from exc


def parse_menu_size(value: str) -> int:
    """Parse menu sizes as MB when no explicit unit is supplied."""
    value = value.strip()
    if value and not value.upper().endswith(("B", "KB", "MB", "GB", "TB")):
        value = f"{value}MB"
    return parse_size(value)


def is_excluded(path, patterns):
    """Return True when a file or directory matches an exclusion pattern."""
    path = Path(path)
    candidates = {path.name, str(path), path.as_posix(), *path.parts}
    return any(
        fnmatch.fnmatch(candidate, pattern)
        for pattern in patterns
        for candidate in candidates
    )


def matches_extension(path, extensions):
    """Return True when a file matches one of the requested extensions."""
    if not extensions:
        return True
    suffix = Path(path).suffix.lower()
    normalized = {
        ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in extensions
    }
    return suffix in normalized


def parse_selection(value, maximum):
    """Parse comma-separated 1-based result numbers."""
    selected = []
    for token in value.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            number = int(token)
        except ValueError as exc:
            raise ValueError from exc
        if not 1 <= number <= maximum:
            raise ValueError
        if number not in selected:
            selected.append(number)
    return selected
