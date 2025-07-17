from lark import lark

from crucio.tokenize import Tokenizer, Token, Tokens


class GeneralTokenizer(Tokenizer):
    def __init__(self, larkStr):
        self.lexer = lark.Lark(larkStr, start='start', propagate_positions=True)

    def tokenize(self, sentence: str) -> Tokens:
        return tuple(Token(i.type, i.value) for i in self.lexer.lex(sentence))


class TypeTokenizer(Tokenizer):
    def tokenize(self, sentence: str) -> Tokens:
        return tuple(Token(i) for i in sentence.split())