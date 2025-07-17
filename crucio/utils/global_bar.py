import time

from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn, TimeRemainingColumn, SpinnerColumn, \
    TaskProgressColumn, Task, ProgressColumn
from rich.text import Text

console = Console()
progress = Progress(
    SpinnerColumn(),
    TextColumn("{task.description}"),
    BarColumn(),
    TextColumn("{task.completed}/{task.total}"),
    "•",
    TextColumn("[bold blue]{task.percentage:>3.0f}%"),
    TimeElapsedColumn(),
    '~',
    TimeRemainingColumn(),
    console=console
)
progress.start()


def rqdm(x, desc=""):
    task = progress.add_task(desc, total=len(x))
    for i in x:
        yield i
        progress.update(task, advance=1)
    progress.remove_task(task)
    progress.refresh()


class RichBar:
    def __init__(self, x, total=0, desc=""):
        self.x = iter(x)
        self.task = progress.add_task(desc, total=total)

    def close(self):
        progress.remove_task(self.task)
        progress.refresh()

    def inc(self, advance=1):
        progress.update(self.task, advance=advance)

    def __iter__(self):
        for i in self.x:
            yield i
            self.inc()
        self.close()

import sys
import termios

def restore_terminal():
    fd = sys.stdin.fileno()
    termios.tcsetattr(fd, termios.TCSADRAIN, termios.tcgetattr(fd))
    print("\033[?25h", end="", flush=True)
def stop():
    progress.stop()
    restore_terminal()


from rich.progress import TaskID
from typing import Optional


class TaskProgress:
    def __init__(self, total: int = 0, initial_description: str = "start..."):
        self.task_id: Optional[TaskID] = None
        self.total = total
        self.initial_description = initial_description
        self.current = 0

    def __enter__(self):
        self.task_id = progress.add_task(self.initial_description, total=self.total)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        progress.remove_task(self.task_id)

    def update_task(self, description: str):
        progress.update(self.task_id, description=f"[cyan]{description}")
        progress.refresh()

    def advance(self, step: int = 1, description: Optional[str] = None):
        global progress
        if description:
            self.update_task(description)
        progress.advance(self.task_id, step)
        self.current += step
        if self.current >= self.total:
            progress.update(self.task_id, total=self.current)

    def set_current(self, current):
        self.current = current
        progress.update(self.task_id, completed=self.current)
        progress.refresh()

    def set_total(self, new_total: int):
        global progress
        progress.update(self.task_id, total=new_total)
        progress.refresh()


if __name__ == '__main__':
    with TaskProgress(total=100) as tp:
        for i in range(100):
            tp.set_current(i+1)
            time.sleep(1)
