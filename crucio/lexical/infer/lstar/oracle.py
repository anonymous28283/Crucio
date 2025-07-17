from aalpy import Oracle, SUL

from crucio.lexical.infer.lstar.sampling import samplingPositive, samplingDfa


class MemberBasedEqvOracle(Oracle):
    def __init__(self, examples, alphabet: list, sul: SUL):
        super().__init__(alphabet, sul)
        self.examples = examples

    def find_cex(self, hypothesis):
        # get positive
        positive = samplingPositive(self.examples, hypothesis)
        if positive is not None:
            return positive
        # get negative
        samples = samplingDfa(hypothesis,100, 10)
        for sample in samples:
            self.sul.pre()
            ans = True
            for char in sample:
                ans = self.sul.step(char)
            self.sul.post()
            if not ans:

                return sample
        return None
