#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
import autofield as AF


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


def test_nested():
    import writepolys

    writepolys.write_polys("polys.bin", writepolys.polys)
    f = open("polys.bin", "rb")
    ph = PolyHeader.from_file(f)
    assert ph.file_code == 0x1234
    assert ph.min.as_tuple() == (0.5, 0.5)
    assert ph.max.as_tuple() == (7.0, 9.2)
    assert ph.num_polys == 3


if __name__ == "__main__":
    import writepolys

    writepolys.write_polys("polys.bin", writepolys.polys)
    f = open("polys.bin", "rb")
    ph = AF.PolyHeader.from_file(f)
    print(f"{ph.file_code:x}")
    print(ph.min.as_tuple())
    print(ph.max.as_tuple())
    print(ph.num_polys)
# how to test:
# $ pytest run.py::test_nested -v
