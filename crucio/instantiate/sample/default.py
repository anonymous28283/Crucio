from typing import Iterable

from data_types import Grammar
from Instantiate.Sample import GrammarSampler
from Instantiate.Node.Core import SyntaxTree
from crucio.instantiate.node.core.node_grow.per_prod_limit import PerProdLimitSNG


class DefaultGrammarSampler(GrammarSampler):
    def __init__(self, grammar: Grammar, n: int, maxRetryRate: float = 10):
        super().__init__(grammar)
        self.__n = n
        self.__maxRetryRate = maxRetryRate

    def sample(self) -> Iterable[SyntaxTree]:
        sng = PerProdLimitSNG(self._grammar, 10)
        samples = set()
        maxRetry = self.__maxRetryRate * self.__n
        while len(samples) < self.__n and maxRetry > 0:
            st = SyntaxTree(self._grammar.getStart(), self._grammar)
            sng.grow(st.getRoot())
            samples.add(st)
            maxRetry -= 1
        return samples
