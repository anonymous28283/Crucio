from typing import Iterator

from crucio.grammar_tool import checkBalance
from crucio.decompose.strategy import DataDecomposer
from crucio.tokenize import Tokens
from crucio.utils.subseq import SubSeqIterator


class SubSeqDecomposer(DataDecomposer):
    def decompose(self, tokens: Tokens) -> Iterator[Tokens]:
        ssi1 = SubSeqIterator(tokens)
        for l1, r1 in ssi1:
            ssi2 = SubSeqIterator(tokens[l1:r1])
            for l2, r2 in ssi2:
                subseq = tokens[:l1] + tokens[l1:r1][l2:r2] + tokens[r1:]
                if not checkBalance(subseq) or len(subseq) >= len(tokens):
                    continue
                yield subseq

