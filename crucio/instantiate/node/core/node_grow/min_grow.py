import queue
from typing import List, Optional, Iterable

from crucio.data_types import Prod, Symbol, Grammar
from crucio.instantiate.node.core import SyntaxNode
from crucio.instantiate.node.core.node_grow import SyntaxNodeGrower


def sortProds(prods: List[Prod], msng: "MinSNG"):
    for i in range(len(prods)):
        for j in range(i + 1, len(prods)):
            l1 = msng.len(prods[i].getSymbols())
            l2 = msng.len(prods[j].getSymbols())
            if l1 > l2 or (l1 == l2 and not prods[i].isTerminalProd() and prods[j].isTerminalProd()):
                prods[i], prods[j] = prods[j], prods[i]


class MinSNG(SyntaxNodeGrower):
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

    def __init__(self, grammar: Grammar):
        super().__init__(grammar)
        self.__lenTbl = {}
        self.__initLen()
        self.__action = {}
        self.__initAction()

    def __isSymbolsInstantiable(self, symbols: Iterable[Symbol]):
        for symbol in symbols:
            if symbol.isTerminal():
                continue
            if not symbol.getValue() in self.__action:
                return False
        return True

    def __initAction(self):
        updated = True
        while updated:
            updated = False
            for nt in self._grammar.getNts().difference(self.__action.keys()):
                prods = list(self._grammar.getProds(nt))
                sortProds(prods, self)
                for prod in prods:
                    if not self.__isSymbolsInstantiable(prod.getSymbols()):
                        continue
                    if self.__lenTbl[nt] != self.len(prod.getSymbols()):
                        continue
                    self.__action[nt] = prod
                    updated = True
                    break
        # print(self.__tbl)

    def __initLen(self):
        for nt in self._grammar.getNts():
            self.__lenTbl[nt] = float('inf')
        updated = True
        while updated:
            updated = False
            for prod in self._grammar.getProds():
                if self.__lenTbl[prod.getNt()] > self.len(prod.getSymbols()):
                    self.__lenTbl[prod.getNt()] = self.len(prod.getSymbols())
                    updated = True
        # print(self.__lenTbl)

    def len(self, symbols: Iterable[Symbol]) -> int:
        ret = 0
        for symbol in symbols:
            if symbol.isTerminal():
                ret += 1
            else:
                ret += self.__lenTbl[symbol.getValue()]
        return ret
