def dfa_accepts(dfa, input_str):
    state = dfa.initial_state
    for symbol in input_str:
        if symbol not in state.transitions:
            return False
        state = state.transitions[symbol]
    return state.is_accepting
