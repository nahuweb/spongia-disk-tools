import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import spongia
from spongia_common import parse_menu_size  # pyright: ignore[reportMissingImports]


class SpongiaTests(unittest.TestCase):
    def test_parse_size(self):
        self.assertEqual(spongia.parse_size("1KB"), 1024)
        self.assertEqual(spongia.parse_size("1.5MB"), int(1.5 * 1024**2))
        self.assertEqual(spongia.parse_size("42"), 42)

    def test_confirm_si_by_language(self):
        self.assertTrue(spongia.confirm_si("sí", "es"))
        self.assertTrue(spongia.confirm_si("yes", "en"))
        self.assertFalse(spongia.confirm_si("sim", "en"))

    def test_remove_file_permanently_when_forced(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "temporary.txt"
            target.write_text("temporary", encoding="utf-8")
            result = spongia.remove_path(
                target, to_trash=False, force=True, protected_dirs=[], lang="en"
            )
            self.assertEqual(result, 0)
            self.assertFalse(target.exists())

    def test_remove_rejects_protected_descendant(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "protected.txt"
            target.write_text("protected", encoding="utf-8")
            result = spongia.remove_path(
                target, to_trash=False, force=True, protected_dirs=[root], lang="en"
            )
            self.assertEqual(result, 1)
            self.assertTrue(target.exists())

    def test_remove_allows_file_inside_user_profile(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "local-updater" / "installer.exe"
            target.parent.mkdir()
            target.write_bytes(b"installer")
            with patch("spongia.Path.home", return_value=root):
                result = spongia.remove_path(
                    target, to_trash=False, force=True, lang="en"
                )
            self.assertEqual(result, 0)
            self.assertFalse(target.exists())

    def test_remove_directory_requires_recursive(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "folder"
            target.mkdir()
            result = spongia.remove_path(
                target, to_trash=False, force=True, protected_dirs=[], lang="en"
            )
            self.assertEqual(result, 1)
            self.assertTrue(target.exists())

    def test_remove_symlink_removes_link_not_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / "original.txt"
            link = root / "link.txt"
            original.write_text("keep", encoding="utf-8")
            try:
                link.symlink_to(original)
            except (OSError, NotImplementedError):
                self.skipTest("Symlinks are unavailable in this environment")

            result = spongia.remove_path(
                link, to_trash=False, force=True, protected_dirs=[], lang="en"
            )
            self.assertEqual(result, 0)
            self.assertFalse(link.exists())
            self.assertTrue(original.exists())

    def test_parse_size_rejects_unknown_unit(self):
        with self.assertRaises(ValueError):
            spongia.parse_size("10XB")

    def test_parse_menu_size_defaults_to_megabytes(self):
        self.assertEqual(parse_menu_size("500"), 500 * 1024**2)
        self.assertEqual(parse_menu_size("500KB"), 500 * 1024)

    def test_parse_selection_validates_and_deduplicates(self):
        self.assertEqual(spongia.parse_selection("1, 2,1", 3), [1, 2])
        with self.assertRaises(ValueError):
            spongia.parse_selection("0", 3)

    def test_is_excluded_matches_names_and_globs(self):
        self.assertTrue(spongia.is_excluded(Path("build/cache/file.pyc"), ["build"]))
        self.assertTrue(spongia.is_excluded(Path("build/cache/file.pyc"), ["*.pyc"]))
        self.assertFalse(spongia.is_excluded(Path("src/main.py"), ["*.pyc"]))

    def test_main_accepts_extension_filter(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "included.bin").write_bytes(b"x" * 1024)
            (root / "ignored.txt").write_bytes(b"x" * 2048)
            output = io.StringIO()
            with redirect_stdout(output):
                result = spongia.main(
                    [
                        "find",
                        "--dir",
                        str(root),
                        "--min-size",
                        "0",
                        "--extension",
                        "bin",
                    ]
                )
            self.assertEqual(result, 0)
            self.assertIn("included.bin", output.getvalue())
            self.assertNotIn("ignored.txt", output.getvalue())

    def test_main_without_arguments_opens_menu(self):
        with patch("spongia.interactive_menu", return_value=0) as menu:
            self.assertEqual(spongia.main([]), 0)
        menu.assert_called_once()

    def test_main_handles_keyboard_interrupt_during_find(self):
        output = io.StringIO()
        with (
            patch("spongia.find_largest_files", side_effect=KeyboardInterrupt),
            redirect_stdout(output),
        ):
            result = spongia.main(["find", "--min-size", "0"])
        self.assertEqual(result, 130)
        self.assertIn("interrupted", output.getvalue().lower())

    def test_interactive_menu_asks_for_language(self):
        output = io.StringIO()
        with patch("builtins.input", side_effect=["es", "3"]), redirect_stdout(output):
            result = spongia.interactive_menu()
        self.assertEqual(result, 0)
        self.assertIn("Buscar archivos más pesados", output.getvalue())

    def test_find_largest_files_applies_exclusions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "included.bin").write_bytes(b"x" * 1024)
            (root / "ignored.pyc").write_bytes(b"x" * 2048)
            output = io.StringIO()
            with redirect_stdout(output):
                spongia.find_largest_files(root, min_size_mb=0, excludes=["*.pyc"])
            self.assertIn("included.bin", output.getvalue())
            self.assertNotIn("ignored.pyc", output.getvalue())


if __name__ == "__main__":
    unittest.main()
