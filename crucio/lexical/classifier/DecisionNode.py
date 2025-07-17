from collections import defaultdict
from dataclasses import dataclass
from typing import Optional, Set, Tuple, Collection, Dict, FrozenSet, Any, List

from aalpy import visualize_automaton
from aalpy.automata import Dfa

from crucio.lexical.infer.lexical_infer import ContextualCharOracle, seg2indexes
from crucio.lexical.infer.segment.split import getMultiContexts, MultiContext, PreSegmenter, getContexts
from crucio.oracle.tokenized import TokenizedOracle
from crucio.tokenize import SupportAssembly, Token, Tokens, pretty_tokens, Tokenizer, TokenizedContext
from crucio.utils.dfa import dfa_accepts
from crucio.utils.global_bar import rqdm
from crucio.utils.statistics import timer, counting
from crucio.lexical.classifier.dfa import DfaInferencer


def is_multi_token(oracle, token_value, context: SupportAssembly):
    seg = PreSegmenter.segment(token_value)
    indexes = seg2indexes(seg)
    for index in indexes:
        value = token_value[:index] + ' ' + token_value[index:]
        t = Token(value,value)
        example = context.assembly((t,))
        if oracle.parse(example):
            return True
    return False

class QueryTool:
    def __init__(self, oracle: TokenizedOracle):
        self.oracle = oracle
        self.examples = []

    def add(self, example: Tokens):
        self.examples.append(example)

    def get_contexts(self, tokens):
        contexts = list(getContexts(tokens, self.examples))
        return getMultiContexts(tokens, self.examples) + contexts

    def check(self, token, context):
        if token is None:
            return False
        example = context.assembly((token,))
        return self.oracle.parse(example) and not is_multi_token(self.oracle,token.value,context)

    def __reduce_multi_context(self, values, multi_context):
        indexes = multi_context.indexes
        mc = MultiContext(multi_context.seq, [])
        for i in indexes:
            mc.indexes.add(i)
            parseResult = [self.check(value, mc) for value in rqdm(values, '计算区分')]
            if any(parseResult) and not all(parseResult):
                return mc

    def check_all(self, tokens) -> Optional[SupportAssembly]:
        contexts = self.get_contexts(tokens)
        for context in contexts:
            for token in tokens:
                if not self.check(token, context):
                    if isinstance(context,MultiContext):
                        return self.__reduce_multi_context(tokens, context)
                    else:
                        return context
        return None

    def classify(self, tokens, context: SupportAssembly) -> Tuple[Set[Token], Set[Token]]:
        left = {i for i in tokens if not self.check(i, context)}
        right = {i for i in tokens if self.check(i, context)}
        return left, right


@dataclass
class DecisionNode:
    tokens: Set[Optional[Token]]
    context: Optional[SupportAssembly] = None
    left: Optional["DecisionNode"] = None
    right: Optional["DecisionNode"] = None

    def _update_children(self, qt: QueryTool):
        self.left.tokens, self.right.tokens = qt.classify(self.tokens, self.context)
        self.left.update_node(qt)
        self.right.update_node(qt)

    def add(self, tokens: Collection[Token]):
        self.tokens.update(tokens)

    @property
    def is_leaf(self):
        return self.left is None

    def update_node(self, qt: QueryTool):
        if self.is_leaf:
            context = qt.check_all(self.tokens)
            if context is None:
                return
            # split node
            self.split(context)
        self._update_children(qt)

    def split(self, context):
        self.context = context
        self.left = DecisionNode(set())
        self.right = DecisionNode(set())

    def get_paths(self) -> Dict[FrozenSet[Tuple[SupportAssembly, bool]], Set[Token]]:
        if self.is_leaf:
            if self.tokens == {None}:
                return {}
            else:
                return {frozenset(): self.tokens}
        left = self.left.get_paths()
        right = self.right.get_paths()
        ans = {k.union({(self.context, False)}): v for k, v in left.items()}
        ans.update({k.union({(self.context, True)}): v for k, v in right.items()})
        return ans


def create_decision_tree():
    return DecisionNode({None})


