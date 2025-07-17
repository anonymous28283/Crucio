import queue
from enum import Enum
from typing import Collection, FrozenSet, Generic, Iterable, List, Optional, Sequence, Set, Tuple, \
    TypeVar, Union, Dict

import lark
from colored import bg, attr
from lark.lexer import Lexer, Token as LarkToken

from crucio.config import Config
from crucio.instantiate.TokenIns import DefaultTokenInstantiator, TokenInstantiator
from crucio.oracle.string import LarkOracle, CachedStringOracle
from crucio.oracle.tokenized import TokenizedOracle
from crucio.tokenize import Token, Tokens
from crucio.utils.statistics import timer, counter


class SymbolType(Enum):
    Default = 0
    Rep0 = 1
    Rep1 = 2
    Opt = 3

    def __repr__(self):
        return 'SymbolType.%s' % self.name


T = TypeVar('T', bound=Union[str, Token])


class Symbol(Generic[T]):
    def __init__(self, value: T, symbolType: SymbolType = SymbolType.Default) -> None:
        self.__value = value
        self.__type = symbolType
        self.__isTerminal = isinstance(value, Token)

    def __repr__(self) -> str:
        return "symbol(%s,%s)" % (repr(self.getValue()), repr(self.getType()))

    def getValue(self) -> T:
        return self.__value

    def isTerminal(self) -> bool:
        return self.__isTerminal

    def getType(self) -> SymbolType:
        return self.__type

    def __hash__(self) -> int:
        return hash((self.__value, self.__type))

    def __lt__(self, other) -> bool:
        return isinstance(other, Symbol) and str(self) < str(other)

    def __str__(self) -> str:
        value = str(self.getValue())
        if self.getType() == SymbolType.Default:
            return value
        elif self.getType() == SymbolType.Opt:
            return "%s?" % value
        elif self.getType() == SymbolType.Rep0:
            return "%s*" % value
        elif self.getType() == SymbolType.Rep1:
            return "%s+" % value
        raise Exception()

    def pretty(self) -> str:
        value = repr(self.getValue().value) if self.isTerminal() else self.getValue()
        if self.getType() == SymbolType.Default:
            return value
        elif self.getType() == SymbolType.Opt:
            return "%s?" % value
        elif self.getType() == SymbolType.Rep0:
            return "%s*" % value
        elif self.getType() == SymbolType.Rep1:
            return "%s+" % value
        raise Exception()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Symbol):
            return False
        return self.getType() == other.getType() and self.getValue() == other.getValue()


Symbols = Tuple[Symbol[T], ...]


def symbols2str(symbols: Symbols):
    return ' '.join(map(str, symbols))


def symbols2strPretty(symbols: Symbols):
    return ' '.join(map(lambda x: x.pretty(), symbols))


def tokens2symbols(tokens: Iterable[Token]) -> Symbols:
    return tuple(Symbol(token) for token in tokens)


class Context(Generic[T]):
    def __init__(self, prefix: Symbols, suffix: Symbols) -> None:
        self.__prefix = tuple(prefix)
        self.__suffix = tuple(suffix)

    def getPrefix(self):
        return self.__prefix

    def getSuffix(self):
        return self.__suffix

    def assembly(self, symbols: Symbols) -> Symbols:
        return self.__prefix + tuple(symbols) + self.__suffix

    def __str__(self) -> str:
        return symbols2str(self.getPrefix()) + bg('blue') + ' ' + attr('reset') + symbols2str(self.getSuffix())

    def __eq__(self, other: object) -> bool:
        return isinstance(other,
                          Context) and self.getPrefix() == other.getPrefix() and self.getSuffix() == other.getSuffix()


