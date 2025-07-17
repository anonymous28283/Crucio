import string
from typing import List, Tuple, Optional, Union

from aalpy.automata import Dfa

from crucio.data_types.lexical import Segmentation
from crucio.instantiate.TokenIns import SepTokenInstantiator
from crucio.lexical.infer.group.fast_group import buildDecisionTree2
from crucio.lexical.infer.lstar.sul import FuncSUL
from crucio.lexical.infer.segment.sensitive import get_insensitive_chars
from crucio.lexical.infer.segment.split import PreSegmenter, Node, LexicalGroup, MultiContext, SegmentationAdjuster
from crucio.lexical.lexicalBuild.automations import make_dfa_from_triples
from crucio.lexical.lexicalBuild.infer import infer_dfa
from crucio.oracle import StringOracle
from crucio.oracle.string import CachedStringOracle
from crucio.oracle.tokenized import TokenizedOracle
from crucio.tokenize import SupportAssembly, Token, TokenizedContext
from crucio.utils.log import dummy
from crucio.utils.statistics import timer, counter, counting




def get_token_oracle(oracle: CachedStringOracle, insensitive_chars):
    if ' ' not in insensitive_chars:
        ins = SepTokenInstantiator('')
    else:
        ins = SepTokenInstantiator(' ')
    return TokenizedOracle(oracle, ins)


def seg2indexes(seg: Segmentation):
    prefix = ''
    indexes = []
    for i in seg.slices[:-1]:
        prefix += i
        indexes.append(len(prefix))
    return indexes


class ContextualCharOracle(CachedStringOracle):
    def __init__(self, contexts: List[Tuple[SupportAssembly, bool]], oracle: TokenizedOracle, insensitive_chars):
        super().__init__()
        self.contexts = sorted(contexts, key=lambda x: x[1], reverse=True)
        self.oracle = oracle
        self._space_insensitive = ' ' in insensitive_chars

    def pretty(self) -> str:
        ans = ''
        for context, tag in self.contexts:
            ans += self.oracle.ins(context.assembly((Token('#', '#'),))) + '\n'
            ans += str(tag) + '\n'
        return ans

    def __assembly(self, token_value, context: SupportAssembly):
        return context.assembly((Token(token_value, token_value),))

    def __parse_positive(self, token_value, context: SupportAssembly):
        example = self.__assembly(token_value, context)
        if not self.oracle.parse(example):
            return False
        return True

    @timer('CCO_multi_tokens')
    def __is_multi_token(self, token_value, context: SupportAssembly):
        if self._space_insensitive:
            seg = PreSegmenter.segment(token_value)
            indexes = seg2indexes(seg)
            for index in indexes:
                example = self.__assembly(token_value[:index] + ' ' + token_value[index:], context)
                if self.oracle.parse(example):
                    return True
        else:
            seg = PreSegmenter.segment(token_value)
            indexes = seg2indexes(seg)
            return len(indexes) > 0
        return False

    def __is_multi_token_r(self, token_value, context: SupportAssembly):
        if self._space_insensitive:
            seg = PreSegmenter.segment(token_value)
            indexes = seg2indexes(seg)
            for index in indexes:
                example = self.__assembly(token_value[:index] + ' ' + token_value[index:], context)
                if self.oracle.parse(example):
                    print(self.oracle.ins(example))
                    return True
        else:
            seg = PreSegmenter.segment(token_value)
            indexes = seg2indexes(seg)
            return len(indexes) > 0
        return False

    def __parse_negative(self, token_value, context: SupportAssembly):
        return not self.oracle.parse(self.__assembly(token_value, context))

    def report(self, token_value):
        for con, val in self.contexts:
            print(self.oracle.ins(con.assembly((Token(token_value, token_value),))))
            if val:
                print(val, self.__parse_positive(token_value, con), self.__is_multi_token_r(token_value, con))
            else:
                print(val, self.__parse_positive(token_value, con), self.__is_multi_token_r(token_value, con))
            print()
        return True

    @timer('CCO_parse')
    @counter('CCO_parse')
    def parse(self, token_value: str) -> bool:
        if len(token_value) == 0:
            return False
        n = 0
        for con, val in self.contexts:
            n += 1
            counting('CCO_parse_single', 1)
            start = self.oracle.raw().calls
            if val != (self.__parse_positive(token_value,con) and not self.__is_multi_token(token_value,con)):
                counting('lexical infer oracle_calls', self.oracle.raw().calls - start)
                return False
            else:
                counting('lexical infer oracle_calls', self.oracle.raw().calls - start)
        start = self.oracle.raw().calls
        if all(self.__is_multi_token(token_value, con) for con, val in self.contexts if val):
            counting('lexical infer oracle_calls', self.oracle.raw().calls - start)
            return False
        counting('lexical infer oracle_calls', self.oracle.raw().calls - start)
        return True


from typing import List





