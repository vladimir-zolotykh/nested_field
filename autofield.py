#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
import os
from typing import BinaryIO, ClassVar, cast, Any
from typing import Union, Type, Protocol, runtime_checkable

from struct import Struct, calcsize
import logging

LOGFILENAME = f".{os.path.splitext(os.path.basename(__file__))[0]}.log"


@runtime_checkable
class BufferProtocol(Protocol):
    buffer_size: ClassVar[int]

    def __call__(self, bytedata: Union[bytes, memoryview]) -> Any:
        pass


BufferType = Type["Buffer"]
FormatOrBuffer = Union[str, BufferType]


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
    def __init__(self, format_or_type: FormatOrBuffer, offset: int):
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
        # when we get here, self.format_or_type is of type Buffer
        cls_type = cast(Type["Buffer"], self.format_or_type)
        logger = get_logger(self.__class__.__name__, LOGFILENAME)
        logger.info(f"{owner.buffer_size = }, {cls_type.buffer_size = }")
        buffer_slice = slice(self.offset, self.offset + cls_type.buffer_size)
        field: Buffer = cls_type(instance._buffer[buffer_slice])
        setattr(instance, self.name, field)
        return field


class Nested(Field):
    pass


class AutoField(type):
    def __init__(cls, clsname, bases, clsdict, **kwargs):
        fields = getattr(cls, "_fields", [])
        offset = 0
        for format_or_cls, attr in fields:
            if isinstance(format_or_cls, type) and issubclass(format_or_cls, Buffer):
                buffer_cls = format_or_cls
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
    _fields: ClassVar[list[tuple[FormatOrBuffer, str]]] = []
    buffer_size: ClassVar[int] = 0

    def __init__(self, bytedata):
        self._buffer = memoryview(bytedata)

    def as_tuple(self) -> tuple[str, ...]:
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
