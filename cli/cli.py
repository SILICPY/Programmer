#!/usr/bin/env python

from math import log2, ceil
import click

from datatypes import *
from util import error, warning, as_int

@click.group()
@click.option("--ic", "-c", type=click.Choice(BaseIC), required=True, help="The IC type used.")
@click.option("--port", "-d", type=NamedStr("port"), help="Serial port the programmer is connected to.")
@click.option("--range", "-r", type=CtxStr("range"), help="The address range to work with. Format: {start}.{end}")
def cli(ic: BaseIC, port: str, range: CtxStr) -> None:
    """Perform operations on ROM IC"""

    Context.ic = ic

    if range:
        if len((split := range.value.split("."))) != 2:
            range.fail(f"{range.value} is not a valid range.")

        try:
            if split[0]: Context.range[0] = as_int(split[0])
            if split[1]: Context.range[1] = as_int(split[1])
        except ValueError:
            range.fail(f"{range.value} contains non-integer values.")

        if not Context.range[0] < Context.range[1]:
            range.fail(f"Range has to be bigger than zero.")
        if not Context.range[0] < Context.ic.size:
            range.fail(f"Rtart of range has to be in address space of ROM IC.")
        if Context.ic.size < Context.range[1]:
            Context.range[1] = Context.ic.size
            warning("Truncated range to match size of ROM IC.")
    else:
        Context.range[1] = Context.ic.size

    SerDev.connect(port)
    Context.ic.init()

@cli.group(chain=True)
@click.argument("file", type=click.File("rb"))
@click.option("--offset", "-o", type=BasedInt("offset"), help="Skip first OFFSET bytes of file.")
def file(file: str, offset: int) -> None:
    Context.file = file.read()[offset:]
    if len(Context.file) < Context.range[1] - Context.range[0]:
        warning("Truncated range to match file size.")
        Context.range[1] = Context.range[0] + len(Context.file)

@file.command()
def write() -> None:
    click.echo("Writing")
    Context.ic.write(Context.range, Context.file)

@file.command()
def verify() -> None:
    def callback(addr, data):
        fdata = Context.file[addr - Context.range[0]]
        if data != fdata:
            warning(f"Mismatch in byte 0x{hex(addr)[2:].zfill(ceil(log2(Context.ic.size) // 4))}: should be 0x{hex(fdata)[2:].zfill(2)}, got 0x{hex(data)[2:].zfill(2)}.", start = "\x1b[2K\r")

    click.echo("Verifying")
    Context.ic.read(Context.range, callback)

@cli.command()
def read() -> None:
    def callback(addr, data):
        click.echo(f"\x1b[2K\r0x{hex(addr)[2:].zfill(ceil(log2(Context.ic.size) / 4))}: 0x{hex(data)[2:].zfill(2)}")

    click.echo("Reading")
    Context.ic.read(Context.range, callback)

@cli.command()
def erase() -> None:
    click.echo("Erasing")
    Context.ic.erase(Context.range)

if __name__ == "__main__":
    try:
        cli()
    except Exception as e:
        raise e
    finally:
        if SerDev.is_connected():
            BaseIC.init()
            SerDev.close()
