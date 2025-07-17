from abc import abstractmethod
from typing import Optional

from crucio.data_types import Grammar
from crucio.instantiate.node.core import SyntaxNode


class SyntaxNodeGrower:
    def __init__(self, grammar: Grammar) -> None:
        self._grammar = grammar

    @abstractmethod
    def grow(self, node: Optional[SyntaxNode] = None) -> SyntaxNode:
        pass

    def getGrammar(self):
        return self._grammar
