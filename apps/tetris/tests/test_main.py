import contextlib
import io
import unittest
from unittest import mock

import tetris


class TestMain(unittest.TestCase):
    def test_main_delegates_to_cli_run(self):
        called = []
        with mock.patch("tetris.cli.run", lambda: called.append(True)):
            tetris.main([])
        self.assertEqual(called, [True])

    def test_main_version_flag_prints_version_and_exits(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            with self.assertRaises(SystemExit) as cm:
                tetris.main(["--version"])
        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(stdout.getvalue().strip(), f"tetris {tetris.__version__}")


if __name__ == "__main__":
    unittest.main()
