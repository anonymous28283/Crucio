import os
from dataclasses import dataclass

from lark import Lark
from lark.lexer import Lexer

from crucio.consts import projectPath, benchmarkPath, getTrainPath
from crucio.dataset.dataload import MultiFileDataLoader
from crucio.instantiate.TokenIns import DictTokenInstantiator, TypeTokenInstantiator
from crucio.oracle.string import CachedStringOracle
from crucio.tokenize.general import GeneralTokenizer, TypeTokenizer
from crucio.utils.load_grammar import loadGrammar


@dataclass
class Meta:
    name: str

    def __init__(self, name):
        self.name = name
        try:
            with open(projectPath + 'meta/' + name + '/grammar.lark', 'r') as f:
                self.grammar = loadGrammar(f.read())
        except FileNotFoundError:
            self.grammar = None

        try:
            with open(projectPath + 'meta/' + name + '/tokenInsDict', 'r') as f:
                self.tokenInsDict = eval(f.read())
        except FileNotFoundError:
            self.tokenInsDict = None

        try:
            with open(projectPath + 'meta/' + name + '/lexical.lark', 'r') as f:
                self.lexical = f.read()
                self.spaceSensitive = '%ignore' not in self.lexical
        except FileNotFoundError:
            self.lexical = None
            self.spaceSensitive = True

    def getTokenizer(self):
        if self.lexical is None:
            return TypeTokenizer()
        return GeneralTokenizer(self.lexical)

    def getInstantiator(self):
        if self.tokenInsDict is None:
            return TypeTokenInstantiator()
        return DictTokenInstantiator(self.tokenInsDict, self.spaceSensitive)

    def getParser(self, **kwargs):
        self1 = self

        class TypeLexer(Lexer):
            def __init__(self, lexer_conf):
                self.__lexer = Lark(self1.lexical)

            def lex(self, data):
                return self.__lexer.lex(data)

        parser = Lark(self.grammar.asLark(), lexer=TypeLexer, **kwargs)
        return parser

    def get_inner_oracle(self):
        class MetaOracle(CachedStringOracle):
            def __init__(self, tokenizer, oracle):
                super().__init__()
                self.tokenizer = tokenizer
                self.oracle = oracle

            def _parse(self, sentence: str) -> bool:
                try:
                    tokens = self.tokenizer.tokenize(sentence)
                except:
                    return False
                ans = self.oracle.parse(tokens)
                return ans

        return MetaOracle(self.getTokenizer(), self.get_grammar_oracle())

    def get_grammar_oracle(self):
        return self.grammar.getOracle()

    def get_external_oracle(self):
        import sys
        path = f"{benchmarkPath}{self.name}/parse_{self.name}_{sys.platform}"
        from crucio.oracle.string import ExternalOracle
        if not os.path.exists(path):
            return None
        return ExternalOracle(path)

    def getSeeds(self):
        seeds = []
        path = f"{benchmarkPath}{self.name}"
        for sub in os.listdir(path):
            if 'train' not in sub:
                continue
            seeds.append(sub.split('-')[-1])
        return sorted(seeds)

    def getTrainSet(self, seed: str):
        trainPath = getTrainPath(self.name, seed)
        dl = MultiFileDataLoader()
        return dl.load(trainPath)

    def getTokenTrainSet(self, seed: str):
        return self.getTokenizer().tokenizeAll(self.getTrainSet(seed))

    def getTokenTestSet(self, seed: str = None):
        return self.getTokenizer().tokenizeAll(self.getTestSet(seed))

    def getTestSet(self, seed: str = None):
        dataLoader = MultiFileDataLoader()
        if seed is None:
            path = projectPath + '/benchmark/{0}/{0}-test'.format(self.name)
        else:
            path = projectPath + '/benchmark/{0}/{0}-test-{1}'.format(self.name, seed)
        return dataLoader.load(path)


def load_meta(name):
    return Meta(name)
