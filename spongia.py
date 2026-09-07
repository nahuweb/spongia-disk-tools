#!/usr/bin/env python3
"""Spongia — Disk Tools: analysis and safe disk cleanup."""

import argparse
import sys
from contextlib import suppress
from pathlib import Path

from spongia_common import (  # pyright: ignore[reportMissingImports]
    SUPPORTED_LANGS,
    Colores,
    fit_terminal_line,
    format_size,
    is_excluded,
    matches_extension,
    parse_menu_size,
    parse_selection,
    parse_size,
    print_scan_progress,
    resolve_lang,
)
from spongia_remove import (  # pyright: ignore[reportMissingImports]
    _puede_borrar_permisos,
    interactive_remove,
    remove_path,
)
from spongia_scan import (  # pyright: ignore[reportMissingImports]
    find_largest_dirs,
    find_largest_files,
)
from spongia_translations import confirm_si, text

__all__ = [
    "SUPPORTED_LANGS",
    "Colores",
    "Path",
    "_puede_borrar_permisos",
    "confirm_si",
    "find_largest_dirs",
    "find_largest_files",
    "fit_terminal_line",
    "format_size",
    "interactive_remove",
    "is_excluded",
    "main",
    "matches_extension",
    "parse_menu_size",
    "parse_selection",
    "parse_size",
    "print_scan_progress",
    "remove_path",
    "resolve_lang",
    "text",
]

if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            with suppress(Exception):
                reconfigure(encoding="utf-8", errors="replace")


def choose_menu_language():
    """Ask for the language used by the guided menu."""
    prompt = "Idioma / Language / Idioma [es/en/pt] (default: es): "
    while True:
        try:
            value = input(prompt).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return "es"
        if not value:
            return "es"
        if value in SUPPORTED_LANGS:
            return resolve_lang(value)
        print("Idioma inválido. Elegí es, en o pt.")


def print_interrupted(lang):
    """Print a friendly cancellation message for Ctrl+C."""
    print(f"\n{Colores.AMARILLO}{text(lang, 'interrupted')}{Colores.RESET}")


def interactive_menu(lang=None):
    """Show the guided disk-analysis menu used by bare ``spongia``."""
    if lang is None:
        lang = choose_menu_language()

    while True:
        print(
            f"\n{Colores.CIAN}{Colores.NEGRITA}{text(lang, 'menu_title')}{Colores.RESET}"
        )
        print(f"  1. {text(lang, 'menu_files')}")
        print(f"  2. {text(lang, 'menu_dirs')}")
        print(f"  3. {text(lang, 'menu_exit')}")
        try:
            choice = input(text(lang, "menu_choice")).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if choice == "3":
            print(text(lang, "menu_goodbye"))
            return 0
        if choice not in ("1", "2"):
            print(f"{Colores.AMARILLO}{text(lang, 'menu_invalid')}{Colores.RESET}")
            continue

        try:
            directory = input(text(lang, "menu_dir")).strip() or "."
            min_size_text = input(text(lang, "menu_min_size")).strip() or "10MB"
            top_text = input(text(lang, "menu_top")).strip() or "20"
            min_bytes = parse_menu_size(min_size_text)
            top_n = int(top_text)
            if min_bytes < 0 or top_n < 1:
                raise ValueError
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        except (TypeError, ValueError):
            print(
                f"{Colores.AMARILLO}{text(lang, 'menu_invalid_config')}{Colores.RESET}"
            )
            continue

        min_mb = min_bytes / (1024 * 1024)
        try:
            if choice == "1":
                find_largest_files(
                    directory,
                    top_n=top_n,
                    min_size_mb=min_mb,
                    lang=lang,
                    interactive=True,
                )
            else:
                find_largest_dirs(
                    directory,
                    top_n=top_n,
                    lang=lang,
                    min_size_mb=min_mb,
                    interactive=True,
                )
        except KeyboardInterrupt:
            print_interrupted(lang)
            return 130

        try:
            input(text(lang, "menu_continue"))
        except (EOFError, KeyboardInterrupt):
            print()
            return 0


def main(argv=None):
    """CLI entry point."""
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        return interactive_menu()

    parser = argparse.ArgumentParser(
        prog="spongia",
        description=text("en", "description"),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    find_parser = subparsers.add_parser("find", help=text("en", "desc_find"))
    find_parser.add_argument("--dir", "-d", default=".", help=text("en", "dir_help"))
    find_parser.add_argument(
        "--min-size", type=str, default="10MB", help=text("en", "min_size_help")
    )
    find_parser.add_argument("--top", type=int, default=20, help=text("en", "top_help"))
    find_parser.add_argument(
        "--exclude", action="append", default=[], help=text("en", "exclude_help")
    )
    find_parser.add_argument(
        "--extension", action="append", default=[], help=text("en", "extension_help")
    )
    find_parser.add_argument(
        "--interactive", action="store_true", help=text("en", "interactive_help")
    )
    find_parser.add_argument(
        "mode",
        nargs="?",
        default="files",
        choices=["files", "dirs"],
        help=text("en", "mode_help"),
    )
    find_parser.add_argument(
        "--lang",
        "-L",
        default="en",
        choices=sorted(SUPPORTED_LANGS.keys()),
        help=text("en", "lang_help"),
    )

    remove_parser = subparsers.add_parser("remove", help=text("en", "desc_remove"))
    remove_parser.add_argument("ruta", help=text("en", "ruta_help"))
    remove_parser.add_argument(
        "--recursive", "-r", action="store_true", help=text("en", "recursive_help")
    )
    remove_parser.add_argument(
        "--permanent", action="store_true", help=text("en", "permanent_help")
    )
    remove_parser.add_argument(
        "--force", "-f", action="store_true", help=text("en", "force_help")
    )
    remove_parser.add_argument(
        "--lang",
        "-L",
        default="en",
        choices=sorted(SUPPORTED_LANGS.keys()),
        help=text("en", "lang_help"),
    )

    args = parser.parse_args(argv)
    lang = resolve_lang(getattr(args, "lang", "en"))

    if args.command == "find":
        try:
            min_bytes = parse_size(args.min_size)
        except (TypeError, ValueError):
            parser.error(text(lang, "min_size_invalid", value=args.min_size))
        if min_bytes < 0:
            parser.error(text(lang, "min_size_invalid", value=args.min_size))
        if args.top < 1:
            parser.error(text(lang, "top_invalid", value=args.top))
        min_mb = min_bytes / (1024 * 1024)
        try:
            if args.mode == "dirs":
                find_largest_dirs(
                    args.dir,
                    top_n=args.top,
                    lang=lang,
                    excludes=args.exclude,
                    min_size_mb=min_mb,
                    extensions=args.extension,
                    interactive=args.interactive,
                )
            else:
                find_largest_files(
                    args.dir,
                    top_n=args.top,
                    min_size_mb=min_mb,
                    lang=lang,
                    excludes=args.exclude,
                    extensions=args.extension,
                    interactive=args.interactive,
                )
        except KeyboardInterrupt:
            print_interrupted(lang)
            return 130
        return 0

    if args.command == "remove":
        return remove_path(
            args.ruta,
            to_trash=not args.permanent,
            recursive=args.recursive,
            force=args.force,
            lang=lang,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
