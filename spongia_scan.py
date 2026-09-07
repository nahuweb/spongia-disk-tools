"""Disk usage scanners for Spongia."""

import heapq
import os
import sys
import time
from pathlib import Path

from spongia_common import (  # pyright: ignore[reportMissingImports]
    Colores,
    format_size,
    is_excluded,
    matches_extension,
    print_scan_progress,
)
from spongia_remove import interactive_remove  # pyright: ignore[reportMissingImports]
from spongia_translations import text


def find_largest_files(
    directory,
    top_n=20,
    min_size_mb: float = 10,
    lang="en",
    excludes=(),
    extensions=(),
    interactive=False,
):
    """Encuentra los N archivos más pesados ≥ min_size usando un heap."""
    root = Path(directory).resolve()
    if not root.is_dir():
        print(
            f"{Colores.ROJO}{text(lang, 'dir_not_found', dir=directory)}{Colores.RESET}"
        )
        return

    min_bytes = min_size_mb * 1024 * 1024
    heap = []
    files_checked = 0

    print(
        f"{Colores.CIAN}{text(lang, 'searching_files', min=min_size_mb)}{Colores.RESET}"
    )
    print(f"{Colores.MAGENTA}{text(lang, 'directory', dir=root)}{Colores.RESET}")
    inicio = time.time()

    last_report = time.monotonic()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            name for name in dirnames if not is_excluded(Path(dirpath) / name, excludes)
        ]
        for name in filenames:
            file_path = Path(dirpath) / name
            if is_excluded(file_path, excludes) or not matches_extension(
                file_path, extensions
            ):
                continue
            files_checked += 1
            now = time.monotonic()
            if files_checked == 1 or now - last_report >= 1:
                print_scan_progress(
                    text(lang, "scan_progress", files=files_checked),
                    Colores.CIAN,
                )
                last_report = now
            filepath = os.path.join(dirpath, name)
            try:
                size = os.path.getsize(filepath)
            except (OSError, PermissionError):
                continue
            if size >= min_bytes:
                if len(heap) < top_n:
                    heapq.heappush(heap, (size, filepath))
                elif size > heap[0][0]:
                    heapq.heappushpop(heap, (size, filepath))

    completion = text(lang, "scan_complete", files=files_checked)
    if sys.stdout.isatty():
        print(f"\r\033[2K{Colores.VERDE}{completion}{Colores.RESET}")
    else:
        print(f"{Colores.VERDE}{completion}{Colores.RESET}")
    top = sorted(heap, key=lambda x: x[0], reverse=True)
    elapsed = time.time() - inicio

    print(f"\n{Colores.AMARILLO}{'=' * 78}{Colores.RESET}")
    print(
        f"{Colores.NEGRITA}{text(lang, 'top_title', n=len(top), time=elapsed, files=files_checked)}{Colores.RESET}"
    )
    print(f"{Colores.AMARILLO}{'=' * 78}{Colores.RESET}")
    print(text(lang, "table_header"))

    total = 0
    for i, (size, path) in enumerate(top, 1):
        total += size
        try:
            rel = os.path.relpath(path, root)
        except ValueError:
            rel = path
        print(f"{i:<3} {format_size(size):<10} {rel}")

    print(f"{Colores.AMARILLO}{'=' * 78}{Colores.RESET}")
    print(
        f"{Colores.AZUL}{text(lang, 'total_listed', size=format_size(total))}{Colores.RESET}"
    )

    if interactive:
        interactive_remove([path for _, path in top], lang=lang)


def find_largest_dirs(
    directory,
    top_n=15,
    lang="en",
    excludes=(),
    min_size_mb: float = 0,
    extensions=(),
    interactive=False,
):
    """Muestra las carpetas de un nivel con mayor tamaño total."""
    root = Path(directory).resolve()
    if not root.is_dir():
        print(
            f"{Colores.ROJO}{text(lang, 'dir_not_found', dir=directory)}{Colores.RESET}"
        )
        return

    items = []
    print(f"{Colores.CIAN}{text(lang, 'calculating_dirs', dir=root)}{Colores.RESET}")

    def dir_size(path):
        total = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                dirnames[:] = [
                    name
                    for name in dirnames
                    if not is_excluded(Path(dirpath) / name, excludes)
                ]
                for name in filenames:
                    file_path = Path(dirpath) / name
                    if is_excluded(file_path, excludes) or not matches_extension(
                        file_path, extensions
                    ):
                        continue
                    try:
                        size = file_path.stat().st_size
                        if size >= min_size_mb * 1024 * 1024:
                            total += size
                    except OSError:
                        pass
        except OSError:
            pass
        return total

    for entry in root.iterdir():
        if is_excluded(entry, excludes):
            continue
        if entry.is_dir():
            print(text(lang, "analyzing", name=entry.name))
            items.append((dir_size(entry), entry.name))
        elif entry.is_file() and matches_extension(entry, extensions):
            try:
                size = entry.stat().st_size
                if size >= min_size_mb * 1024 * 1024:
                    items.append((size, entry.name))
            except OSError:
                pass

    items.sort(key=lambda x: x[0], reverse=True)
    displayed = items[:top_n]
    print(f"\n{Colores.AMARILLO}{'=' * 78}{Colores.RESET}")
    print(f"{Colores.NEGRITA}{text(lang, 'dirs_title', name=root.name)}{Colores.RESET}")
    total = sum(s for s, _ in items)
    for i, (size, name) in enumerate(displayed, 1):
        print(f"{i:2}. {format_size(size):>12} - {name}")
    print(
        f"\n{Colores.AZUL}{text(lang, 'total_size', size=format_size(total))}{Colores.RESET}"
    )

    if interactive:
        interactive_remove([str(root / name) for _, name in displayed], lang=lang)
