import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from version_checker.cli import main

from .pe_fixtures import build_pe, build_version_resource_section


class TestMain(unittest.TestCase):
    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp_dir.cleanup)
        self.tmp_path = Path(self._tmp_dir.name)

    def test_cli_prints_ok_and_exits_zero_when_version_info_present(self):
        exe_path = self.tmp_path / "with_version.exe"
        exe_path.write_bytes(build_pe(build_version_resource_section(resource_type_id=16)))

        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            exit_code = main([str(exe_path)])

        self.assertEqual(exit_code, 0)
        self.assertEqual(out.getvalue().strip(), "ok")

    def test_cli_prints_ng_and_exits_one_when_version_info_missing(self):
        exe_path = self.tmp_path / "without_version.exe"
        exe_path.write_bytes(build_pe(resource_section=None))

        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            exit_code = main([str(exe_path)])

        self.assertEqual(exit_code, 1)
        self.assertEqual(out.getvalue().strip(), "ng")

    def test_cli_exits_two_on_missing_file(self):
        missing_path = self.tmp_path / "does_not_exist.exe"

        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            exit_code = main([str(missing_path)])

        self.assertEqual(exit_code, 2)
        self.assertIn("error", err.getvalue())

    def test_cli_exits_two_on_invalid_pe_file(self):
        bad_path = self.tmp_path / "not_an_exe.exe"
        bad_path.write_bytes(b"this is not a PE file")

        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            exit_code = main([str(bad_path)])

        self.assertEqual(exit_code, 2)
        self.assertIn("not a valid PE file", err.getvalue())

    def test_cli_requires_an_argument(self):
        with self.assertRaises(SystemExit):
            main([])


if __name__ == "__main__":
    unittest.main()
