from typing import NoReturn, Iterable, Any

import time, click

PROGRESS_BAR_WIDTH = 40
PROGRESS_BAR_CHAR = "#"
PROGRESS_BAR_START = "["
PROGRESS_BAR_END = "]"

def error(msg: str, start: str = "") -> NoReturn:
    click.secho(f"{start}Error: {msg}", err=True, fg="red")
    exit(1)

def warning(msg: str, start: str = "") -> None:
    click.secho(f"{start}Warning: {msg}", fg="yellow")

def as_int(based: str) -> int:
    if based[:2].lower() == "0x":
        return int(based[2:], 16)
    elif based[:1].lower() == "x":
        return int(based[1:], 16)
    elif based[:1] == "0":
        return int(based, 8)
    return int(based, 10)

def as_time(seconds: float) -> str:
    if seconds < 60:
        return "{:0.2f}s".format(seconds)
    else:
        return "{:d}m {:d}s".format(int(seconds // 60), int(seconds % 60))

class progress:
    def __init__(self, iterable: Iterable) -> None:
        self.iterable = iter(iterable)
        self.current = 0
        self.len = sum(1 for _ in iter(iterable))
        self.ratio = -1
        self.start = time.time()

    def bar(self, ratio):
        delta = time.time() - self.start
        bar = int(PROGRESS_BAR_WIDTH * ratio)
        s = "\x1b[2K\r" + PROGRESS_BAR_START
        s += PROGRESS_BAR_CHAR * bar
        s += " " * (PROGRESS_BAR_WIDTH - bar)
        s += PROGRESS_BAR_END
        s += f" {str(int(ratio * 100)).rjust(3, " ")}%"
        if 0 < ratio and ratio < 1:
            s += f" | ETA: {as_time(delta / ratio - delta)}"
        elif ratio == 1:
            s += f" | Finished in {as_time(delta)}"

        click.echo(s, nl=False)

    def __iter__(self) -> Any:
        return self
    
    def __next__(self) -> Any:
        try:
            nval = next(self.iterable)
            ratio = (self.current / (self.len - 1)) if self.len > 1 else 1
            if (ratio != self.ratio):
                self.ratio = ratio
                self.bar(self.ratio)
            self.current += 1
            return nval
        except StopIteration:
            self.bar(1)
            click.echo("")
            raise StopIteration
