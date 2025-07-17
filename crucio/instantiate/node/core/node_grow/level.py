from itertools import product
from typing import List, Set, Optional, Tuple

from crucio.data_types import Grammar, Symbol
from crucio.instantiate.node.core import SyntaxNode
from crucio.instantiate.node.core.node_grow.static_grow import StaticSNG


class LevelSNG:
    def __init__(self, grammar: Grammar, maxLevel=1) -> None:
        self._grammar = grammar
        self.__terminateSNG = StaticSNG(grammar)
        self.__maxLevel = maxLevel

    def __permutate(self, node: SyntaxNode, childGrowsList: List[List[SyntaxNode]]):
        ret = []
        for i in [list(combination) for combination in product(*childGrowsList)]:
            nodeCopied = node.copy()
            nodeCopied.setChildren(i)
            ret.append(nodeCopied)
        return ret

    def __grow(self, node: SyntaxNode, level=0, mask: Set = set()) -> List[SyntaxNode]:
        # 此处我们添加一个：如果node是部分已生长的，我们不会试图去改变。
        if node.isTerminal():
            return [node]
        if level >= self.__maxLevel:
            return [self.__terminateSNG.grow(node)]
        ret = []
        prods = self._grammar.getProds(node.getSymbol().getValue())
        if node.getProd() is not None:
            prods = [node.getProd()]
        for prod in prods:
            # 避免递归：s -> n0 -> s
            if prod in mask:
                continue
            nextLevel = level + 1
            # 单nt的prod不增加level
            if prod.isSingleNt():
                mask.add(prod)
                nextLevel = level
            nodeCopied = node.copy()
            if nodeCopied.getProd() is None:
                nodeCopied.produce(prod)
            childGrowsList = []
            for child in nodeCopied.getChildren():
                childGrows = self.__grow(child, nextLevel)
                childGrowsList.append(childGrows)
            ret += self.__permutate(nodeCopied, childGrowsList)
            if prod.isSingleNt():
                mask.remove(prod)
        return ret

    def grow(self, node: Optional[SyntaxNode] = None) -> Tuple[SyntaxNode, ...]:
        # 为了避免n0 -> n1 -> n2 .. nk导致的深度损失从而无法测试到较深层次
        # 我们增加了优化：当产生式为单nt时，不增加深度，但是为了避免递归，我们添加__mask来避免
        if node is None:
            node = SyntaxNode(Symbol(self._grammar.getStart()))
        return tuple(self.__grow(node))
