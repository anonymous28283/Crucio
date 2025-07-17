from typing import Dict, Tuple

from crucio.data_types import Grammar, Prod
from crucio.instantiate.node.core import SyntaxTree
from crucio.instantiate.node.core.context_grow import ContextTreeGrower
from crucio.instantiate.node.core.node_grow.min_grow import MinSNG


class MinCTG(ContextTreeGrower):
    def get(self, nt: str) -> SyntaxTree:
        st = SyntaxTree(self._grammar.getStart(),self._grammar)
        node = st.getRoot()
        for prod, index in self.__action[nt]:
            node.produce(prod)
            node = node.getChildren()[index]
        for freeNode in st.getFreeNodes():
            if freeNode is node:
                continue
            self.__sng.grow(freeNode)
        return st

    def __init__(self, grammar: Grammar):
        super().__init__(grammar)
        self.__sng = MinSNG(grammar)
        self.__action: Dict[str, Tuple[Tuple[Prod, int], ...]] = {grammar.getStart(): ()}
        self.__len: Dict[str, int] = {grammar.getStart(): 0}
        # action:(prod,index)
        # prod表示选取的产生式，index表示接下来的节点是该prod的第几个节点
        self.__initTbl()

    def __estimateLen(self, prod, x):
        y = self.__len[prod.getNt()]
        y += self.__sng.len(prod.getSymbols()[:x] + prod.getSymbols()[x + 1:])
        return y

    def __initTbl(self):
        updated = True
        while updated:
            updated = False
            for nt in set(self.__len.keys()):
                for prod in self._grammar.getProds(nt):
                    for i in range(len(prod)):
                        symbol = prod.getSymbols()[i]
                        if symbol.isTerminal():
                            continue
                        estimateLen = self.__estimateLen(prod, i)
                        if estimateLen < self.__len.get(symbol.getValue(), float('inf')):
                            self.__len[symbol.getValue()] = estimateLen
                            self.__action[symbol.getValue()] = self.__action[nt] + ((prod, i),)
                            updated = True
