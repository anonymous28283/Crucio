import random
from abc import abstractmethod
from typing import Sequence

from crucio.tokenize import Token


class TokenInstantiator:
    @abstractmethod
    def instantiate(self, tokens: Sequence[Token]):
        pass


class DefaultTokenInstantiator(TokenInstantiator):
    def instantiate(self, tokens: Sequence[Token]):
        return ''.join([i.value if i.value is not None else i.type for i in tokens])


class SSTokenInstantiator(TokenInstantiator):
    def instantiate(self, tokens: Sequence[Token]):
        return ' '.join([i.value if i.value is not None else i.type for i in tokens])



class DictTokenInstantiator(TokenInstantiator):
    def __init__(self, tokenDict, spaceSensitive: bool = True):
        self.__tokenDict = tokenDict
        self.__sep = ''
        if not spaceSensitive:
            self.__sep = ' '

    def instantiate(self, tokens: Sequence[Token]):
        ret = []
        for token in tokens:
            if token.type in self.__tokenDict and len(self.__tokenDict[token.type]) > 0:
                ret.append(random.choice(self.__tokenDict[token.type]))
            else:
                ret.append(token.type)
        return self.__sep.join(ret)


class TypeTokenInstantiator(TokenInstantiator):
    def instantiate(self, tokens: Sequence[Token]):
        return ' '.join([i.type for i in tokens])


class SepTokenInstantiator(TokenInstantiator):
    def __init__(self, sep: str = ' '):
        self.sep = sep

    def instantiate(self, tokens: Sequence[Token]):
        return self.sep.join([i.value if i.value is not None else i.type for i in tokens])
