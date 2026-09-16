import pytest

from exe_checker.cli import main

from .pe_fixtures import build_pe, build_version_resource_section


def test_cli_prints_ok_and_exits_zero_when_version_info_present(tmp_path, capsys):
    exe_path = tmp_path / "with_version.exe"
    exe_path.write_bytes(build_pe(build_version_resource_section(resource_type_id=16)))

    exit_code = main([str(exe_path)])

    assert exit_code == 0
    assert capsys.readouterr().out.strip() == "ok"


def test_cli_prints_ng_and_exits_one_when_version_info_missing(tmp_path, capsys):
    exe_path = tmp_path / "without_version.exe"
    exe_path.write_bytes(build_pe(resource_section=None))

    exit_code = main([str(exe_path)])

    assert exit_code == 1
    assert capsys.readouterr().out.strip() == "ng"


def test_cli_exits_two_on_missing_file(tmp_path, capsys):
    missing_path = tmp_path / "does_not_exist.exe"

    exit_code = main([str(missing_path)])

    assert exit_code == 2
    assert "error" in capsys.readouterr().err


def test_cli_exits_two_on_invalid_pe_file(tmp_path, capsys):
    bad_path = tmp_path / "not_an_exe.exe"
    bad_path.write_bytes(b"this is not a PE file")

    exit_code = main([str(bad_path)])

    assert exit_code == 2
    assert "not a valid PE file" in capsys.readouterr().err


def test_cli_requires_an_argument():
    with pytest.raises(SystemExit):
        main([])
