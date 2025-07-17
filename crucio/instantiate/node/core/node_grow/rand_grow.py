import random
from collections import defaultdict
from typing import Optional

from crucio.data_types import Grammar, Symbol
from crucio.instantiate.node.core import SyntaxNode
from crucio.instantiate.node.core.node_grow import SyntaxNodeGrower
from crucio.instantiate.node.core.node_grow.static_grow import StaticSNG
from crucio.utils.statistics import counter


class RandomizedSNG(SyntaxNodeGrower):
    def __init__(self, grammar: Grammar, maxDepth=20, maxProdUse=3) -> None:
        super().__init__(grammar)
        self.__terminateSNG = StaticSNG(grammar)
        self.__maxDepth = maxDepth
        self.__maxProdUse = maxProdUse
        self.__prodUsage = {}
        self.__forbidden = set()

    @counter('grow')
    def __grow(self, node: SyntaxNode, depth=0):
        if node.isTerminal():
            return node
        if depth >= self.__maxDepth:
            return self.__terminateSNG.grow(node)

        prods = self._grammar.getProds(node.getSymbol().getValue())
        prods = [i for i in prods if i not in self.__forbidden]
        if len(prods) == 0:
            return self.__terminateSNG.grow(node)
        randomProd = random.choice(prods)
        self.__prodUsage[randomProd] += 1
        if self.__prodUsage[randomProd] >= self.__maxProdUse:
            self.__forbidden.add(randomProd)
        node.produce(randomProd)
        for child in node.getChildren():
            self.__grow(child, depth + 1)
        return node

    def grow(self, node: Optional[SyntaxNode] = None) -> SyntaxNode:
        if node is None:
            node = SyntaxNode(Symbol(self.getGrammar().getStart()))
        self.__prodUsage = defaultdict(int)
        self.__forbidden = set()
        return self.__grow(node)
