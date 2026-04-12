#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
from typing import Any, Iterator, Type, cast
from typing import Union
from typing import BinaryIO
import struct
import autofield as AF


class SizedRecord:
    def __init__(self, bytedata: Union[bytes, memoryview]):
        self._buffer = memoryview(bytedata)

    @staticmethod
    def calc_record_size(format_or_type: AF.FormatOrBuffer) -> int:
        # Do not read the file
        return (
            struct.calcsize(format_or_type)
            if isinstance(format_or_type, str)
            else format_or_type.buffer_size
        )

    @classmethod
    def from_file(cls, f: BinaryIO, format_or_type: AF.FormatOrBuffer) -> "SizedRecord":
        def read_unpack(fmt="<i") -> Any:
            s = struct.Struct(fmt)
            tup = s.unpack(f.read(s.size))
            return tup[0] if len(tup) == 1 else tup

        size = SizedRecord.calc_record_size(format_or_type) * read_unpack("<i")
        return cls(f.read(size))

    def iter_as(
        self, format_or_type: Union[str, Type["AF.Buffer"]]
    ) -> Iterator[AF.Buffer]:
        size = SizedRecord.calc_record_size(format_or_type)
        for offset in range(0, len(self._buffer), size):
            end = offset + size
            chunk = self._buffer[offset:end]
            if isinstance(format_or_type, str):
                yield struct.unpack_from(format_or_type, chunk)  # type: ignore[misc]
            else:
                yield format_or_type(chunk)


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
        for rec in records:
            # for dd in rec.iter_as("<dd"):
            for dd in rec.iter_as(Point):
                print(dd.as_tuple())
