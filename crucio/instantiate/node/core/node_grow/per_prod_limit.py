import random

from crucio.data_types import Grammar
from crucio.instantiate.node.core import SyntaxNode
from crucio.instantiate.node.core.node_grow import SyntaxNodeGrower
from crucio.instantiate.node.core.node_grow.static_grow import StaticSNG


class PerProdLimitSNG(SyntaxNodeGrower):
    def __init__(self, grammar: Grammar, maxProdUse=10) -> None:
        super().__init__(grammar)
        self.__terminateSNG = StaticSNG(grammar)
        self.__maxProdUse = maxProdUse

    def __grow(self, node: SyntaxNode):
        if node.isTerminal():
            return node
        forbiddenProds = [prod for prod in self.__prodUsage.keys() if self.__prodUsage[prod] >= self.__maxProdUse]
        prods = list(set(self._grammar.getProds(node.getSymbol().getValue())).difference(forbiddenProds))
        if len(prods) == 0:
            return self.__terminateSNG.grow(node)
        randomProd = random.choice(prods)
        if randomProd not in self.__prodUsage:
            self.__prodUsage[randomProd] = 0
        self.__prodUsage[randomProd] += 1
        node.produce(randomProd)
        for child in node.getChildren():
            self.__grow(child)
        return node

    def grow(self, node: SyntaxNode) -> SyntaxNode:
        self.__prodUsage = {}
        return self.__grow(node)
