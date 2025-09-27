from collections.abc import Sequence

from datatypes import *
from util import progress

class SST39SF010(BaseIC):
    size = 0x20000
    
    @classmethod
    def erase(cls, addr_range: Sequence) -> None:
        SerDev.cmd(ERASE_SECTOR)

        first_sector = addr_range[0] // 4096
        last_sector = -(addr_range[1] // -4096)
        click.echo(f"Erasing sectors \
{first_sector} ({"0x{:05x}".format(first_sector * 4096)}) to \
{last_sector} ({"0x{:05x}".format(last_sector * 4096)}).")
        
        for sector in progress(range(first_sector, last_sector)):
            SerDev.data(sector)
            SerDev.read()

class SST39SF020(SST39SF010):
    size = 0x40000

class SST39SF040(SST39SF010):
    size = 0x80000

class AT28C64(BaseIC):
    size = 0x2000

class AT28C256(BaseIC):
    size = 0x8000

    @classmethod
    def write(cls, addr_range: Sequence, file: Sequence) -> None:
        chnkend = (addr_range[1] // 256) * 256
        iterator = progress(range(addr_range[0], addr_range[1]))

        SerDev.cmd(PAGE_WRITE)

        addr = addr_range[0]
        while True:
            if addr == chnkend:
                break
            elif addr == addr_range[0] or not addr % 256:
                SerDev.addr(addr)
            next(iterator)
            SerDev.data(file[addr - addr_range[0]])
            if addr % 256 == 255:
                SerDev.read()
            addr += 1

        super()._write([chnkend, addr_range[1]], file[chnkend-addr_range[0]:], iterator)