class Prod(Generic[T]):
    def __init__(self, nt: T, symbols: Symbols) -> None:
        self.__nt = nt
        self.__symbols = tuple(symbols)
        self.__hashVal = hash((self.__nt, self.__symbols))

    def isTerminalProd(self) -> bool:
        if len(self) == 0:
            return True
        for symbol in self.__symbols:
            if not symbol.isTerminal():
                return False
        return True

    def getCharset(self):
        tokens = set()
        for symbol in self.__symbols:
            if symbol.isTerminal():
                tokens.add(symbol.getValue())
        return tokens

    def isSingleNt(self):
        return self.newClause().isSingleNt()

    def getValueNt(self) -> T:
        assert self.isSingleNt()
        return self[0].getValue()

    def getNt(self) -> T:
        return self.__nt

    def getSymbols(self) -> Symbols:
        return self.__symbols

    def __iter__(self):
        for symbol in self.getSymbols():
            yield symbol

    def __len__(self):
        return len(self.__symbols)

    def newClause(self, left: int = None, right: int = None) -> "Clause[T]":
        if left is None:
            left = 0
        if right is None:
            right = len(self)
        return Clause(self, left, right)

    def __repr__(self) -> str:
        return "Prod(%s,%s)" % (repr(self.getNt()), repr(self.getSymbols()))

    def clauses(self):
        for i in range(len(self)):
            for j in range(i + 1, len(self) + 1):
                yield self.newClause(i, j)

    def __hash__(self) -> int:
        return self.__hashVal

    def __lt__(self, other) -> bool:
        return (self.__nt, self.__symbols) < (other.__nt, other.__symbols)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Prod):
            return False
        return (self.__nt, self.__symbols) == (other.__nt, other.__symbols)

    def __str__(self) -> str:
        return '%s: %s' % (str(self.__nt), symbols2str(self.__symbols))

    def pretty(self):
        return '%s: %s' % (str(self.__nt), symbols2strPretty(self.__symbols))

    def __getitem__(self, index) -> Symbol[T]:
        return self.__symbols[index]


class Clause(Generic[T]):
    def __init__(self, prod: Prod[T], left: int, right: int) -> None:
        self.__prod = prod
        self.__left = left
        self.__right = right

    def isConflict(self, other: "Clause"):
        if self.getProd() != other.getProd():
            return False
        # [1,3] [2,4]
        if self.getLeft() < other.getLeft() < self.getRight() < other.getRight() or \
                other.getLeft() < self.getLeft() < other.getRight() < self.getRight():
            return True
        return False

    def isSingleNt(self) -> bool:
        """
        check clause is a single non terminal
        :return:
        """
        return len(self) == 1 and not next(iter(self)).isTerminal()

    def getValueNt(self) -> T:
        assert self.isSingleNt()
        return self.getValue()[0].getValue()

    def isProd(self) -> bool:
        return len(self) == len(self.__prod)

    def __repr__(self) -> str:
        return "Clause(%s,%s,%s)" % (repr(self.__prod), repr(self.__left), repr(self.__right))

    def isSub(self, other: "Clause[T]") -> bool:
        return self.__prod == other.__prod and self.__left >= other.__left and self.__right <= other.__right

    def __lt__(self, other):
        return (self.__prod, self.__left, self.__right) < (other.__prod, other.__left, other.__right)

    def __len__(self) -> int:
        return self.getRight() - self.getLeft()

    def getNt(self) -> str:
        return self.__prod.getNt()

    def getProd(self):
        return self.__prod

    def getLeft(self) -> int:
        return self.__left

    def getRight(self) -> int:
        return self.__right

    def getPrefix(self) -> Symbols:
        return self.__prod.getSymbols()[:self.getLeft()]

    def getSuffix(self) -> Symbols:
        return self.__prod.getSymbols()[self.getRight():]

    def getValue(self) -> Symbols:
        return self.__prod.getSymbols()[self.getLeft():self.getRight()]

    def __iter__(self):
        for symbol in self.getValue():
            yield symbol

    def __str__(self) -> str:
        ret = "%s:" % self.getProd().getNt()
        if self.getLeft() == self.getRight():
            p, s = ' '.join(map(str, self.getPrefix())), ' '.join(map(str, self.getSuffix()))
            return ret + (' ' if self.getLeft() != 0 else '') + p + bg(Config.clauseColor) + ' ' + attr('reset') + s
        for index, symbol in enumerate(self.__prod):
            if index == self.getRight():
                if not Config.showRepr:
                    ret += attr('reset')
                else:
                    ret += ' s '
            ret += ' '
            if index == self.getLeft():
                if not Config.showRepr:
                    ret += bg(Config.clauseColor)
                else:
                    ret += ' s '
            ret += str(symbol)
        if len(self.__prod) == self.getRight():
            if not Config.showRepr:
                ret += attr('reset')
            else:
                ret += ' s '
        return ret

    def __hash__(self) -> int:
        return hash((self.__prod, self.__left, self.__right))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Clause):
            return False
        return (self.__prod, self.__left, self.__right) == (other.__prod, other.__left, other.__right)


