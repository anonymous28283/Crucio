from typing import List, Tuple, Union, Collection

from aalpy.automata import Dfa, DfaState


def make_dfa_from_triples(transitions: List[Tuple[str, str, str]], start: str, accept: Union[str, Collection[str]]) -> Dfa:
    state_names = {src for src, _, _ in transitions} | {dst for _, _, dst in transitions}

    state_map = {name: DfaState(name) for name in state_names}


    for src, symbol, dst in transitions:
        state_map[src].transitions[symbol] = state_map[dst]


    if isinstance(accept, str):
        state_map[accept].is_accepting = True
    else:
        for s in accept:
            state_map[s].is_accepting = True

    dfa = Dfa(state_map[start], list(state_map.values()))
    return dfa


space = make_dfa_from_triples([
    ('q0', ' ', 'q1'),
], 'q0', 'q1')
