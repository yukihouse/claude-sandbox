import pytest

from exe_checker.pe import PEFormatError, has_version_info_resource

from .pe_fixtures import build_pe, build_version_resource_section


def test_detects_embedded_version_info():
    data = build_pe(build_version_resource_section(resource_type_id=16))
    assert has_version_info_resource(data) is True


def test_no_version_info_when_resource_tree_lacks_it():
    # Resource section exists but its only entry is RT_ICON (3), not
    # RT_VERSION (16).
    data = build_pe(build_version_resource_section(resource_type_id=3))
    assert has_version_info_resource(data) is False


def test_no_version_info_when_no_resources_at_all():
    data = build_pe(resource_section=None)
    assert has_version_info_resource(data) is False


def test_rejects_file_without_mz_header():
    with pytest.raises(PEFormatError, match="MZ"):
        has_version_info_resource(b"not a PE file" + b"\x00" * 100)


def test_rejects_truncated_file():
    with pytest.raises(PEFormatError):
        has_version_info_resource(b"MZ" + b"\x00" * 10)


def test_rejects_file_missing_pe_signature():
    data = bytearray(build_pe(resource_section=None))
    # Corrupt the "PE\0\0" signature that e_lfanew points to.
    data[64:68] = b"XXXX"
    with pytest.raises(PEFormatError, match="PE signature"):
        has_version_info_resource(bytes(data))
