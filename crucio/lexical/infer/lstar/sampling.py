def samplingPositive(examples, hypothesis):
    for example in examples:
        hypothesis.reset_to_initial()
        ans = True
        for i in example:
            ans = hypothesis.step(i)
        if not ans:
            return example
    return None


import random


def samplingDfa(dfa, max_length=100, num_samples=10):
    accepted_samples = []
    input_alphabet = dfa.get_input_alphabet()
    while len(accepted_samples) < num_samples:
        state = dfa.initial_state
        trace = []
        for _ in range(random.randint(1, max_length)):
            inp = random.choice(input_alphabet)
            if inp not in state.transitions:
                break
            state = state.transitions[inp]
            trace.append(inp)
        if state.is_accepting:
            accepted_samples.append(trace)

    return accepted_samples