def get_valid_chars(examples: List[str], oracle: StringOracle, alphabet):
    valid = set().union(*examples).intersection(alphabet)
    for example in examples:
        for index, char in enumerate(example):
            if char in alphabet:
                for other_char in alphabet:
                    if other_char in valid:
                        continue
                    new_example = example[:index] + other_char + example[index + 1:]
                    if oracle.parse(new_example):
                        valid.add(other_char)
    return valid


def build_alphabet_feedback(examples: List[str], oracle: StringOracle):
    ans = set().union(*examples)
    alphabets = [string.ascii_lowercase, string.ascii_uppercase, string.digits]
    for alphabet in alphabets:
        if any(i in ans for i in alphabet):
            ans.update(get_valid_chars(examples, oracle, alphabet))
    return list(ans)


def build_sequence_dfa(s: str):
    transitions = []
    for i in range(len(s)):
        transitions.append((f's{i}', s[i], f's{i + 1}'))
    return make_dfa_from_triples(transitions, 's0', f's{len(s)}')


from typing import List, Tuple, Dict, Set


def build_sequences_dfa(samples: List[str]):
    transitions: List[Tuple[str, str, str]] = []
    state_map: Dict[Tuple[str, str], str] = {}
    start_state = 's0'
    state_counter = 0
    accept_states: Set[str] = set()

    for s in samples:
        current_state = start_state
        for ch in s:
            key = (current_state, ch)
            if key not in state_map:
                state_counter += 1
                next_state = f's{state_counter}'
                state_map[key] = next_state
                transitions.append((current_state, ch, next_state))
            current_state = state_map[key]
        accept_states.add(current_state)

    return make_dfa_from_triples(transitions, start_state, accept_states)


def build_alphabet(examples: List[str]):
    ans = set().union(*examples)
    alphabets = [string.ascii_lowercase, string.ascii_uppercase, string.digits]
    for alphabet in alphabets:
        if any(i in ans for i in alphabet):
            ans.update(alphabet)
    return list(ans)




def is_example_mutable(example, oracle: StringOracle, examples: List[str]):
    chars = build_alphabet(examples)
    for i in range(len(example)):
        for char in chars:
            new_example = example[:i] + char + example[i + 1:]
            if new_example in examples:
                continue
            if oracle.parse(new_example):
                return True
    return False


def lexical_infer2(oracle: StringOracle, examples: List[str], logger=dummy) -> Tuple[Optional[Dfa], Optional[Dfa]]:
    from crucio.utils.global_bar import rqdm
    logger.print('infer')
    mutable_dfa = None
    immutable_dfa = None
    # 1.divide into mutable and immutable
    mutable = []
    immutable = []
    for example in rqdm(examples, 'mutable Token detect'):
        if is_example_mutable(example, oracle, examples):
            mutable.append(example)
        else:
            immutable.append(example)
    logger.print('mutable token')
    for i in mutable:
        logger.print(i)
    logger.print()
    logger.print('immutable token')
    for i in immutable:
        logger.print(i)
    logger.print()
    # 2. infer dfa
    if len(mutable) > 0:
        # 1. build token oracle
        dfa_oracle = FuncSUL(lambda x: oracle.parse(''.join(x)))
        # 2. extract alphabet
        alphabet = build_alphabet_feedback(examples, oracle)
        # 3. infer by L*
        inferred_dfa: Dfa = infer_dfa(dfa_oracle, mutable, alphabet)
        mutable_dfa = inferred_dfa
    # 3. build dfa for immutable examples
    if len(immutable) > 0:
        immutable_dfa = build_sequences_dfa(immutable)
    return mutable_dfa, immutable_dfa


def separate_string(examples: List[str]) -> Tuple[List[str], List[str], List[str]]:
    double_quote = []
    single_quote = []
    other = []
    for example in examples:
        if example[0] == '"' and example[-1] == '"' and len(example) > 1:
            double_quote.append(example)
        elif example[0] == "'" and example[-1] == "'" and len(example) > 1:
            single_quote.append(example)
        else:
            other.append(example)
    return double_quote, single_quote, other


def build_string_dfa(border):

    transitions = []

    transitions.append(('s0', border, 's1'))

    for i in string.printable:
        if i == '\\' or i == border:
            continue
        transitions.append(('s1', i, 's1'))

    transitions.append(('s1', '\\', 's2'))

    for i in string.printable:
        transitions.append(('s2', i, 's1'))

    transitions.append(('s1', border, 's3'))

    return make_dfa_from_triples(transitions, 's0', 's3')



def segment_examples(examples: List[str], oracle: CachedStringOracle, logger=dummy):
    # Step1. segment by pre-defined rule
    segs = PreSegmenter.segmentAll(examples)
    # Step2. char sensitive detect
    insensitive_chars = get_insensitive_chars(segs, oracle)
    logger.print('insensitive chars=', insensitive_chars)
    # Step3. if space insensitive,adjust
    if ' ' in insensitive_chars:
        with logger.timer('adjust segment'):
            segs = SegmentationAdjuster(oracle, insensitive_chars).adjustAll(segs)
    return segs, insensitive_chars
