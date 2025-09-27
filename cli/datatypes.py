from typing import Sequence, Iterable, Self
from collections.abc import Sequence, Callable

import time, serial, click
import serial.tools.list_ports

from util import error, warning, as_int, progress

CMD_BYTE = 0x7E
BAUD_RATE = 500000

READ = 0x01
WRITE = 0x02
PAGE_WRITE = 0x03
ERASE_SECTOR = 0x04
ERASE_CHIP = 0x05

class NamedStr(click.ParamType):
    def __init__(self, name: str = "text") -> None:
        self.name = name

class CtxStr(NamedStr):
    def convert(self, value: str, param: click.Option, ctx: click.Context) -> Self:
        self.value, self.param, self.ctx = value, param, ctx
        return self
    def fail(self, error: str) -> None:
        super().fail(error, self.param, self.ctx)

class BasedInt(click.ParamType):
    def __init__(self, name: str = "integer") -> None:
        self.name = name

    def convert(self, value: str, param: click.Option, ctx: click.Context) -> int:
        if isinstance(value, int):
            return value
        try:
            return as_int(value)
        except ValueError:
           self.fail(f"{value!r} is not a valid integer.", param, ctx)

class Context:
    ic = None
    range = [0, -1]
    file = None

class SerDev:
    ser: serial.Serial = None

    @classmethod
    def connect(cls, port: str = None) -> None:
        # Auto-detect port. If multiple ports are available, the highest port number will be chosen.
        if not port:
            for avail in serial.tools.list_ports.comports(include_links=False):
                if avail.usb_device_path:
                    port = avail.device
                    break

        if not port:
            error(f"Failed auto-detect serial port.")

        try:
            cls.ser = serial.Serial(port, BAUD_RATE)
            time.sleep(1)
            if not cls.ser.is_open:
                raise serial.serialutil.SerialException
        except serial.serialutil.SerialException:
            error(f"Failed to open serial device at port '{port}'.")
        cls.ser.flushInput()

    @classmethod
    def close(cls) -> None:
        cls.ser.close()

    @classmethod
    def is_connected(cls) -> bool:
        return cls.ser is not None and cls.ser.is_open

    @classmethod
    def read(cls) -> None:
        return cls.ser.read(1)[0]

    @classmethod
    def data(cls, byte: int) -> None:
        if byte == CMD_BYTE:
            cls.ser.write(CMD_BYTE.to_bytes(1, "little"))
        cls.ser.write(byte.to_bytes(1, "little"))

    @classmethod
    def cmd(cls, cmd: int) -> None:
        cls.ser.write(CMD_BYTE.to_bytes(1, "little"))
        cls.data(cmd)

    @classmethod
    def ic(cls, ic: int) -> None:
        cls.cmd(ic | 0x80)
        time.sleep(0.01)

    @classmethod
    def addr(cls, data: int) -> None:
        b = data.to_bytes(4, "little")
        for byte in b:
            cls.data(byte)

class _MetaIC(type):
    _enum = 0
    _ic = []

    def __new__(cls, name: str, bases: tuple, attrs: dict) -> object:
        attrs["enum"] = __class__._enum
        obj = super().__new__(cls, name, bases, attrs)
        if "__name__" not in attrs:
            __class__._ic.append(obj)
        __class__._enum += 1
        return obj

    def __repr__(cls) -> str:
        return cls.__name__

    def __iter__(cls) -> object:
        return iter(__class__._ic)

class BaseIC(metaclass=_MetaIC):
    __name__ = "base"
    enum: int

    @classmethod
    def _read(cls, addr_range: Sequence, callback: Callable[[int, int], None], iterator: Iterable) -> None:
        SerDev.cmd(READ)
        SerDev.addr(addr_range[0])
        SerDev.addr(addr_range[1])
        for addr in iterator:
            callback(addr, SerDev.read())

    @classmethod
    def _write(cls, addr_range: Sequence, file: Sequence, iterator: Iterable) -> None:
        SerDev.cmd(WRITE)
        SerDev.addr(addr_range[0])
        for addr in iterator:
            SerDev.data(file[addr - addr_range[0]])
            if SerDev.read():
                error("IC doesn't support that operation.", start = "\x1b[2K\r")

    @classmethod
    def init(cls) -> None:
        SerDev.ic(cls.enum)

    @classmethod
    def read(cls, addr_range: Sequence, callback: Callable[[int, int], None]) -> None:
        cls._read(addr_range, callback, progress(range(addr_range[0], addr_range[1])))

    @classmethod
    def write(cls, addr_range: Sequence, file: Sequence) -> None:
        cls._write(addr_range, file, progress(range(addr_range[0], addr_range[1])))

    @classmethod
    def erase(cls, addr_range: Sequence) -> None:
        SerDev.cmd(ERASE_CHIP)
        if SerDev.read():
            error("IC doesn't support that operation.")

import ic
