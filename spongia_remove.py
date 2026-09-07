"""Safe file and directory removal for Spongia."""

import importlib.util
import os
import shutil
from pathlib import Path

from spongia_common import (  # pyright: ignore[reportMissingImports]
    Colores,
    parse_selection,
)
from spongia_translations import confirm_si, text


def interactive_remove(paths, lang="en"):
    """Ask which displayed paths to send to the trash."""
    if not paths:
        return
    try:
        answer = input(text(lang, "interactive_question")).strip()
        if not answer:
            return
        selected = parse_selection(answer, len(paths))
    except (ValueError, EOFError):
        print(f"{Colores.AMARILLO}{text(lang, 'interactive_invalid')}{Colores.RESET}")
        return
    except KeyboardInterrupt:
        print(f"\n{Colores.AMARILLO}{text(lang, 'interrupted')}{Colores.RESET}")
        return

    for number in selected:
        remove_path(
            paths[number - 1],
            to_trash=True,
            force=False,
            recursive=Path(paths[number - 1]).is_dir(),
            lang=lang,
        )


def _puede_borrar_permisos(path: Path) -> bool:
    """Intenta comprobar si el archivo/carpeta es accesible para borrado."""
    try:
        return os.access(path, os.W_OK)
    except OSError:
        return False


def _protected_paths(protected_dirs):
    """Return protected paths and which of them protect descendants."""
    if protected_dirs is None:
        system_root = Path(os.environ.get("SYSTEMROOT", "C:\\Windows"))
        protected_dirs = [Path.home(), system_root]
        protected_descendants = {system_root.expanduser().resolve()}
    else:
        protected_descendants = {
            Path(protected).expanduser().resolve()
            for protected in protected_dirs
            if protected
        }
    return protected_dirs, protected_descendants


def _is_protected(target, protected_dirs, protected_descendants):
    """Return True when target is a protected root or descendant."""
    target_real = target.resolve()
    for protected in protected_dirs:
        if not protected:
            continue
        protected_real = Path(protected).expanduser().resolve()
        if target_real == protected_real or (
            protected_real in protected_descendants
            and protected_real in target_real.parents
        ):
            return True
    return False


def _delete_target(target):
    """Delete a target permanently, including non-symlink directories."""
    try:
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target)
        else:
            target.unlink()
    except OSError:
        raise


def _send_to_trash_or_delete(target, force, lang):
    """Send target to trash when available, otherwise request permanent deletion."""
    if importlib.util.find_spec("send2trash") is not None:
        from send2trash import send2trash  # pyright: ignore[reportMissingModuleSource]

        send2trash(str(target))
        print(f"{Colores.VERDE}{text(lang, 'trashed', target=target)}{Colores.RESET}")
        return

    print(f"{Colores.AMARILLO}{text(lang, 'no_send2trash')}{Colores.RESET}")
    if not force:
        answer = input(text(lang, "confirm_permanent")).strip()
        if not confirm_si(answer, lang):
            return
    _delete_target(target)
    print(f"{Colores.VERDE}{text(lang, 'deleted_perm', target=target)}{Colores.RESET}")


def remove_path(
    ruta, to_trash=True, recursive=False, force=False, protected_dirs=None, lang="en"
):
    """Remove a file or directory, using the system trash by default."""
    protected_dirs, protected_descendants = _protected_paths(protected_dirs)
    target = Path(ruta).expanduser().absolute()

    if not target.exists() and not target.is_symlink():
        print(f"{Colores.ROJO}{text(lang, 'not_found', ruta=ruta)}{Colores.RESET}")
        return 1

    if _is_protected(target, protected_dirs, protected_descendants):
        print(
            f"{Colores.ROJO}{text(lang, 'protected', dir=target.resolve())}{Colores.RESET}"
        )
        return 1

    if target.is_dir() and not target.is_symlink() and not recursive:
        print(
            f"{Colores.AMARILLO}{text(lang, 'is_dir_warning', target=target)}{Colores.RESET}"
        )
        return 1

    print(f"{Colores.CIAN}{text(lang, 'target', target=target)}{Colores.RESET}")
    method_key = "method_trash" if to_trash else "method_permanent"
    print(
        f"{Colores.CIAN}{text(lang, 'method', method=text(lang, method_key))}{Colores.RESET}"
    )

    if not force:
        destination_key = "destination_trash" if to_trash else "destination_permanent"
        answer = input(
            text(
                lang,
                "confirm_question",
                name=target.name,
                dest=text(lang, destination_key),
            )
        ).strip()
        if not confirm_si(answer, lang):
            print(f"{Colores.AMARILLO}{text(lang, 'cancelled')}{Colores.RESET}")
            return 0

    try:
        if to_trash:
            _send_to_trash_or_delete(target, force, lang)
        else:
            _delete_target(target)
            print(
                f"{Colores.VERDE}{text(lang, 'deleted_perm', target=target)}{Colores.RESET}"
            )
        return 0
    except PermissionError:
        print(f"{Colores.ROJO}{text(lang, 'permission_denied')}{Colores.RESET}")
        print(f"{Colores.AMARILLO}{text(lang, 'permission_hint')}{Colores.RESET}")
        return 1
    except OSError as error:
        print(f"{Colores.ROJO}{text(lang, 'error', error=error)}{Colores.RESET}")
        return 1
