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


def main() -> None:
    from streamlit.web import cli as stcli

    app = Path(__file__).with_name("app.py")
    sys.argv = ["streamlit", "run", str(app), *DEFAULT_FLAGS, *sys.argv[1:]]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
