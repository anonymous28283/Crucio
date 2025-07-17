from typing import Iterator

from crucio.grammar_tool import checkBalance
from crucio.decompose.strategy import DataDecomposer
from crucio.tokenize import Tokens
from crucio.utils.subseq import SubSeqIterator


class RemoveBlockDecomposer(DataDecomposer):
    def decompose(self, tokens: Tokens) -> Iterator[Tokens]:
        ssi = SubSeqIterator(tokens)
        for l, r in ssi:
            subseq = tokens[:l] + tokens[r:]
            if not checkBalance(subseq):
                continue
            yield subseq


class BinaryRemoveBlockDecomposer(DataDecomposer):
    def decompose(self, tokens: Tokens) -> Iterator[Tokens]:
        mid = len(tokens) // 2
        prefix = tokens[:mid]
        suffix = tokens[mid:]

        ssi1 = iter(SubSeqIterator(prefix))
        ssi2 = iter(SubSeqIterator(suffix))
        flag = True
        while flag:
            flag = False
            try:
                l, r = next(ssi1)
                flag = True
                subseq = prefix[:l] + prefix[r:] + suffix
                if not checkBalance(subseq):
                    continue
                yield subseq
            except StopIteration:
                pass
            try:
                l, r = next(ssi2)
                flag = True
                subseq = prefix + suffix[:l] + suffix[r:]
                if not checkBalance(subseq):
                    continue
                yield subseq
            except StopIteration:
                pass