class Rule(Generic[T]):
    def __init__(self, nt: T, body: Collection[Prod[T]]) -> None:
        self.__nt = nt
        self.__body = set()
        self.__order = {}
        for i in body:
            self.addProd(i)

    def __repr__(self):
        return "Rule({}, {})".format(repr(self.__nt), repr(self.__body))

    def __len__(self) -> int:
        return len(self.__body)

    def getNt(self) -> T:
        return self.__nt

    def __str__(self) -> str:
        if len(self.__body) == 0:
            return '%s: ' % str(self.__nt)
        iterator = iter(sorted(self.__body, key=lambda x: self.__order[x]))
        ret = str(next(iterator))
        for prod in iterator:
            ret += '\n  | %s' % symbols2str(prod.getSymbols())
        return ret

    def pretty(self) -> str:
        if len(self.__body) == 0:
            return '%s: ' % str(self.__nt)
        iterator = iter(sorted(self.__body, key=lambda x: self.__order[x]))
        ret = next(iterator).pretty()
        for prod in iterator:
            ret += '\n  | %s' % symbols2strPretty(prod.getSymbols())
        return ret

    def addProd(self, prod: Prod[T]) -> None:
        self.__body.add(prod)
        self.__order[prod] = len(self.__order)

    def removeProd(self, prod: Prod[T]) -> None:
        self.__body.remove(prod)

    def findProd(self, prod: Prod[T]) -> bool:
        return prod in self.__body

    def getProds(self) -> Tuple[Prod[T], ...]:
        return tuple(self.__body)

    def __iter__(self):
        for prod in self.getProds():
            yield prod

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Rule) and (self.__nt, self.__body) == (other.__nt, other.__body)

    def __hash__(self) -> int:
        return hash((self.__nt, frozenset(self.__body)))


def buildSymbols(clause: Clause, subClauses: Collection[Clause], symbols: Tuple[Symbol]) -> Tuple[Symbol, ...]:
    jtbl: Dict[int, Clause] = {}
    for subClause in subClauses:
        jtbl[subClause.getLeft()] = subClause
    ret = []
    visited = set()
    index = clause.getLeft()

    while index < clause.getRight():
        if index in jtbl and index not in visited:
            visited.add(index)
            subClause = jtbl[index]
            index = subClause.getRight()
            ret += symbols
        else:
            ret.append(clause.getProd().getSymbols()[index])
            index += 1
    return tuple(ret)


