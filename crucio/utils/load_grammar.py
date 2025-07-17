from typing import List

from crucio.consts import simpleLarkGrammar
from crucio.data_types.grammar import Rule, SymbolType, Symbol, Prod, Grammar, Clause
from crucio.tokenize import Token, TokenizedContext

SimpleLarkGrammar = open(simpleLarkGrammar).read()
import lark


def containsUppercase(s):
    for char in s:
        if char.isupper():
            return True
    return False


def convertStmt2rule(stmt) -> Rule:
    tagMap = {"rep0": SymbolType.Rep0, "rep1": SymbolType.Rep1, "opt": SymbolType.Opt}
    nt = stmt.children[0].value
    prods = []
    for exprTree in stmt.children[1:]:
        symbols = []
        for term in exprTree.children:
            symbolType = SymbolType.Default
            value = term.children[0].value
            if len(term.children) != 1:
                symbolType = tagMap[term.children[1].children[0].data]
            if containsUppercase(value):
                symbols.append(Symbol(Token(value, None), symbolType))
            else:
                symbols.append(Symbol(value, symbolType))
        prods.append(Prod(nt, symbols))
    return Rule(nt, prods)


def loadRules(larkStr: str) -> List[Rule]:
    simpleLarkParser = lark.Lark(SimpleLarkGrammar)
    tree = simpleLarkParser.parse(larkStr)
    rules = []
    for stmt in tree.children:
        rules.append(convertStmt2rule(stmt))
    return rules


def loadProd(larkStr: str) -> Prod:
    return loadRules(larkStr)[0].getProds()[0]


def loadGrammar(larkStr: str) -> Grammar:
    start = None
    rules = []
    for rule in loadRules(larkStr):
        if rule.getNt() == 'start':
            start = rule.getProds()[0].getSymbols()[0].getValue()
            continue
        rules.append(rule)
    grammar = Grammar(start, rules)
    return grammar


def loadClause(larkStr: str, sep: str = 's') -> Clause:
    prod = loadProd(larkStr)
    indexes = []
    for i, symbol in enumerate(prod):
        symbol: Symbol
        if symbol.getValue() == sep:
            indexes.append(i)
    a, b = indexes
    newProd = Prod(prod.getNt(), prod.getSymbols()[:a] + prod.getSymbols()[a + 1:b] + prod.getSymbols()[b + 1:])
    return newProd.newClause(a, b - 1)


def loadContext(larkStr: str) -> TokenizedContext:
    clause = loadClause('n0: '+larkStr)
    return TokenizedContext(tuple(i.getValue() for i in clause.getPrefix()),
                            tuple(i.getValue() for i in clause.getSuffix()))
