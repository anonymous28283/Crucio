from abc import abstractmethod
from dataclasses import dataclass
from typing import Collection, Tuple
from crucio.config import Config
from crucio.utils import str1


class Token:
    def __init__(self, ttype, value=None) -> None:
        self.__type = ttype
        self.__value = value

    @property
    def type(self):
        return self.__type

    @property
    def value(self):
        return self.__value

    def __str__(self):
        return self.type

    def __lt__(self, other):
        return isinstance(other, Token) and self.__type < other.__type

    def __repr__(self):
        return 'Token(%s,%s)' % (repr(self.type), repr(self.value))

    def __hash__(self) -> int:
        return hash(self.__type)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Token):
            return False
        return self.__type == other.__type


Tokens = Tuple[Token, ...]


class SupportAssembly:
    @abstractmethod
    def assembly(self, value: Tokens) -> Tokens:
        pass

    def assembly_one(self,token:Token) -> Tokens:
        return self.assembly((token,))

class TokenizedContext(SupportAssembly):
    def __init__(self, prefix: Tokens, suffix: Tokens) -> None:
        self.__prefix = tuple(prefix)
        self.__suffix = tuple(suffix)

    def assembly(self, value: Tokens) -> Tokens:
        return self.__prefix + tuple(value) + self.__suffix

    def __len__(self):
        return len(self.getPrefix())+len(self.getSuffix())

    def getPrefix(self) -> Tokens:
        return self.__prefix

    def getSuffix(self) -> Tokens:
        return self.__suffix

    def __str__(self):
        return str1(self.__prefix + ('s', 's') + self.__suffix)

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash((self.__prefix, self.__suffix))

    def __eq__(self, other):
        return isinstance(other,TokenizedContext) and self.__suffix == other.__suffix and self.__prefix == other.__prefix


class Tokenizer:
    @abstractmethod
    def tokenize(self, sentence: str) -> Tokens:
        pass

    def tokenizeAll(self, sentences: Collection[str]) -> Tuple[Tokens, ...]:
        ret = []
        for sentence in sentences:
            ret.append(self.tokenize(sentence))
        return tuple(ret)

    def instantiateToken(self, token: Token) -> str:
        if token.value is None:
            return token.type()
        return token.value


@dataclass
class SubSeq:
    tokens: Tokens
    l: int
    r: int

    def getContext(self):
        return TokenizedContext(self.tokens[:self.l], self.tokens[self.r:])

    def getValue(self):
        return self.tokens[self.l:self.r]

    def __hash__(self):
        return hash((self.tokens, self.l, self.r))

    def __str__(self):
        from colored import bg, attr
        tokens_str = [str(token) for token in self.tokens]
        before = ' '.join(tokens_str[:self.l])
        middle = ' '.join(tokens_str[self.l:self.r])
        after = ' '.join(tokens_str[self.r:])
        return f"{before} {bg(Config.clauseColor)}{middle}{attr('reset')} {after}"

    def __eq__(self, other):
        return self.tokens == other.tokens and self.l == other.l and self.r == other.r


def createSubSeq(value: Tokens, context: TokenizedContext):
    tokens = context.assembly(value)
    return SubSeq(tokens, len(context.getPrefix()), len(context.getPrefix()) + len(value))


def loadTokens(s: str):
    while '  ' in s:
        s = s.replace('  ', ' ')
    s = s.lstrip()
    if len(s) == 0:
        return ()
    return tuple(Token(i) for i in s.split(' '))


def loadContext(x):
    l, r = x.split('s s')
    return TokenizedContext(loadTokens(l.strip()), loadTokens(r.strip()))


def loadExamples(s):
    return [loadTokens(i) for i in s.split('\n')]

def pretty_tokens(tokens):
    return ' '.join(i.value if i.value else i.type for i in tokens)