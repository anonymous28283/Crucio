from abc import abstractmethod

from crucio.data_types import Grammar
from crucio.instantiate.node.core import SyntaxTree


class ContextTreeGrower:
    def __init__(self, grammar: Grammar):
        self._grammar = grammar

    @abstractmethod
    def get(self, nt: str) -> SyntaxTree:
        pass
