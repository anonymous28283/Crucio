import string

from crucio.config import Config
from crucio.data_types.lexical import Segmentation
from crucio.utils.global_bar import rqdm
from crucio.lexical.infer.segment.binary_segment import getFlagsFast
from crucio.oracle.string import CachedStringOracle
from crucio.tokenize import Tokens, SupportAssembly
from crucio.utils.statistics import timer

from typing import Collection, List, Dict, Set

from lark import Lark

larkStr = r"""
start: program
program: token*
token: DOUBLE_QUOTE_STRING | SINGLE_QUOTE_STRING | IDENT | MARK | NUM
DOUBLE_QUOTE_STRING: /"([^"\\]|\\.|\\\n|\n)*"/
SINGLE_QUOTE_STRING: /'([^'\\]|\\.|\\\n|\n)*'/
IDENT: /[_a-zA-Z]+/
NUM: /[0-9]+/
MARK: /./ | /\n/ | /\r/
"""

import re

TOKEN_RE = re.compile(
    r'''
    (?P<DOUBLE_QUOTE_STRING>"([^"\\]|\\.|\\\n|\n)*")|
    (?P<SINGLE_QUOTE_STRING>'([^'\\]|\\.|\\\n|\n)*')|
    (?P<IDENT>[_a-zA-Z][_a-zA-Z0-9]*)|
    (?P<NUM>[0-9]+)|
    (?P<MARK>.)
    ''',
    re.VERBOSE
)

def tokenize(text):
    for match in TOKEN_RE.finditer(text):
        for key, val in match.groupdict().items():
            if val is not None:
                yield (key, val)

class PreSegmenter:
    """
    str -> Segmentation
    """
    lexer = Lark(larkStr,parser='lalr', lexer='contextual')

    @staticmethod
    def segment(example: str) -> Segmentation:
        tokens = PreSegmenter.lexer.lex(example)
        return Segmentation(tuple(token.value for token in tokens))



    @staticmethod
    def segmentAll(examples: Collection[str]) -> List[Segmentation]:
        return [PreSegmenter.segment(i) for i in examples]


class CharSegmenter:
    @staticmethod
    def segment(example: str) -> Segmentation:
        return Segmentation(tuple(char for char in example))

    @staticmethod
    def segmentAll(examples: Collection[str]) -> List[Segmentation]:
        return [CharSegmenter.segment(i) for i in examples]


class SegmentationAdjuster:
    """
    adjust by space
    Segmentation -> Segmentation
    """

    def __init__(self, oracle: CachedStringOracle, insensitive_chars=string.whitespace):
        self.oracle = oracle
        self.insensitive_chars = insensitive_chars

    def adjust(self, seg: Segmentation) -> Segmentation:
        flags = getFlagsFast(seg.slices, self.oracle, self.insensitive_chars)
        print('Pass rate=', sum(flags), '/', len(flags))
        newSplit = []
        index = 0
        while index < len(seg.slices):
            j = index
            while j < len(flags) and not flags[j]:
                j += 1
            newSplit.append(''.join([seg.slices[k] for k in range(index, j + 1)]))
            index = j + 1
        return Segmentation(tuple(newSplit))

    def adjustAll(self, segs: Collection[Segmentation]) -> List[Segmentation]:
        return [self.adjust(seg) for seg in rqdm(segs, '空格分割')]


class LexicalGroup:
    def __init__(self, lexicalMap: Dict[str, List[str]]):
        self.lexicalMap = lexicalMap

    @staticmethod
    def fromSets(sets: List[Set]):
        lexicalMap = {}
        for i, s in enumerate(sets):
            lexicalMap[f'T{i}'] = list(s)
        return LexicalGroup(lexicalMap)

    @staticmethod
    def fromSegs(segs: List[Segmentation], ignored):
        slices = list(set().union(*[seg.slices for seg in segs]))
        slices = [i for i in slices if i not in ignored]
        return LexicalGroup({f'T{i}': [value] for i, value in enumerate(slices)})

    def getTypes(self):
        return list(self.lexicalMap.keys())

    def getValues(self, ttype):
        return self.lexicalMap[ttype]

    def getValue(self, ttype):
        return self.lexicalMap[ttype][0]

    def getToken(self, ttype):
        return Token(ttype, self.lexicalMap[ttype][0])

    def getTokens(self, ttype):
        return [Token(ttype, value) for value in self.getValues(ttype)]

    def seg2tokens(self, seg: Segmentation) -> Tokens:
        result = []
        for i in seg.slices:
            for k, v in self.lexicalMap.items():
                if i in v:
                    result.append(Token(k, i))
                    break
        return tuple(result)

    def segs2examples(self, segs: Collection[Segmentation]):
        return [self.seg2tokens(seg) for seg in segs]


from crucio.tokenize import Token, Tokens, TokenizedContext
from typing import List, Optional, Set
from dataclasses import dataclass


@dataclass
class Node:
    values: List[Token]
    context: Optional[SupportAssembly] = None
    left: Optional["Node"] = None
    right: Optional["Node"] = None

    def isLeaf(self):
        return self.left is None



    def getContextsMap(self):
        if self.left is None:
            return [(self.values, (self.context,))]
        left_map = [(k, v + (self.context,)) for k, v in self.left.getContextsMap()]
        right_map = [(k, v + (self.context,)) for k, v in self.right.getContextsMap()]
        return left_map + right_map


class MultiContext(SupportAssembly):
    def __init__(self, seq, indexes):
        self.seq = seq
        self.indexes = set(indexes)

    def assembly(self, seq):
        ans = []
        for i in range(len(self.seq)):
            if i in self.indexes:
                ans.extend(seq)
            else:
                ans.append(self.seq[i])
        return tuple(ans)

    def __hash__(self):
        return hash((self.seq,frozenset(self.indexes)))

    def __eq__(self, other):
        return isinstance(other, MultiContext) and other.indexes == self.indexes and other.seq == self.seq


def getContexts(values: List[Token], examples: List[Tokens]) -> Set[TokenizedContext]:
    ans = set()
    for example in examples:
        for i in range(len(example)):
            if example[i] in values:
                ans.add(TokenizedContext(example[:i], example[i + 1:]))
    return ans


def getMultiContexts(values: List[Token], examples: List[Tokens]) -> List[MultiContext]:
    values = set(values)
    ans = []
    for example in examples:
        indexes = []
        for i in range(len(example)):
            if example[i] in values:
                indexes.append(i)
        if len(indexes) == 0:
            continue
        ans.append(MultiContext(example, indexes))
    return ans






@timer('分割样本')
def segment(examples, oracle, insensitive_chars=string.whitespace) -> List[Segmentation]:
    segs = PreSegmenter.segmentAll(examples)
    if Config.showSplit:
        print('pre segment')
        for i in segs:
            print(i.pretty())
    # adjust by space
    segs = SegmentationAdjuster(oracle, insensitive_chars).adjustAll(segs)
    if Config.showSplit:
        print('adjust split')
        for i in segs:
            print(i.pretty())
    return segs



