#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
import os
from typing import BinaryIO
from struct import Struct, calcsize
import logging

LOGFILENAME = f".{os.path.splitext(os.path.basename(__file__))[0]}.log"


def get_logger(
    name,
    logfilename: str,
    loglevel=logging.DEBUG,
    logformat="%(levelname)s: %(name)s %(message)s",
    filemode: str = "w",
    datefmt="%H:%M:%S",
):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(loglevel)
    logger.propagate = True
    handler = (
        logging.FileHandler(logfilename, mode=filemode)
        if logfilename is not None
        else logging.StreamHandler()
    )
    formatter = logging.Formatter(logformat, datefmt=datefmt)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


class Field:
    def __init__(self, format_or_type, offset: int):
        self.offset: int = offset
        self.format_or_type = format_or_type
        self.struct = (
            Struct(format_or_type) if isinstance(format_or_type, str) else None
        )

    def __set_name__(self, owner: object, name: str):
        self.name = name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        if self.struct:
            r = self.struct.unpack_from(instance._buffer, self.offset)
            return r[0] if len(r) == 1 else r
        logger = get_logger(self.__class__.__name__, LOGFILENAME)
        logger.info(f"{owner.buffer_size = }, {self.format_or_type.buffer_size = }")
        buffer_slice = slice(self.offset, self.offset + self.format_or_type.buffer_size)
        field: Buffer = self.format_or_type(instance._buffer[buffer_slice])
        setattr(instance, self.name, field)
        return field


class Nested(Field):
    pass


class AutoField(type):
    def __init__(cls, clsname, bases, clsdict, **kwargs):
        fields = getattr(cls, "_fields", [])
        offset = 0
        for format_or_cls, attr in fields:
            if isinstance(format_or_cls, AutoField):
                buffer_cls: Buffer = format_or_cls
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

    def as_tuple(self):
        return tuple(getattr(self, tup[1]) for tup in self._fields)

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
    assert ph.min.as_tuple() == (0.5, 0.5)
    assert ph.max.as_tuple() == (7.0, 9.2)
    assert ph.num_polys == 3


if __name__ == "__main__":
    import writepolys

    writepolys.write_polys("polys.bin", writepolys.polys)
    f = open("polys.bin", "rb")
    ph = PolyHeader.from_file(f)
    print(f"{ph.file_code:x}")
    print(ph.min.as_tuple())
    print(ph.max.as_tuple())
    print(ph.num_polys)
