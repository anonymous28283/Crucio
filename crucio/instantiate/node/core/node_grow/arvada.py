import random

from crucio.data_types import Grammar
from crucio.instantiate.node.core import SyntaxNode
from crucio.instantiate.node.core.node_grow import SyntaxNodeGrower


class ArvadaSNG(SyntaxNodeGrower):
    def __init__(self, grammar: Grammar, maxDepth) -> None:
        super().__init__(grammar)
        self.__maxDepth = maxDepth

    def __grow(self, node: SyntaxNode, depth=0):
        if node.isTerminal():
            return node
        prods = list(self._grammar.getProds(node.getSymbol().getValue()))
        if depth >= self.__maxDepth:
            terminalProds = [prod for prod in prods if prod.isTerminalProd()]
            if len(terminalProds) > 0:
                prods = terminalProds
        randomProd = random.choice(prods)
        node.produce(randomProd)
        children = list(node.getChildren())
        for child in children:
            self.__grow(child, depth + 1)
        return node

    def grow(self, node: SyntaxNode) -> SyntaxNode:
        return self.__grow(node)
