#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
from typing import BinaryIO
import struct
import autofield as AF


class SizedRecord:
    def __init__(self, bytedata):
        self._buffer = memoryview(bytedata)

    @classmethod
    def from_file(cls, f: BinaryIO, format_or_type) -> "SizedRecord":
        def get_record_size() -> int:
            return (
                struct.calcsize(format_or_type)
                if isinstance(format_or_type, str)
                else format_or_type.buffer_size
            )

        def read_unpack(fmt="<i"):
            s = struct.Struct(fmt)
            tup = s.unpack(f.read(s.size))
            return tup[0] if len(tup) == 1 else tup

        size = get_record_size() * read_unpack("<i")
        return cls(f.read(size))

    def iter_as(self, format_or_type):
        def get_record_size() -> int:
            return (
                struct.calcsize(format_or_type)
                if isinstance(format_or_type, str)
                else format_or_type.buffer_size
            )

        for offset in range(0, len(self._buffer)):
            size = get_record_size()
            end = offset + size
            yield (
                struct.unpack_from(format_or_type, self._buffer[offset:end])
                if isinstance(format_or_type, str)
                else format_or_type(self._buffer[offset:end])
            )


class Point(AF.Buffer):
    _fields = [
        ("<d", "x"),
        ("d", "y"),
    ]


class PolyHeader(AF.Buffer):
    _fields = [
        ("<i", "file_code"),
        (Point, "min"),
        (Point, "max"),
        ("i", "num_polys"),
    ]


if __name__ == "__main__":
    from writepolys import write_polys, polys

    write_polys("polys.bin", polys)
    with open("polys.bin", "rb") as f:
        poly_header = PolyHeader.from_file(f)
        num_polys = poly_header.num_polys
        records = [SizedRecord.from_file(f, "<dd") for _ in range(num_polys)]
        print(records)
