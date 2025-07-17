import time
from typing import Optional

from crucio.config import Config
from crucio.data_types import Grammar
from crucio.data_types.distribution.matrix import DistributionalMatrix
from crucio.dataset.meta import load_meta
from crucio.grammar_tool.Parser import STParser
from crucio.inference.update_graph.envs.naive7 import infer_dm
from crucio.instantiate.node.core import SyntaxTree
from crucio.lexical.infer.lexical_infer import segment_examples, get_token_oracle
from crucio.lexical.infer.segment.split import LexicalGroup, PreSegmenter
from crucio.inference.build_dm import build_dm
from crucio.tokenize import Tokens, TokenizedContext, Token
from crucio.utils import prettyTokens, str1
from crucio.utils.object_manage import ObjectManager
from crucio.utils.statistics import RecordTime, counting
from crucio.lexical.classifier.DecisionNode import LexicalRule, is_multi_token
from crucio.decompose.decompose_forest import DeForest
from crucio.decompose.decompose_forest.grammar_infer import de_func, DeForestTeacher
from crucio.decompose.decompose_forest.search import BarPathCacheSearcher, BarPrioritySearcher, BarDefaultSearcher, \
    DefaultSearcher
from crucio.data_types.learn_teach import teach, Learner, T, K

from crucio.consts import SEP
from crucio.data_types import Symbol
from crucio.instantiate.node.core import SyntaxNode
from crucio.tokenize import pretty_tokens
from crucio.utils.log import terminal
from crucio.utils.time_out import timeout


def rebuild(node: SyntaxNode, example):
    if node.isTerminal():
        value = node.getSymbol().getValue().value
        ttype = node.getSymbol().getValue().type
        for i in example:
            if value == i.value:
                ttype = i.type
        return SyntaxNode(Symbol(ttype, value))
    else:
        new_node = SyntaxNode(node.getSymbol(), node.getProd())
        new_node.setChildren([rebuild(i, example) for i in node.getChildren()])
        return new_node



@timeout(seconds=120, timeout_return='timeout')
def parse_timeout(parser, example):
    return parser.parseSafe(example)


def report_lexical_error(x, y, z, logger=terminal):
    id_map = {id(y[i]): z[i] for i in range(len(y))}
    new_tokens = tuple(i if id(i) not in id_map else id_map[id(i)] for i in x)
    logger.title('Error lexical report')
    logger.print('Correct=', pretty_tokens(x))
    logger.print('Mapped=', pretty_tokens(new_tokens))
    logger.print('Lexical map=')
    for i in x:
        if id(i) in id_map and i.value != id_map[id(i)].value:
            logger.print(i.value, '->', id_map[id(i)].value)
    logger.print(SEP)



def g(x, y, z, w):
    with RecordTime('min_example_search_is_multi_token'):
        for index in range(len(x)):
            if is_multi_token(w,
                              x[index].value,
                              TokenizedContext(x[:index], x[index + 1:])):
                return x
    id_map = {id(y[i]): z[i] for i in range(len(y))}
    new_tokens = tuple(i if id(i) not in id_map else id_map[id(i)] for i in x)
    if w.parse(new_tokens):
        return "PARSED"
    return None


class LexicalLearner(Learner):
    def __init__(self, tokenizedOracle, insensitive_chars, forest: DeForest, raw):
        self.__lexical = LexicalRule(tokenizedOracle, insensitive_chars)
        self.__raw = raw
        self.__searcher = DefaultSearcher(forest)
        self.__oracle = tokenizedOracle

    @property
    def lexical(self):
        return self.__lexical

    def learn(self, example: Tokens):
        self.lexical.fit(example)
        self.lexical.predict(example)
        while True:
            for i in self.__raw:
                ans = self.lexical.check(i)
                if ans is not None:
                    with RecordTime('min lexical example search'):
                        min_tokens = self.__searcher.search(lambda x: g(x, i, ans, self.__oracle))
                    report_lexical_error(min_tokens, i, ans)
                    self.lexical.fit(min_tokens)
                    break
            else:
                break
        return

    def understand(self, example: Tokens) -> Optional[K]:
        if len(example) == 0:
            return 'YES'
        with  RecordTime('single example check'):
            for index in range(len(example)):
                if is_multi_token(self.__oracle,
                                  example[index].value,
                                  TokenizedContext(example[:index], example[index + 1:])):
                    return example
        try:
            translated = self.__lexical.predict(example)
            return translated
        except:
            return None


