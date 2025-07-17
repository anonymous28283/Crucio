import queue
from typing import Optional

from crucio.data_types import Grammar, Symbol
from crucio.instantiate.node.core import SyntaxNode
from crucio.instantiate.node.core.node_grow import SyntaxNodeGrower


class StaticSNG(SyntaxNodeGrower):
    def __updateActionTable(self):
        for nt in self._grammar.getNts().difference(self.__action.keys()):
            for prod in self._grammar.getProds(nt):
                hasAction = True
                for symbol in prod:
                    if symbol.isTerminal():
                        continue
                    if symbol.getValue() not in self.__action:
                        hasAction = False
                        break
                if hasAction:
                    self.__action[nt] = prod
                    break

    def __initActionTable(self):
        while len(self.__action) < len(self._grammar.getNts()):
            actionLen = len(self.__action)
            self.__updateActionTable()
            if len(self.__action) == actionLen:
                raise Exception(f"Invalid Grammar:\n{self._grammar}\n\nNot Instantiated Symbols:{self._grammar.getNts().difference(self.__action.keys())}")

    def __init__(self, grammar: Grammar) -> None:
        super().__init__(grammar)
        self.__action = {}
        self.__initActionTable()

    def grow(self, node: Optional[SyntaxNode] = None) -> SyntaxNode:
        if node is None:
            node = SyntaxNode(Symbol(self.getGrammar().getStart()))
        if node.isTerminal():
            return node
        root = node
        growQueue = queue.Queue()
        growQueue.put(node)
        while not growQueue.empty():
            node = growQueue.get()
            node.produce(self.__action[node.getSymbol().getValue()])
            for child in node.getChildren():
                if not child.isTerminal():
                    growQueue.put(child)
        return root
