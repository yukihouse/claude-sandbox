import pytest

import tetris


def test_main_delegates_to_cli_run(monkeypatch):
    called = []
    monkeypatch.setattr("tetris.cli.run", lambda: called.append(True))
    tetris.main([])
    assert called == [True]


def test_main_version_flag_prints_version_and_exits(capsys):
    with pytest.raises(SystemExit) as exc_info:
        tetris.main(["--version"])
    assert exc_info.value.code == 0
    assert capsys.readouterr().out.strip() == f"tetris {tetris.__version__}"
