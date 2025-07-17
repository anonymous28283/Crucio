import platform


class Config:
    showSplit = False
    noBalanceCheck = False  # if True, do not check parenthesis
    clauseColor = 'green'
    showRepr = True
    log = True
    realInfer = False
    localConSub = 0
    name = 'tmp'
    showParallelInfo = False
    enableConflict = False
    examples = []
    reverse = False
    raw_cache = False


def printParallel(*args, **kwargs):
    if Config.showParallelInfo:
        print(*args, **kwargs)


def isMacOs():
    return platform.system() == 'Darwin'
