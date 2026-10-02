import unittest
from pathlib import Path

from antarctic_viz import cli

APP = Path("app.py")


class TestStreamlitArgv(unittest.TestCase):
    def test_normal_launch_hides_developer_menu(self):
        argv = cli.streamlit_argv(APP, [])
        self.assertEqual(argv[:3], ["streamlit", "run", "app.py"])
        self.assertIn("--server.showEmailPrompt=false", argv)
        self.assertIn("--server.address=localhost", argv)
        self.assertIn("--client.toolbarMode=viewer", argv)
        self.assertNotIn("--client.toolbarMode=developer", argv)

    def test_dev_option_shows_developer_menu_and_is_not_passed_on(self):
        argv = cli.streamlit_argv(APP, ["--dev", "--server.port", "8600"])
        self.assertIn("--client.toolbarMode=developer", argv)
        self.assertNotIn("--client.toolbarMode=viewer", argv)
        self.assertNotIn("--dev", argv)
        self.assertEqual(argv[-2:], ["--server.port", "8600"])

    def test_user_flags_come_after_defaults(self):
        argv = cli.streamlit_argv(APP, ["--server.address", "0.0.0.0"])
        self.assertGreater(argv.index("0.0.0.0"), argv.index("--server.address=localhost"))
