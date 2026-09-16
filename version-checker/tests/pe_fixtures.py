"""Helpers that hand-assemble minimal, synthetic PE (.exe) byte strings for
tests, so the parser can be exercised without needing a real Windows
toolchain to compile fixtures.
"""

from __future__ import annotations

import struct

IMAGE_FILE_MACHINE_I386 = 0x14C
OPTIONAL_HEADER_SIZE = 224  # 96 fixed bytes + 16 data-directory entries * 8 bytes
DOS_HEADER_SIZE = 64
SECTION_HEADER_SIZE = 40

# Fixed header size when the file has exactly one section: DOS header +
# "PE\0\0" + COFF file header + optional header + one section header.
HEADER_SIZE = DOS_HEADER_SIZE + 4 + 20 + OPTIONAL_HEADER_SIZE + SECTION_HEADER_SIZE

VS_VERSION_INFO_KEY = "VS_VERSION_INFO\x00".encode("utf-16-le")


def _dos_header() -> bytes:
    header = bytearray(DOS_HEADER_SIZE)
    header[0:2] = b"MZ"
    struct.pack_into("<I", header, 0x3C, DOS_HEADER_SIZE)
    return bytes(header)


def _optional_header32(data_directory: list[tuple[int, int]]) -> bytes:
    fixed = struct.pack(
        "<HBBIIIIIIIIIHHHHHHIIIIHHIIIIII",
        0x10B,  # Magic (PE32)
        0, 0,  # Major/MinorLinkerVersion
        0,  # SizeOfCode
        0,  # SizeOfInitializedData
        0,  # SizeOfUninitializedData
        0,  # AddressOfEntryPoint
        0,  # BaseOfCode
        0,  # BaseOfData (PE32 only)
        0x400000,  # ImageBase
        0x1000,  # SectionAlignment
        0x200,  # FileAlignment
        0, 0,  # Major/MinorOperatingSystemVersion
        0, 0,  # Major/MinorImageVersion
        0, 0,  # Major/MinorSubsystemVersion
        0,  # Win32VersionValue
        0,  # SizeOfImage
        0,  # SizeOfHeaders
        0,  # CheckSum
        2,  # Subsystem
        0,  # DllCharacteristics
        0, 0, 0, 0,  # Stack/Heap reserve/commit
        0,  # LoaderFlags
        len(data_directory),  # NumberOfRvaAndSizes
    )
    directory = b"".join(struct.pack("<II", va, size) for va, size in data_directory)
    header = fixed + directory
    assert len(header) == OPTIONAL_HEADER_SIZE
    return header


def _section_header(name: bytes, virtual_size: int, virtual_address: int, size_of_raw_data: int, pointer_to_raw_data: int) -> bytes:
    header = name.ljust(8, b"\x00")[:8] + struct.pack(
        "<IIIIIIHHI",
        virtual_size,
        virtual_address,
        size_of_raw_data,
        pointer_to_raw_data,
        0,  # PointerToRelocations
        0,  # PointerToLinenumbers
        0,  # NumberOfRelocations
        0,  # NumberOfLinenumbers
        0x40000040,  # Characteristics (initialized data, readable)
    )
    assert len(header) == SECTION_HEADER_SIZE
    return header


def build_pe(resource_section: bytes | None) -> bytes:
    """Build a minimal, well-formed PE32 file. If `resource_section` is
    given, it becomes the raw bytes of a single ".rsrc" section, identity
    mapped (RVA == file offset) for simplicity, and wired up via the
    resource data directory entry."""
    data_directory = [(0, 0)] * 16
    sections = b""
    number_of_sections = 0

    if resource_section is not None:
        number_of_sections = 1
        data_directory[2] = (HEADER_SIZE, len(resource_section))
        sections = _section_header(
            b".rsrc",
            virtual_size=len(resource_section),
            virtual_address=HEADER_SIZE,
            size_of_raw_data=len(resource_section),
            pointer_to_raw_data=HEADER_SIZE,
        )

    file_header = struct.pack(
        "<HHIIIHH",
        IMAGE_FILE_MACHINE_I386,
        number_of_sections,
        0,  # TimeDateStamp
        0,  # PointerToSymbolTable
        0,  # NumberOfSymbols
        OPTIONAL_HEADER_SIZE,
        0x0102,  # Characteristics: EXECUTABLE_IMAGE | 32BIT_MACHINE
    )

    pe = _dos_header() + b"PE\x00\x00" + file_header + _optional_header32(data_directory) + sections
    if resource_section is not None:
        pe += resource_section
        assert len(pe) - len(resource_section) == HEADER_SIZE
    return pe


def _resource_directory(entries: list[tuple[int, int]]) -> bytes:
    header = struct.pack("<IIHHHH", 0, 0, 0, 0, 0, len(entries))
    body = b"".join(struct.pack("<II", name_or_id, offset_to_data) for name_or_id, offset_to_data in entries)
    return header + body


def build_version_resource_section(resource_type_id: int = 16) -> bytes:
    """Build a ".rsrc" section containing a 3-level resource directory
    (type -> name -> language) with a single leaf resource of the given
    type ID. When `resource_type_id` is RT_VERSION (16, the default) the
    leaf's data is a minimal but valid VS_VERSIONINFO blob; otherwise it
    is unused filler, letting tests build a resource section that has no
    RT_VERSION entry at all.
    """
    root_offset, name_offset, lang_offset, data_entry_offset, version_offset = 0, 24, 48, 72, 88

    root_dir = _resource_directory([(resource_type_id, name_offset | 0x80000000)])
    name_dir = _resource_directory([(1, lang_offset | 0x80000000)])
    lang_dir = _resource_directory([(0x409, data_entry_offset)])

    fixed_file_info = struct.pack("<I", 0xFEEF04BD) + b"\x00" * 48
    assert len(fixed_file_info) == 52
    body = VS_VERSION_INFO_KEY + b"\x00\x00" + fixed_file_info  # pad key to 4-byte boundary
    version_data = struct.pack("<HHH", 6 + len(body), len(fixed_file_info), 0) + body

    resource_rva = HEADER_SIZE
    data_entry = struct.pack("<IIII", resource_rva + version_offset, len(version_data), 0, 0)

    section = root_dir + name_dir + lang_dir + data_entry + version_data
    assert len(section) == version_offset + len(version_data)
    return section
