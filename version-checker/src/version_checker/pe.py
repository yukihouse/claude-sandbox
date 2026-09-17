"""Minimal PE (Portable Executable) parser for detecting an embedded
``VS_VERSION_INFO`` resource, i.e. whether an .exe file has version
information (file version, product name, company name, ...) baked in.

Only the pieces of the PE/COFF format needed for that check are
implemented: the DOS/PE headers, the data directory, the section table,
and the (up to) three-level resource directory tree.
"""

from __future__ import annotations

import struct

IMAGE_DIRECTORY_ENTRY_RESOURCE = 2
RT_VERSION = 16
RESOURCE_ENTRY_IS_SUBDIRECTORY = 0x80000000
RESOURCE_ENTRY_MASK = 0x7FFFFFFF

# "VS_VERSION_INFO\0" encoded as UTF-16LE, the fixed key every
# VS_VERSIONINFO resource starts with.
VS_VERSION_INFO_KEY = "VS_VERSION_INFO\x00".encode("utf-16-le")


class PEFormatError(ValueError):
    """Raised when the input bytes are not a well-formed PE (.exe) file."""


def has_version_info_resource(data: bytes) -> bool:
    """Return True if `data` (the raw bytes of a PE file) embeds a
    VS_VERSION_INFO version-information resource.

    Raises PEFormatError if `data` is not a well-formed PE file.
    """
    resource_root = _find_resource_directory(data)
    if resource_root is None:
        return False
    resource_rva, resource_file_offset, sections = resource_root

    for type_id, type_offset in _read_directory_entries(data, resource_file_offset):
        if type_id != RT_VERSION or not (type_offset & RESOURCE_ENTRY_IS_SUBDIRECTORY):
            continue

        name_dir_offset = _rva_to_offset(
            resource_rva + (type_offset & RESOURCE_ENTRY_MASK), sections
        )
        for _name_id, name_offset in _read_directory_entries(data, name_dir_offset):
            if not (name_offset & RESOURCE_ENTRY_IS_SUBDIRECTORY):
                continue

            lang_dir_offset = _rva_to_offset(
                resource_rva + (name_offset & RESOURCE_ENTRY_MASK), sections
            )
            for _lang_id, lang_offset in _read_directory_entries(data, lang_dir_offset):
                if lang_offset & RESOURCE_ENTRY_IS_SUBDIRECTORY:
                    continue

                if _resource_data_is_version_info(data, resource_rva, lang_offset, sections):
                    return True

    return False


def _resource_data_is_version_info(
    data: bytes, resource_rva: int, data_entry_offset: int, sections
) -> bool:
    entry_offset = _rva_to_offset(resource_rva + data_entry_offset, sections)
    entry = data[entry_offset : entry_offset + 16]
    if len(entry) < 16:
        return False
    version_rva, version_size = struct.unpack_from("<II", entry, 0)
    if version_size == 0:
        return False

    version_offset = _rva_to_offset(version_rva, sections)
    version_data = data[version_offset : version_offset + version_size]
    # wLength(2) + wValueLength(2) + wType(2) precede the szKey string.
    return VS_VERSION_INFO_KEY in version_data[6 : 6 + len(VS_VERSION_INFO_KEY) + 8]


def _find_resource_directory(data: bytes):
    """Return (resource_rva, resource_file_offset, sections), or None if
    the PE file has no resource directory at all."""
    if len(data) < 0x40 or data[0:2] != b"MZ":
        raise PEFormatError("missing MZ (DOS) header")

    (e_lfanew,) = struct.unpack_from("<I", data, 0x3C)
    if data[e_lfanew : e_lfanew + 4] != b"PE\x00\x00":
        raise PEFormatError("missing PE signature")

    file_header_offset = e_lfanew + 4
    file_header = data[file_header_offset : file_header_offset + 20]
    if len(file_header) < 20:
        raise PEFormatError("truncated COFF file header")
    _machine, number_of_sections, _timestamp, _symtab, _nsyms, size_of_optional_header, _chars = (
        struct.unpack_from("<HHIIIHH", file_header, 0)
    )

    optional_header_offset = file_header_offset + 20
    if size_of_optional_header == 0:
        raise PEFormatError("PE file has no optional header")

    (magic,) = struct.unpack_from("<H", data, optional_header_offset)
    if magic == 0x10B:  # PE32
        data_directory_offset = optional_header_offset + 96
    elif magic == 0x20B:  # PE32+ (64-bit)
        data_directory_offset = optional_header_offset + 112
    else:
        raise PEFormatError(f"unrecognized optional header magic: 0x{magic:x}")

    (number_of_rva_and_sizes,) = struct.unpack_from("<I", data, data_directory_offset - 4)
    if number_of_rva_and_sizes <= IMAGE_DIRECTORY_ENTRY_RESOURCE:
        return None

    resource_entry_offset = data_directory_offset + IMAGE_DIRECTORY_ENTRY_RESOURCE * 8
    resource_rva, resource_size = struct.unpack_from("<II", data, resource_entry_offset)
    if resource_rva == 0 or resource_size == 0:
        return None

    section_table_offset = optional_header_offset + size_of_optional_header
    sections = _read_sections(data, section_table_offset, number_of_sections)
    resource_file_offset = _rva_to_offset(resource_rva, sections)
    return resource_rva, resource_file_offset, sections


def _read_sections(data: bytes, section_table_offset: int, number_of_sections: int):
    sections = []
    for index in range(number_of_sections):
        offset = section_table_offset + index * 40
        header = data[offset : offset + 40]
        if len(header) < 40:
            raise PEFormatError("truncated section table")
        virtual_size, virtual_address, size_of_raw_data, pointer_to_raw_data = struct.unpack_from(
            "<IIII", header, 8
        )
        sections.append((virtual_address, virtual_size, size_of_raw_data, pointer_to_raw_data))
    return sections


def _rva_to_offset(rva: int, sections) -> int:
    for virtual_address, virtual_size, size_of_raw_data, pointer_to_raw_data in sections:
        size = max(virtual_size, size_of_raw_data)
        if virtual_address <= rva < virtual_address + size:
            return rva - virtual_address + pointer_to_raw_data
    raise PEFormatError(f"RVA 0x{rva:x} is not contained in any section")


def _read_directory_entries(data: bytes, directory_offset: int):
    header = data[directory_offset : directory_offset + 16]
    if len(header) < 16:
        raise PEFormatError("truncated resource directory")
    number_of_named_entries, number_of_id_entries = struct.unpack_from("<HH", header, 12)

    entries = []
    entries_offset = directory_offset + 16
    for index in range(number_of_named_entries + number_of_id_entries):
        entry = data[entries_offset + index * 8 : entries_offset + index * 8 + 8]
        if len(entry) < 8:
            raise PEFormatError("truncated resource directory entry")
        name_or_id, offset_to_data = struct.unpack_from("<II", entry, 0)
        entries.append((name_or_id, offset_to_data))
    return entries