class LexicalRule:


    def __init__(self, oracle: TokenizedOracle, insensitive_chars):
        self.tree = create_decision_tree()
        self.dfa_map: Dict[Any, DfaInferencer] = {}
        self.oracle = oracle
        self.insensitive_chars = insensitive_chars
        self.qt = QueryTool(oracle)

    def _update_rule(self, path, tokens):
        if path not in self.dfa_map:
            self.dfa_map[path] = DfaInferencer(ContextualCharOracle(path, self.oracle, self.insensitive_chars))
        for token in tokens:
            self.dfa_map[path].infer(token.value)

    @timer('lexical-build')
    def fit(self, example: Tokens):
        print('lexical infer', pretty_tokens(example))
        # Step1. add to decision tree
        self.qt.add(example)
        start = self.oracle.raw().calls
        self.tree.add(example)
        self.tree.update_node(self.qt)
        counting('classify calls=', self.oracle.raw().calls - start)
        # Step2. extract decision tree paths
        path = self.tree.get_paths()
        # Step3. dfa infer
        for path, tokens in path.items():
            self._update_rule(path, tokens)

    @timer('lexical-sampling')
    def check(self, example: Tokens):
        positions = defaultdict(list)
        q = {}
        for i, k in enumerate(self.tree.get_paths().values()):
            q[f'T{i}'] = {j.value for j in k}
        for i in range(len(example)):
            try:
                token = self.predict_token(example[i])
                positions[token.type].append(i)
            except:
                pass
        start = self.oracle.raw().calls
        for k, indexes in positions.items():
            mc = MultiContext(example, indexes)
            for value in q[k]:
                tokens = mc.assembly_one(Token(k, value))
                if not self.oracle.parse(tokens):
                    counting('check-lexical', self.oracle.raw().calls - start)
                    return tokens
            for index in indexes[:10]:
                c = TokenizedContext(example[:index],example[index+1:])
                for value in q[k]:
                    tokens = c.assembly_one(Token(k, value))
                    if not self.oracle.parse(tokens):
                        counting('check-lexical', self.oracle.raw().calls - start)
                        return tokens
        counting('check-lexical', self.oracle.raw().calls - start)
        return None

    def predict_token(self, token: Token) -> Token:
        paths = self.tree.get_paths()
        for i, path in enumerate(paths):
            if token.value in {j.value for j in paths[path]}:
                return Token(f'T{i}', token.value)
        candidates = []
        for i, k in enumerate(paths):
            v = self.dfa_map[k]
            for dfa in v.automations:
                if dfa_accepts(dfa, token.value):
                    candidates.append(f'T{i}')
                    break
        if len(candidates) == 1:
            return Token(candidates[0], token.value)
        elif len(candidates) > 1:
            raise Exception(f'Multiple tokens found: {candidates}')
        raise Exception(f'Unrecognized token {token.value}')

    def report(self):
        # draw_dfa_matplotlib
        paths = self.tree.get_paths()
        for i, k in enumerate(paths):
            v = self.dfa_map[k]
            for j,dfa in enumerate(v.automations):
                visualize_automaton(dfa,f'T{i}_{j}')
        for i, path in enumerate(paths):
            print(f'T{i}')
            for s in {j.value for j in paths[path]}:
                print('\t',s)
        pass

    def predict(self, example: Tokens) -> Tokens:
        return tuple(self.predict_token(i) for i in example)

    def getTokenizer(self):
        paths = self.tree.get_paths()
        self1 = self
        automations:List[Dfa] = []
        for i, k in enumerate(paths):
            v = self.dfa_map[k]
            for dfa in v.automations:
                automations.append(dfa)

        class LearnedTokenizer(Tokenizer):
            def get_longest_match_length(self, sentence) -> int:
                indexes = []
                states = [dfa.initial_state for dfa in automations]
                for index in range(len(sentence)):
                    char = sentence[index]
                    new_states = []
                    for state in states:
                        if char in state.transitions:
                            new_states.append(state.transitions[char])
                    if len(new_states)>0:
                        states = new_states
                    else:
                        break
                    for i in states:
                        if i.is_accepting:
                            indexes.append(index+1)
                if len(indexes)==0:
                    return -1
                return max(indexes)

            def tokenize(self, sentence: str) -> Tokens:
                index = 0
                tokens = []
                while index < len(sentence):
                    if sentence[index] in self1.insensitive_chars:
                        index += 1
                        continue
                    length = self.get_longest_match_length(sentence[index:])
                    if length == -1:
                        raise Exception()
                    value = sentence[index:index + length]
                    tokens.append(self1.predict_token(Token(value, value)))
                    index += length
                return tuple(tokens)
        return LearnedTokenizer()