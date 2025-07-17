from abc import abstractmethod
from typing import Union

from crucio.data_types import Grammar, Clause, Context, Symbol
from crucio.instantiate.node.core.context_grow.min_grow import MinCTG
from crucio.instantiate.symbol.symbol_ins import MinSymbolInstantiator
from crucio.tokenize import Token
from crucio.utils.load_grammar import loadProd


class ContextInstantiator:
    def __init__(self, grammar: Grammar) -> None:
        self._grammar = grammar

    @abstractmethod
    def instantiate(self, clauseOrNt: Union[str, Clause]) -> Context:
        pass


class RandomizedContextInstantiator(ContextInstantiator):
    def __initContextTable(self):
        updated = True
        while updated:
            updated = False
            for nt in tuple(self.__ctbl.keys()):
                for prod in self._grammar.getRule(nt).getProds():
                    for i, symbol in enumerate(prod.getSymbols()):
                        if symbol.isTerminal():
                            continue
                        if symbol.getValue() in self.__ctbl:
                            continue
                        self.__ctbl[symbol.getValue()] = self.instantiate(prod.newClause(i, i + 1))
                        updated = True

    def __init__(self, grammar: Grammar) -> None:
        super().__init__(grammar)
        self.__ctbl = {grammar.getStart(): Context((), ())}
        self.__initContextTable()

    def instantiate(self, clauseOrNt: Union[str, Clause]) -> Context:
        if isinstance(clauseOrNt, str):
            if clauseOrNt not in self.__ctbl:
                raise Exception('%s\n\n not found %s' % (str(self._grammar), clauseOrNt))
            return self.__ctbl[clauseOrNt]
        if clauseOrNt.getNt() not in self.__ctbl:
            raise Exception('%s not found\n\n the grammar is %s' % (str(clauseOrNt.getNt()), str(self._grammar)))
        context = self.__ctbl[clauseOrNt.getNt()]
        prefix, suffix = context.getPrefix(), context.getSuffix()
        prefix1, suffix1 = clauseOrNt.getPrefix(), clauseOrNt.getSuffix()
        return Context(prefix + prefix1, suffix1 + suffix)


class MinContextInstantiator(ContextInstantiator):

    def __init__(self, grammar: Grammar) -> None:
        super().__init__(grammar)
        self.__mctg = MinCTG(grammar)
        self.__msi = MinSymbolInstantiator(grammar)

    def __getNtContext(self, nt: str):
        st = self.__mctg.get(nt)
        st.getFreeNodes()[0].produce(loadProd(f'{nt}: A12345'))
        tokens = st.toTokens()
        index = tokens.index(Token('A12345'))
        return Context(tuple(Symbol(i) for i in tokens[:index]), tuple(Symbol(i) for i in tokens[index + 1:]))

    def instantiate(self, clauseOrNt: Union[str, Clause]) -> Context:
        if isinstance(clauseOrNt, str):
            return self.__getNtContext(clauseOrNt)
        context = self.__getNtContext(clauseOrNt.getNt())
        prefix, suffix = context.getPrefix(), context.getSuffix()
        prefix1, suffix1 = clauseOrNt.getPrefix(), clauseOrNt.getSuffix()
        return Context(prefix + prefix1, suffix1 + suffix)
