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

        nrecords = f.read(struct.calcsize("<i"))
        size = get_record_size() * nrecords
        cls(f.read(size))

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


if __name__ == "__main__":
    from writepolys import write_polys, polys

    write_polys("polys.bin", polys)
    with open("polys.bin", "rb") as f:
        poly_header = AF.PolyHeader.from_file(f)
        num_polys = poly_header.num_polys
        records = [SizedRecord.from_file(f, "<dd") for _ in num_polys]
        print(records)
