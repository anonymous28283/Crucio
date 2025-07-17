from typing import Collection

from crucio.config import Config
from crucio.grammar_tool import checkBalance

from crucio.tokenize import Tokens, TokenizedContext
from crucio.utils.subseq import SubSeqIterator


def Subs(examples: Collection[Tokens]):
    ans = set()
    for tokens in examples:
        tokens: Tokens
        ans = ans.union(Sub(tokens))
    return ans


def SubsK(examples: Collection[Tokens], k):
    ans = set()
    for tokens in examples:
        tokens: Tokens
        ans = ans.union(Sub(tokens))
    return set({i[:k] + i[-k:]: i for i in ans}.values())


def Sub(tokens: Tokens):
    ssi = SubSeqIterator(tokens)
    ret = set()
    for left, right in ssi:
        if not checkBalance(tokens[left:right]):
            continue
        ret.add(tokens[left:right])
    return ret


def Cons(examples: Collection[Tokens]):
    ans = set()
    for tokens in examples:
        tokens: Tokens
        ans = ans.union(Con(tokens))
    return ans


def ConsK(examples: Collection[Tokens], k):
    ans = set()
    for tokens in examples:
        tokens: Tokens
        ans = ans.union(Con(tokens))
    return set({(i.getPrefix()[-k:], i.getSuffix()[:k]): i for i in ans}.values())


def Con(tokens: Tokens):
    ssi = SubSeqIterator(tokens)
    ret = set()
    for left, right in ssi:
        if not checkBalance(tokens[left:right]):
            continue
        ret.add(TokenizedContext(tokens[:left], tokens[right:]))
    return ret
