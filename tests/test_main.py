import tetris


def test_main_delegates_to_cli_run(monkeypatch):
    called = []
    monkeypatch.setattr("tetris.cli.run", lambda: called.append(True))
    tetris.main()
    assert called == [True]
