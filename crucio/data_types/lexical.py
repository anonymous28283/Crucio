from dataclasses import dataclass
from typing import Tuple


@dataclass
class Segmentation:
    slices: Tuple

    def join(self):
        return ''.join(self.slices)

    def pretty(self):
        from colored import bg, attr
        colors = [bg("yellow"), bg("green")]
        ret = ''
        color_index = 0
        for value in self.slices:
            if value in {" ", "\n", '\t'}:
                ret += value
            else:
                ret += f"{colors[color_index]}{value}{attr('reset')}"
                color_index = 1 - color_index
        return ret
