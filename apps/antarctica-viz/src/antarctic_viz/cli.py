"""``antarctic-viz`` console entry point: launches the Streamlit app."""

import sys
from pathlib import Path

# Launch defaults: skip the first-run email prompt, send no usage statistics, and
# listen on this machine only. Flags given on the command line come later and win,
# e.g. ``antarctic-viz --server.address 0.0.0.0`` to share the app on the network.
DEFAULT_FLAGS = [
    "--server.showEmailPrompt=false",
    "--browser.gatherUsageStats=false",
    "--server.address=localhost",
]
DEV_OPTION = "--dev"
# Viewer mode hides Streamlit's developer menu (Deploy, Rerun, Clear cache);
# ``--dev`` brings it back.
TOOLBAR_FLAGS = {False: "--client.toolbarMode=viewer", True: "--client.toolbarMode=developer"}


def streamlit_argv(app: Path, args: list[str]) -> list[str]:
    """``streamlit run`` arguments for ``app``, given the user's command-line ``args``."""
    dev = DEV_OPTION in args
    rest = [arg for arg in args if arg != DEV_OPTION]
    return ["streamlit", "run", str(app), *DEFAULT_FLAGS, TOOLBAR_FLAGS[dev], *rest]


def main() -> None:
    from streamlit.web import cli as stcli

    sys.argv = streamlit_argv(Path(__file__).with_name("app.py"), sys.argv[1:])
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