class Grammar(Generic[T]):
    def __init__(self, start: T, rules: Collection[Rule[T]]) -> None:
        self._start = start
        self._rules = {rule.getNt(): rule for rule in rules}
        if start not in self._rules:
            self._rules[start] = Rule(start, [])

    def __repr__(self):
        return "Grammar(%s,%s)" % (repr(self._start), repr(list(self._rules.values())))

    def setStart(self, start: T):
        self._start = start

    def copy(self):
        import copy
        return Grammar(self._start, copy.deepcopy(self.getRules()))

    def getStart(self) -> T:
        return self._start

    def __iter__(self):
        for rule in self.getRules():
            yield rule

    def getRule(self, nt: T) -> Rule[T]:
        if nt not in self._rules:
            raise Exception("Rule of {0} not found\n\n{1}".format(repr(nt), str(self)))
        return self._rules[nt]

    def getRules(self) -> Tuple[Rule[T], ...]:
        return tuple(self._rules.values())

    def __str__(self) -> str:
        return '\n'.join(['start:%s' % self.getStart()] + [str(rule) for rule in self._rules.values()])

    def pretty(self) -> str:
        return '\n'.join(['start:%s' % self.getStart()] + [rule.pretty() for rule in self._rules.values()])

    def getNts(self) -> FrozenSet[T]:
        return frozenset(self._rules.keys())

    def addRule(self, rule: Rule[T]) -> None:
        self._rules[rule.getNt()] = rule

    def addProd(self, prod: Prod[T]) -> None:
        if not self.findNt(prod.getNt()):
            self.addRule(Rule(prod.getNt(), []))
        self._rules[prod.getNt()].addProd(prod)

    def asLark(self):
        terminals = self.getCharset()
        if len(terminals) == 0:
            return str(self)
        return f"{self}\n%declare {' '.join(map(str, terminals))}"

    def getProds(self, nt: Optional[str] = None):
        if nt is None:
            nts = self.getNts()
            prods = []
            for nt in nts:
                for prod in self.getRule(nt).getProds():
                    prods.append(prod)
            return prods
        else:
            return self.getRule(nt).getProds()

    def removeRule(self, nt: T) -> None:
        self._rules.pop(nt)

    def removeProd(self, prod: Prod[T]) -> None:
        self._rules[prod.getNt()].removeProd(prod)

    def findNt(self, nt: T) -> bool:
        return nt in self._rules

    def findProd(self, prod: Prod[T]) -> bool:
        return self.findNt(prod.getNt()) and self._rules[prod.getNt()].findProd(prod)

    def replaceProd(self, prod: Prod[T], newProd: Prod[T]):
        self.removeProd(prod)
        self.addProd(newProd)

    def getParser(self, **kwargs):
        class TypeLexer(Lexer):
            def __init__(self, lexer_conf):
                pass

            def lex(self, data):
                return [LarkToken(i, i, start_pos=j, end_pos=j + 1) for j, i in enumerate(data.split())]

        return lark.Lark(self.asLark(), lexer=TypeLexer, **kwargs)

    @timer('build oracle')
    @counter('build oracle')
    def getOracle(self) -> TokenizedOracle:

        return BetterOracle(LarkOracle(self.asLark(), lexer=TypeLexer), GrammarTokenInstantiator())

    def getCharset(self):
        charset = set()
        for prod in self.getProds():
            for symbol in prod:
                if symbol.isTerminal():
                    charset.add(symbol.getValue())
        return charset

    def clauses(self):
        for prod in self.getProds():
            for clause in prod.clauses():
                yield clause

    def newNt(self, prefix: str = 'n') -> str:
        index = 0
        while True:
            nt = "%s%d" % (prefix, index)
            if self.findNt(nt):
                index += 1
                continue
            return nt

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Grammar) and (other._start, other._rules) == (self._start, self._rules)

    def __hash__(self) -> int:
        return hash(str(self))



class GrammarTokenInstantiator(DefaultTokenInstantiator):
    def instantiate(self, tokens: Sequence[Token]) -> str:
        return ' '.join(map(lambda x: x.type, tokens))


class TypeLexer(Lexer):
    def __init__(self, lexer_conf):
        pass

    def lex(self, data):
        return [LarkToken(i, i) for i in data.split()]


class BetterOracle(TokenizedOracle):
    @timer('betterOracle build')
    def __init__(self, rawOracle: CachedStringOracle, tokenInstantiator: TokenInstantiator):
        super().__init__(rawOracle, tokenInstantiator)

    def parse(self, tokens: Union[Tokens]) -> bool:
        return super().parse(tokens)
