import itertools
import sys
from typing import Collection, List, Iterable

import numpy
import numpy as np

from crucio.utils.sub_con import Sub, Con
from crucio.oracle.extend.naive import NaiveExtendOracle
from crucio.oracle.tokenized import TokenizedOracle
from crucio.tokenize import TokenizedContext, Tokens
from crucio.utils.log import terminal, Logger
from crucio.utils.statistics import timer, timing, record


class DistributionalMatrix:
    @timer('distributional matrix build')
    def __init__(self, subseqs: Collection[Tokens], contexts: Collection[TokenizedContext], oracle: TokenizedOracle
                 ,logger:Logger = terminal):
        self._subseqs = list(subseqs)
        self._contexts = list(contexts)
        self._r = len(self._subseqs)
        self._c = len(self._contexts)
        self._mat = numpy.zeros((self._r, self._c), dtype=np.uint8)
        self._ms, self._msi, = buildMap(self._subseqs)
        self._mc, self._mci = buildMap(self._contexts)
        self.__oracle = oracle
        self.positives = set()
        examples = list({c.assembly(s) for s, c in itertools.product(self._subseqs, self._contexts)})
        logger.print('Size of examples',sys.getsizeof(examples))
        logger.print('examples=',len(examples))
        cache = NaiveExtendOracle(oracle).batch(examples,'distributional matrix build')
        x = timing('cache parse')
        for s, c in itertools.product(self._subseqs, self._contexts):
            if cache[c.assembly(s)]:
                self._mat[self._ms[s]][self._mc[c]] = 1
                self.positives.add(c.assembly(s))
        record(x)

    def getOracle(self):
        return self.__oracle

    def getSubseqByIndex(self, index: int) -> Tokens:
        return self._msi[index]

    def getSubseqByIndexes(self, indexes: Collection[int]) -> List[Tokens]:
        return [self.getSubseqByIndex(index) for index in indexes]

    def getContextByIndex(self, index: int) -> TokenizedContext:
        return self._mci[index]

    def getContextByIndexes(self, indexes: Collection[int]) -> List[TokenizedContext]:
        return [self.getContextByIndex(index) for index in indexes]

    def getIndexBySubseq(self, subseq: Tokens) -> int:
        return self._ms[subseq]

    def getContextWeight(self, index):
        return sum(self.getMatrix()[:, index])

    def getSubseqWeight(self, index: int):
        return sum(self.getMatrix()[index])

    def getIndexByContext(self, context: TokenizedContext) -> int:
        return self._mc[context]

    def getMatrix(self):
        return self._mat

    def getSubseqs(self):
        return self._subseqs

    def getContexts(self):
        return self._contexts

    @timer('distributional matrix build')
    def addContext(self, context: TokenizedContext):
        if context in self._mc:
            return
        # build map
        self._mc[context] = len(self._mc)
        self._mci[self._mc[context]] = context
        self._contexts.append(context)
        self._c += 1
        # build column
        newColumn = np.zeros((self._r, 1), dtype=np.uint8)
        for index, s in enumerate(self.getSubseqs()):
            if self.__oracle.parse(context.assembly(s)):
                newColumn[index] = 1
                self.positives.add(context.assembly(s))
        self._mat = np.append(self._mat, newColumn, axis=1)

    def addContexts(self, contexts: Collection[TokenizedContext]):
        for context in contexts:
            self.addContext(context)


    def addSubseq(self, subseq: Tokens):
        if subseq in self._ms:
            return
        self._ms[subseq] = len(self._ms)
        self._msi[self._ms[subseq]] = subseq
        self._subseqs.append(subseq)
        self._r += 1
        # 然后构造行
        newRow = np.zeros((1, self._c), dtype=np.uint8)
        for index, c in enumerate(self.getContexts()):
            if self.__oracle.parse(c.assembly(subseq)):
                newRow[0, index] = 1
                self.positives.add(c.assembly(subseq))
        self._mat = np.append(self._mat, newRow, axis=0)

    @timer('distributional matrix build')
    def addExample(self,example):
        subseqs = [i for i in Sub(example) if i not in self._ms]
        contexts = [i for i in Con(example) if i not in self._mc]
        examples = set()
        for sub in subseqs:
            for con in self._contexts+contexts:
                examples.add(con.assembly(sub))
        for sub in self._subseqs+subseqs:
            for con in contexts:
                examples.add(con.assembly(sub))
        cache = NaiveExtendOracle(self.__oracle).batch(examples,'distributional matrix construct')
        for subseq in subseqs:
            self._ms[subseq] = len(self._ms)
            self._msi[self._ms[subseq]] = subseq
            self._subseqs.append(subseq)
            self._r += 1
            # 然后构造行
            newRow = np.zeros((1, self._c), dtype=np.uint8)
            for index, c in enumerate(self.getContexts()):
                if cache[c.assembly(subseq)]:
                    newRow[0, index] = 1
                    self.positives.add(c.assembly(subseq))
            self._mat = np.append(self._mat, newRow, axis=0)
        for context in contexts:
            # 首先维护映射
            self._mc[context] = len(self._mc)
            self._mci[self._mc[context]] = context
            self._contexts.append(context)
            self._c += 1
            # 然后构造列
            newColumn = np.zeros((self._r, 1), dtype=np.uint8)
            for index, s in enumerate(self.getSubseqs()):
                if cache[context.assembly(s)]:
                    newColumn[index] = 1
                    self.positives.add(context.assembly(s))
            self._mat = np.append(self._mat, newColumn, axis=1)

    def addSubseqs(self, subseqs: Collection[Tokens]):
        for subseq in subseqs:
            self.addSubseq(subseq)


def buildMap(s: Iterable):
    m1 = {item: index for index, item in enumerate(s)}
    m2 = {v: k for k, v in m1.items()}
    return m1, m2

