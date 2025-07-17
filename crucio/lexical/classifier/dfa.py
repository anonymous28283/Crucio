from crucio.lexical.infer.lexical_infer import lexical_infer2, separate_string, build_string_dfa
from crucio.oracle import StringOracle
from crucio.utils.dfa import dfa_accepts
from crucio.utils.log import dummy


def lexical_infer3(oracle,examples,logger=dummy):
    automations = []
    double_quote, single_quote, other = separate_string(examples)
    if len(double_quote) > 0:
        logger.print('double-quote=')
        for example in double_quote:
            logger.print(example)
        automations.append(build_string_dfa('"'))
    if len(single_quote) > 0:
        logger.print('single-quote=')
        for example in single_quote:
            logger.print(example)
        automations.append( build_string_dfa("'"))
    if len(other) > 0:
        logger.print('other')
        for example in other:
            logger.print(example)
        mutable_dfa, immutable_dfa = lexical_infer2(oracle, other, logger.fork('dfa-infer'))
        if mutable_dfa is not None:
            automations.append(mutable_dfa)
        if immutable_dfa is not None:
            automations.append(immutable_dfa)
    return automations

class DfaInferencer:
    def __init__(self, oracle: StringOracle):
        self.automations = []
        self.oracle = oracle

    def is_learned(self, example):
        for i in self.automations:
            if dfa_accepts(i, example):
                return True
        return False

    def infer(self, example):
        if self.is_learned(example):
            return
        assert self.oracle.parse(example)
        self.automations.extend(lexical_infer3(self.oracle, [example]))

    def get_automations(self):
        return self.automations
