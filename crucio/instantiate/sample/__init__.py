from abc import abstractmethod
from typing import Iterable

from data_types import Grammar
from Instantiate.Node.Core import SyntaxTree


class GrammarSampler:
    def __init__(self, grammar: Grammar) -> None:
        # 语法采样器
        self._grammar = grammar

    @abstractmethod
    def sample(self) -> Iterable[SyntaxTree]:
        pass

    def getGrammar(self):
        return self._grammar
