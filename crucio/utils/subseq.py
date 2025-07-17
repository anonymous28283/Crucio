import itertools
from typing import Sequence

from crucio.config import Config


def intervals_overlap(interval1, interval2):
    """
    check two intervals overlap
    """
    a, b = interval1
    c, d = interval2

    return not (b <= c or d <= a)


class SubSeqIterator:
    def __init__(self, seq: Sequence):
        self.__seq = seq
        self.__skip = False

    def __iter__(self):
        skipInt = []
        for l, r in sorted(itertools.combinations(range(len(self.__seq) + 1), 2), key=lambda x: x[0] - x[1],
                           reverse=Config.reverse):
            overlap = False
            for l1, r1 in skipInt:
                if intervals_overlap((l, r), (l1, r1)):
                    overlap = True
                    break
            if overlap:
                continue
            yield l,r
            if self.__skip:
                skipInt.append((l, r))
                self.__skip = False

    def skip(self):
        self.__skip = True
