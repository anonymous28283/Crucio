from crucio.config import Config
from crucio.tokenize import Tokens


def checkRealBalance(tokens: Tokens) -> bool:
    ps = [('(', ')'), ('[', ']'), ('{', '}')]
    pstack = []
    for token in tokens:
        for p in ps:
            if token.value == p[0]:
                pstack.append(p[0])
            elif token.value == p[1]:
                if len(pstack) == 0 or pstack[-1] != p[0]:
                    return False
                else:
                    pstack.pop()
    return len(pstack) == 0


def checkBalance(tokens: Tokens) -> bool:
    if Config.noBalanceCheck:
        return True
    if Config.realInfer:
        return checkRealBalance(tokens)
    ps = [('L_BRA', 'R_BRA'), ('L_SB', 'R_SB'), ('L_PAREN', 'R_PAREN'), ('L_VIRTUAL', 'R_VIRTUAL')]
    pstack = []
    for token in tokens:
        for p in ps:
            if token.type == p[0]:
                pstack.append(p[0])
            elif token.type == p[1]:
                if len(pstack) == 0 or pstack[-1] != p[0]:
                    return False
                else:
                    pstack.pop()
            elif token.type.startswith('L_VP'):
                pstack.append(token.type)
            elif token.type.startswith('R_VP'):
                if len(pstack) == 0 or pstack[-1][1:] != token.type[1:]:
                    return False
                else:
                    pstack.pop()
    return len(pstack) == 0
