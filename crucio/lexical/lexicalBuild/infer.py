from typing import Collection, List

from aalpy import SUL
from aalpy.automata import Dfa

from crucio.lexical.infer.lstar.oracle import MemberBasedEqvOracle


def infer_dfa(oracle: SUL, examples: Collection[str], alphabet: List[str]) -> Dfa:
    eq = MemberBasedEqvOracle(examples, alphabet, oracle)
    from aalpy import run_Lstar
    learned_dfa = run_Lstar(
        alphabet=alphabet,
        sul=oracle,
        eq_oracle=eq,
        automaton_type='dfa',
        print_level=2,
    )
    return learned_dfa
