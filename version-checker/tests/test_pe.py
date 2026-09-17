import unittest

from version_checker.pe import PEFormatError, has_version_info_resource

from .pe_fixtures import build_pe, build_version_resource_section


class TestHasVersionInfoResource(unittest.TestCase):
    def test_detects_embedded_version_info(self):
        data = build_pe(build_version_resource_section(resource_type_id=16))
        self.assertTrue(has_version_info_resource(data))

    def test_no_version_info_when_resource_tree_lacks_it(self):
        # Resource section exists but its only entry is RT_ICON (3), not
        # RT_VERSION (16).
        data = build_pe(build_version_resource_section(resource_type_id=3))
        self.assertFalse(has_version_info_resource(data))

    def test_no_version_info_when_no_resources_at_all(self):
        data = build_pe(resource_section=None)
        self.assertFalse(has_version_info_resource(data))

    def test_rejects_file_without_mz_header(self):
        with self.assertRaisesRegex(PEFormatError, "MZ"):
            has_version_info_resource(b"not a PE file" + b"\x00" * 100)

    def test_rejects_truncated_file(self):
        with self.assertRaises(PEFormatError):
            has_version_info_resource(b"MZ" + b"\x00" * 10)

    def test_rejects_file_missing_pe_signature(self):
        data = bytearray(build_pe(resource_section=None))
        # Corrupt the "PE\0\0" signature that e_lfanew points to.
        data[64:68] = b"XXXX"
        with self.assertRaisesRegex(PEFormatError, "PE signature"):
            has_version_info_resource(bytes(data))


if __name__ == "__main__":
    unittest.main()
