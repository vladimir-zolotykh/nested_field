#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
from typing import BinaryIO
from struct import Struct, calcsize


class Field:
    def __init__(self, format, offset):
        self.name = None
        self.offset = offset
        self.struct = Struct(format)

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        r = self.struct.unpack_from(instance._buffer, self.offset)
        return r[0] if len(r) == 1 else r


class Nested(Field):
    def __init__(self, field_type, offset):
        self.name = None
        self.offset = offset
        self.field_type = field_type

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        buffer_slice = slice(self.offset, self.offset + owner.buffer_size)
        field: Point | PolyHeader = self.field_type(instance._buffer[buffer_slice])
        setattr(instance, self.name, field)
        return field


class AutoField(type):
    def __init__(cls, clsname, bases, clsdict, **kwargs):
        fields = getattr(cls, "_fields", [])
        offset = 0
        for format_or_cls, attr in fields:
            if isinstance(format_or_cls, AutoField):
                buffer_cls: Point | PolyHeader = format_or_cls
                nested = Nested(buffer_cls, offset)
                nested.__set_name__(None, attr)
                setattr(cls, attr, nested)
                offset += buffer_cls.buffer_size
            elif isinstance(format_or_cls, str):
                format: str = format_or_cls
                field = Field(format, offset)  # a Descriptor
                field.__set_name__(None, attr)
                setattr(cls, attr, field)
                offset += calcsize(format)
            else:
                raise TypeError(f"{format_or_cls} must be Point, PolyHeader, or str")
        setattr(cls, "buffer_size", offset)


class Buffer(metaclass=AutoField):
    def __init__(self, bytedata):
        self._buffer = memoryview(bytedata)

    @classmethod
    def from_file(cls, f: BinaryIO):
        return cls(f.read(cls.buffer_size))


class Point(Buffer):
    _fields = [
        ("<d", "x"),
        ("d", "y"),
    ]


class PolyHeader(Buffer):
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