class GrammarLearner(Learner):
    def __init__(self, tokenizedOracle, lexical, forest: DeForest,insensitive_chars):
        self.__oracle = tokenizedOracle
        self.__examples = []
        self.__lexical = lexical
        self.__grammar = Grammar('n0', [])
        self.__parser = STParser(self.__grammar)
        self.__dm: DistributionalMatrix = build_dm([], self.__oracle)
        self.__parser_cache = {}
        self.__forest = forest
        self.__timeout = set()
        self.__insensitive_chars = insensitive_chars

    def learn(self, example: T):
        if ' ' not in self.__insensitive_chars:
            seg = PreSegmenter.segment(''.join([i.value for i in example]))
            example = tuple(Token(i,i) for i in seg.slices)

        print('infer example')
        print(prettyTokens(example))
        logger = terminal.fork('meta')

        self.__examples.append(self.__lexical.predict(example))
        logger.print(str1(self.__examples[-1]))
        logger.print(prettyTokens(example))
        start = self.__oracle.raw().calls
        self.__dm.addExample(self.__examples[-1])
        counting('distributional matrix construct calls', self.__oracle.raw().calls - start)
        with RecordTime('grammar infer'):
            self.__grammar = infer_dm(self.__examples, self.__dm)
            self.__parser = STParser(self.__grammar)
            self.__parser_cache.clear()

    def understand(self, example: T):
        if ' ' not in self.__insensitive_chars:
            seg = PreSegmenter.segment(''.join([i.value for i in example]))
            example = tuple(Token(i,i) for i in seg.slices)
        if example in self.__timeout:
            return 'timeout'
        if example in self.__parser_cache:
            return self.__parser_cache[example]

        # translate by lexical
        try:
            translated = self.__lexical.predict(example)
        except:
            print('Can not translate',example,'while grammar inference')
            return 'example can not translated'
        # parse by grammar
        tree = parse_timeout(self.__parser, translated)
        if tree is None:
            self.__parser_cache[example] = None
            return None
        if tree == 'timeout':
            node = self.__forest.get_node(example)
            n = 0
            while node:
                self.__parser_cache[node.value] = 'timeout'
                self.__timeout.add(node.value)
                node = node.parent
                n += 1
            print(f'total {n}examples marked as timeout')
            t = time.time()
            om = ObjectManager('timeout')
            print('timeout example, length=', len(example), 'saved to', f'timeout-{t}')
            om.save((translated, self.__grammar), str(t))
            return self.__parser_cache[example]
        tree: SyntaxTree
        root: SyntaxNode = tree.getRoot()
        self.__parser_cache[example] = SyntaxTree(rebuild(root, example), self.__grammar)
        return self.__parser_cache[example]

    @property
    def grammar(self):
        return self.__grammar


def run_crucio3(oracle, examples):
    # lexical inference
    segs, insensitive_chars = segment_examples(examples, oracle)
    defaultGroup = LexicalGroup.fromSegs(segs, insensitive_chars)
    tokenizedExamples = defaultGroup.segs2examples(segs)
    tokenizedOracle = get_token_oracle(oracle, insensitive_chars)
    forest = DeForest(lambda x: de_func(x, tokenizedOracle), tokenizedExamples)
    teacher = DeForestTeacher(BarPathCacheSearcher(BarPrioritySearcher(BarDefaultSearcher(forest),
                                                                       'LexicalInfer')
                                                   ))
    lexical_learner = LexicalLearner(tokenizedOracle, insensitive_chars, forest, tokenizedExamples)
    teach(teacher, lexical_learner)
    # grammar inference
    grammar_learner = GrammarLearner(tokenizedOracle, lexical_learner.lexical, forest,insensitive_chars)
    teacher = DeForestTeacher(BarPathCacheSearcher(BarPrioritySearcher(BarDefaultSearcher(forest),
                                                                       'GrammarInfer')
                                                   ))
    teach(teacher, grammar_learner)
    print(grammar_learner.grammar.pretty())
    return lexical_learner.lexical, grammar_learner.grammar, tokenizedOracle


def demo():
    meta = load_meta('turing')
    Config.realInfer = True
    examples = meta.getTrainSet('r0')
    o = meta.get_inner_oracle()
    run_crucio3(o, examples)


if __name__ == '__main__':
    demo()
