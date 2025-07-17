import random

from data_types import Grammar
from Instantiate.Node.Core import SyntaxNode
from Instantiate.Node.Core.NodeGrow import SyntaxNodeGrower
from Instantiate.Node.Core.NodeGrow.Static import StaticSNG


class ProdLimitSNG(SyntaxNodeGrower):
    def __init__(self, grammar: Grammar, maxProdUsageRate=10) -> None:
        super().__init__(grammar)
        self.__maxProdUsage = int(maxProdUsageRate * len(list(grammar.getProds())))
        self.__terminateSNG = StaticSNG(grammar)

    def __grow(self, node: SyntaxNode):
        if node.isTerminal():
            return node
        if self.__prodUsage >= self.__maxProdUsage:
            return self.__terminateSNG.grow(node)
        prods = list(self._grammar.getProds(node.getSymbol().getValue()))
        randomProd = random.choice(prods)
        node.produce(randomProd)
        self.__prodUsage += 1
        children = list(node.getChildren())
        random.shuffle(children)
        for child in children:
            self.__grow(child)
        return node

    def grow(self, node: SyntaxNode) -> SyntaxNode:
        self.__prodUsage = 0
        return self.__grow(node)
