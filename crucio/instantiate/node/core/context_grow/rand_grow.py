from typing import Dict, Tuple

from crucio.data_types import Grammar, Prod
from crucio.instantiate.node.core import SyntaxTree
from crucio.instantiate.node.core.context_grow import ContextTreeGrower
from crucio.instantiate.node.core.node_grow.static_grow import StaticSNG


class RandomizedCTG(ContextTreeGrower):
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
        self.__sng = StaticSNG(grammar)
        self.__action: Dict[str, Tuple[Tuple[Prod, int], ...]] = {grammar.getStart(): ()}
        # action:(prod,index)
        # prod表示选取的产生式，index表示接下来的节点是该prod的第几个节点
        self.__initTbl()

    def __initTbl(self):
        updated = True
        while updated:
            updated = False
            for nt in set(self.__action.keys()):
                for prod in self._grammar.getProds(nt):
                    for index, symbol in enumerate(prod):
                        if symbol.isTerminal():
                            continue
                        otherNt = symbol.getValue()
                        if otherNt in self.__action:
                            continue
                        self.__action[otherNt] = self.__action[nt] + ((prod, index),)
                        updated = True
