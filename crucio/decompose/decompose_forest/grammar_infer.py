from typing import Optional

from crucio.decompose.strategy.RemoveBlock import BinaryRemoveBlockDecomposer, RemoveBlockDecomposer
from crucio.decompose.strategy.SubSeq import SubSeqDecomposer
from crucio.utils.statistics import timer, counting
from crucio.decompose.decompose_forest.search import ForestSearcher
from crucio.data_types.learn_teach import Teacher


class DeForestTeacher(Teacher):
    def __init__(self, searcher: ForestSearcher):
        self.searcher = searcher

    @timer('produce generalize example')
    def teach(self, learner) -> Optional:
        return self.searcher.search(learner.understand)


def de_func(example, oracle):
    brb = BinaryRemoveBlockDecomposer()
    for i in brb.decompose(example):
        start = oracle.raw().calls
        if oracle.parse(i):
            counting('decompose', oracle.raw().calls-start)
            yield i
        else:
            counting('decompose', oracle.raw().calls - start)
    rb = RemoveBlockDecomposer()
    for i in rb.decompose(example):
        start = oracle.raw().calls
        if oracle.parse(i):
            counting('decompose', oracle.raw().calls-start)
            yield i
        else:
            counting('decompose', oracle.raw().calls - start)
    ssb = SubSeqDecomposer()
    for i in ssb.decompose(example):
        start = oracle.raw().calls
        if oracle.parse(i):
            counting('decompose', oracle.raw().calls-start)
            yield i
        else:
            counting('decompose', oracle.raw().calls - start)
