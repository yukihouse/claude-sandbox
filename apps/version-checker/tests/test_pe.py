import struct
import unittest

from version_checker.pe import PEFormatError, has_version_info_resource

from .pe_fixtures import (
    DOS_HEADER_SIZE,
    HEADER_SIZE,
    build_pe,
    build_resource_section_skips_non_version_leaf_then_finds_version_info,
    build_version_resource_section,
)

_OPTIONAL_HEADER_OFFSET = DOS_HEADER_SIZE + 4 + 20
_DATA_DIRECTORY_OFFSET = _OPTIONAL_HEADER_OFFSET + 96
_SECTION_TABLE_OFFSET = _OPTIONAL_HEADER_OFFSET + 224  # OPTIONAL_HEADER_SIZE for PE32


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

    def test_rejects_truncated_coff_file_header(self):
        data = build_pe(resource_section=None)
        # Cut the file off partway through the 20-byte COFF file header.
        truncated = data[: DOS_HEADER_SIZE + 4 + 10]
        with self.assertRaisesRegex(PEFormatError, "truncated COFF file header"):
            has_version_info_resource(truncated)

    def test_rejects_pe_with_no_optional_header(self):
        data = bytearray(build_pe(resource_section=None))
        struct.pack_into("<H", data, DOS_HEADER_SIZE + 4 + 16, 0)  # SizeOfOptionalHeader
        with self.assertRaisesRegex(PEFormatError, "no optional header"):
            has_version_info_resource(bytes(data))

    def test_rejects_unrecognized_optional_header_magic(self):
        data = bytearray(build_pe(resource_section=None))
        struct.pack_into("<H", data, _OPTIONAL_HEADER_OFFSET, 0x1234)
        with self.assertRaisesRegex(PEFormatError, "unrecognized optional header magic"):
            has_version_info_resource(bytes(data))

    def test_pe32_plus_with_no_resource_directory_reports_no_version_info(self):
        # A PE32+ (64-bit) optional header lays the data directory 16 bytes
        # further in than PE32; a NumberOfRvaAndSizes of 0 there means the
        # file declares no data directories at all, resource or otherwise.
        data = bytearray(build_pe(resource_section=None))
        struct.pack_into("<H", data, _OPTIONAL_HEADER_OFFSET, 0x20B)  # PE32+
        struct.pack_into("<I", data, _OPTIONAL_HEADER_OFFSET + 108, 0)
        self.assertFalse(has_version_info_resource(bytes(data)))

    def test_rejects_truncated_section_table(self):
        data = build_pe(build_version_resource_section())
        truncated = data[: _SECTION_TABLE_OFFSET + 10]
        with self.assertRaisesRegex(PEFormatError, "truncated section table"):
            has_version_info_resource(truncated)

    def test_rejects_resource_rva_outside_any_section(self):
        data = bytearray(build_pe(build_version_resource_section()))
        resource_entry_offset = _DATA_DIRECTORY_OFFSET + 2 * 8
        struct.pack_into("<I", data, resource_entry_offset, 0x7FFFFFFF)
        with self.assertRaisesRegex(PEFormatError, "not contained in any section"):
            has_version_info_resource(bytes(data))

    def test_rejects_truncated_resource_directory_header(self):
        # Far too short to contain the 16-byte resource directory header.
        data = build_pe(b"\x00" * 8)
        with self.assertRaisesRegex(PEFormatError, "truncated resource directory$"):
            has_version_info_resource(data)

    def test_rejects_truncated_resource_directory_entry(self):
        # A valid 16-byte header claiming one entry, but no entry bytes follow.
        header_claiming_one_entry = struct.pack("<IIHHHH", 0, 0, 0, 0, 0, 1)
        data = build_pe(header_claiming_one_entry)
        with self.assertRaisesRegex(PEFormatError, "truncated resource directory entry"):
            has_version_info_resource(data)

    def test_ignores_truncated_version_data_entry(self):
        data = build_pe(build_version_resource_section())
        # Cut the file off partway through the 16-byte data-entry structure
        # that would otherwise point at the VS_VERSIONINFO bytes.
        truncated = data[: HEADER_SIZE + 72 + 5]
        self.assertFalse(has_version_info_resource(truncated))

    def test_ignores_version_resource_with_zero_size(self):
        section = bytearray(build_version_resource_section())
        struct.pack_into("<I", section, 72 + 4, 0)  # zero the VS_VERSIONINFO size field
        data = build_pe(bytes(section))
        self.assertFalse(has_version_info_resource(data))

    def test_skips_name_entry_that_is_not_itself_a_subdirectory(self):
        # A well-formed 3-level tree always has a subdirectory at the name
        # level; clearing that bit models a malformed tree that must be
        # skipped rather than misread as pointing at resource data.
        section = bytearray(build_version_resource_section())
        offset_field = 24 + 16 + 4  # name_offset + directory header + id field
        current = struct.unpack_from("<I", section, offset_field)[0]
        struct.pack_into("<I", section, offset_field, current & 0x7FFFFFFF)
        data = build_pe(bytes(section))
        self.assertFalse(has_version_info_resource(data))

    def test_skips_lang_entry_that_is_itself_a_subdirectory(self):
        # The lang level is always a leaf in a well-formed 3-level tree;
        # setting the subdirectory bit models a deeper tree than this
        # parser supports, which must be skipped rather than misread.
        section = bytearray(build_version_resource_section())
        offset_field = 48 + 16 + 4  # lang_offset + directory header + id field
        current = struct.unpack_from("<I", section, offset_field)[0]
        struct.pack_into("<I", section, offset_field, current | 0x80000000)
        data = build_pe(bytes(section))
        self.assertFalse(has_version_info_resource(data))

    def test_keeps_scanning_siblings_after_a_non_version_leaf(self):
        # Real multi-locale executables have several language entries per
        # resource; the first one here carries no version data, so the
        # parser must keep scanning rather than stop at it.
        data = build_pe(build_resource_section_skips_non_version_leaf_then_finds_version_info())
        self.assertTrue(has_version_info_resource(data))


if __name__ == "__main__":
    unittest.main()
