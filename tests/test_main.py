import unittest
from unittest import mock

import tetris


class TestMain(unittest.TestCase):
    def test_main_delegates_to_cli_run(self):
        called = []
        with mock.patch("tetris.cli.run", lambda: called.append(True)):
            tetris.main()
        self.assertEqual(called, [True])


if __name__ == "__main__":
    unittest.main()
