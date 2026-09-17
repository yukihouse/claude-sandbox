import struct
import unittest

from version_checker.pe import (
    PEFormatError,
    _read_directory_entries,
    _resource_data_is_version_info,
    _rva_to_offset,
    has_version_info_resource,
)

from .pe_fixtures import (
    DOS_HEADER_SIZE,
    _file_header,
    _minimal_optional_header,
    build_pe,
    build_pe_from_parts,
    build_resource_section_lang_entry_is_subdirectory,
    build_resource_section_name_entry_not_subdirectory,
    build_resource_section_skips_non_version_leaf_then_finds_version_info,
    build_version_resource_section,
)


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
        data = build_pe(resource_section=None)[: DOS_HEADER_SIZE + 4 + 10]
        with self.assertRaisesRegex(PEFormatError, "truncated COFF file header"):
            has_version_info_resource(data)

    def test_rejects_missing_optional_header(self):
        file_header = _file_header(number_of_sections=0, size_of_optional_header=0)
        data = build_pe_from_parts(file_header, optional_header=b"")
        with self.assertRaisesRegex(PEFormatError, "no optional header"):
            has_version_info_resource(data)

    def test_no_version_info_for_pe32_plus_with_empty_data_directory(self):
        # Exercises the PE32+ (64-bit) magic branch, and a NumberOfRvaAndSizes
        # too small to contain a resource-directory entry at all.
        optional_header = _minimal_optional_header(
            magic=0x20B, fixed_size=112, number_of_rva_and_sizes=0
        )
        file_header = _file_header(
            number_of_sections=0, size_of_optional_header=len(optional_header)
        )
        data = build_pe_from_parts(file_header, optional_header)
        self.assertFalse(has_version_info_resource(data))

    def test_rejects_unrecognized_optional_header_magic(self):
        optional_header = _minimal_optional_header(
            magic=0x999, fixed_size=96, number_of_rva_and_sizes=16, data_directory=[(0, 0)] * 16
        )
        file_header = _file_header(
            number_of_sections=0, size_of_optional_header=len(optional_header)
        )
        data = build_pe_from_parts(file_header, optional_header)
        with self.assertRaisesRegex(PEFormatError, "unrecognized optional header magic"):
            has_version_info_resource(data)

    def test_rejects_truncated_section_table(self):
        data_directory = [(0, 0)] * 16
        data_directory[2] = (100, 50)  # nonzero resource RVA/size to reach section parsing
        optional_header = _minimal_optional_header(
            magic=0x10B, fixed_size=96, number_of_rva_and_sizes=16, data_directory=data_directory
        )
        file_header = _file_header(
            number_of_sections=1, size_of_optional_header=len(optional_header)
        )
        data = build_pe_from_parts(file_header, optional_header, sections=b"\x00" * 10)
        with self.assertRaisesRegex(PEFormatError, "truncated section table"):
            has_version_info_resource(data)

    def test_skips_name_entry_that_is_not_a_subdirectory(self):
        data = build_pe(build_resource_section_name_entry_not_subdirectory())
        self.assertFalse(has_version_info_resource(data))

    def test_skips_lang_entry_that_is_marked_as_a_subdirectory(self):
        data = build_pe(build_resource_section_lang_entry_is_subdirectory())
        self.assertFalse(has_version_info_resource(data))

    def test_keeps_scanning_siblings_after_a_non_version_leaf(self):
        data = build_pe(build_resource_section_skips_non_version_leaf_then_finds_version_info())
        self.assertTrue(has_version_info_resource(data))


class TestResourceDataIsVersionInfo(unittest.TestCase):
    def test_returns_false_when_entry_is_truncated(self):
        sections = [(0, 10, 10, 0)]
        self.assertFalse(
            _resource_data_is_version_info(
                b"\x00" * 10, resource_rva=0, data_entry_offset=0, sections=sections
            )
        )

    def test_returns_false_for_zero_length_version_data(self):
        data = struct.pack("<II", 0, 0) + b"\x00" * 8  # version_rva=0, version_size=0
        sections = [(0, 100, 100, 0)]
        self.assertFalse(
            _resource_data_is_version_info(
                data, resource_rva=0, data_entry_offset=0, sections=sections
            )
        )


class TestRvaToOffset(unittest.TestCase):
    def test_finds_rva_in_a_later_section_after_earlier_mismatch(self):
        sections = [(0x1000, 0x200, 0x200, 0x400), (0x2000, 0x200, 0x200, 0x800)]
        self.assertEqual(_rva_to_offset(0x2050, sections), 0x850)

    def test_rejects_rva_outside_every_section(self):
        sections = [(0x1000, 0x200, 0x200, 0x400)]
        with self.assertRaisesRegex(PEFormatError, "not contained in any section"):
            _rva_to_offset(0x5000, sections)


class TestReadDirectoryEntries(unittest.TestCase):
    def test_rejects_truncated_directory_header(self):
        with self.assertRaisesRegex(PEFormatError, "truncated resource directory$"):
            _read_directory_entries(b"\x00" * 10, 0)

    def test_rejects_truncated_directory_entry(self):
        header = struct.pack("<IIHHHH", 0, 0, 0, 0, 0, 1)  # declares 1 entry, none follows
        with self.assertRaisesRegex(PEFormatError, "truncated resource directory entry"):
            _read_directory_entries(header, 0)


if __name__ == "__main__":
    unittest.main()
