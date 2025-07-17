from abc import abstractmethod
from typing import Tuple, Sequence, List

from crucio.data_types import Grammar, Symbol, Context
from crucio.instantiate.node.core import SyntaxNode
from crucio.instantiate.node.core.node_grow import SyntaxNodeGrower
from crucio.instantiate.node.core.node_grow.arvada import ArvadaSNG
from crucio.instantiate.node.core.node_grow.level import LevelSNG
from crucio.instantiate.node.core.node_grow.rand_grow import RandomizedSNG
from crucio.instantiate.node.core.node_grow.static_grow import StaticSNG
from crucio.tokenize import Token, TokenizedContext, Tokens


class SymbolInstantiator:
    def __init__(self, grammar: Grammar) -> None:
        self._grammar = grammar
        self._tmpUsage = None

    @abstractmethod
    def instantiateSymbol(self, symbol: Symbol) -> Tuple[Token]:
        pass

    def instantiateNt(self,nt:str=None) -> Tuple[Token]:
        if nt is None:
            nt = self._grammar.getStart()
        return self.instantiateSymbol(Symbol(nt))

    def instantiate(self, symbols: Sequence[Symbol]) -> Tuple[Token]:
        ret = ()
        for symbol in symbols:
            ret = ret + self.instantiateSymbol(symbol)
        return ret

    def instantiateContext(self, context: Context) -> TokenizedContext:
        tokenizedPrefix = self.instantiate(context.getPrefix())
        tokenizedSuffix = self.instantiate(context.getSuffix())
        return TokenizedContext(tokenizedPrefix, tokenizedSuffix)

    def getGrammar(self) -> Grammar:
        return self._grammar


class StaticSymbolInstantiator(SymbolInstantiator):
    def __init__(self, grammar: Grammar) -> None:
        super().__init__(grammar)
        self.__ssng = StaticSNG(grammar)

    def instantiateSymbol(self, symbol: Symbol) -> Tuple[Token,...]:
        return self.__ssng.grow(SyntaxNode(symbol)).toTokens()


class SngSymbolInstantiator(SymbolInstantiator):
    def __init__(self, sng: SyntaxNodeGrower) -> None:
        super().__init__(sng.getGrammar())
        self.__sng = sng

    def instantiateSymbol(self, symbol: Symbol) -> Tokens:
        while True:
            try:
                return self.__sng.grow(SyntaxNode(symbol)).toTokens()
            except RecursionError:
                continue


class RandomizedSymbolInstantiator(SngSymbolInstantiator):
    def __init__(self, grammar: Grammar, maxDepth=20, maxProdUse=3) -> None:
        super().__init__(RandomizedSNG(grammar))


class ArvadaSymbolInstantiator(SngSymbolInstantiator):
    def __init__(self, grammar: Grammar) -> None:
        super().__init__(ArvadaSNG(grammar, 4))
        # 之前的论文是用的5,因为它们是从start出发，而我们从start产生的那个非终结符出发，所以此处需要减少1


class LevelSymbolInstantiator:
    def __init__(self, si: SymbolInstantiator, maxLevel: int = 1) -> None:
        self.__lsng = LevelSNG(si.getGrammar(), maxLevel)

    def instantiate(self, symbol: Symbol) -> List[Tokens]:
        ret = []
        for node in self.__lsng.grow(SyntaxNode(symbol)):
            ret.append(node.toTokens())
        return ret


class MinSymbolInstantiator(SymbolInstantiator):
    def __init__(self, grammar: Grammar):
        super().__init__(grammar)
        self.__lenTbl = {}
        self.__initLen()
        self.__tbl = {}
        self.__initTable()

    def __isSymbolsInstantiable(self, symbols: Tuple[Symbol]):
        for symbol in symbols:
            if symbol.isTerminal():
                continue
            if not symbol.getValue() in self.__tbl:
                return False
        return True

    def __initTable(self):
        updated = True
        while updated:
            updated = False
            for nt in self._grammar.getNts().difference(self.__tbl.keys()):
                for prod in self._grammar.getProds(nt):
                    if not self.__isSymbolsInstantiable(prod.getSymbols()):
                        continue
                    if self.__lenTbl[nt] != self.__len(prod.getSymbols()):
                        continue
                    self.__tbl[nt] = self.instantiate(prod.getSymbols())
                    updated = True
        # print(self.__tbl)

    def __initLen(self):
        for nt in self._grammar.getNts():
            self.__lenTbl[nt] = float('inf')
        updated = True
        while updated:
            updated = False
            for prod in self._grammar.getProds():
                if self.__lenTbl[prod.getNt()] > self.__len(prod.getSymbols()):
                    self.__lenTbl[prod.getNt()] = self.__len(prod.getSymbols())
                    updated = True
        # print(self.__lenTbl)

    def __len(self, symbols: Tuple[Symbol]) -> int:
        ret = 0
        for symbol in symbols:
            if symbol.isTerminal():
                ret += 1
            else:
                ret += self.__lenTbl[symbol.getValue()]
        return ret

    def instantiateSymbol(self, symbol: Symbol) -> Tuple[Token]:
        if symbol.isTerminal():
            return (symbol.getValue(),)
        if symbol.getValue() not in self.__tbl:
            raise Exception("symbol {} does not exist,grammar is \n{}".format(symbol.getValue(), self._grammar))
        return self.__tbl[symbol.getValue()]
