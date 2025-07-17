from aalpy import SUL


class FuncSUL(SUL):
    def __init__(self,func):
        super().__init__()
        self.func = func
        self.input_seq = []

    def pre(self):
        self.input_seq = []

    def step(self, letter):
        if letter is None:
            return False
        self.input_seq.append(letter)
        return self.func(self.input_seq)

    def post(self):
        self.input_seq = []