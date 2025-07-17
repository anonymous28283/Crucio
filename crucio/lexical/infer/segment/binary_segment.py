# %%
"""
二分的方案来分割。
"""
import string
import time
# %%

# %%
from tqdm import tqdm

from crucio.utils.global_bar import RichBar


def toStr(slices):
    return ''.join(slices)


def getFlags(slices, oracle):
    flags = []
    # 同时插入多个空格，可以大幅度提升效率。
    for i in tqdm(range(1, len(slices)), '插入空格'):
        # 尝试插入空格。
        newStr = toStr(slices[:i]) + ' ' + toStr(slices[i:])
        flags.append(oracle.parse(newStr))
    return flags


def getFlagsSkipSpace(slices, oracle):
    flags = []
    for i in tqdm(range(1, len(slices)), '插入空格'):
        if slices[i].isspace() or slices[i - 1].isspace():
            flags.append(True)
            continue

        # 尝试插入空格。
        newStr = toStr(slices[:i]) + ' ' + toStr(slices[i:])
        flags.append(oracle.parse(newStr))
    return flags


def insertSpace(slices):
    return ' '.join(slices)


def insertSpaceByFlag(slices, flags):
    ret = slices[0]
    for i in range(len(flags)):
        if flags[i]:
            ret += ' '
        ret += slices[i + 1]
    return ret


def getFlagsBinary(slices, oracle, prefix='', suffix=''):
    if len(slices) <= 1:
        return []
    assert oracle.parse(prefix + toStr(slices) + suffix)
    example = prefix + insertSpace(slices) + suffix
    if oracle.parse(example):
        return [True] * (len(slices) - 1)
    if len(slices) == 2:
        return [False]
    # binary insert
    n = len(slices)
    mid = n // 2
    s1 = slices[:mid + 1]
    suffix1 = toStr(slices[mid + 1:]) + suffix
    s2 = slices[mid:]
    flags1 = getFlagsBinary(s1, oracle, prefix, suffix1)
    prefix1 = prefix + insertSpaceByFlag(s1[:-1] + ('',), flags1)
    flags2 = getFlagsBinary(s2, oracle, prefix1, suffix)
    # print(len(slices),len(flags1),len(flags2))
    return flags1 + flags2


def getFlagsFast(slices, oracle,insensitive_chars=string.whitespace):
    flags = [None] * (len(slices) - 1)
    # 把isspace()附近的字符都标记为True
    for index in range(len(slices)):
        if slices[index] in insensitive_chars:
            if index < len(flags):
                flags[index] = True
            if index - 1 > 0:
                flags[index - 1] = True

    def setIndexes(indexes):
        for i in indexes:
            flags[i] = True

    def resetIndexes(indexes):
        for i in indexes:
            flags[i] = None

    def getStr():
        ret = slices[0]
        for index in range(len(slices) - 1):
            if flags[index]:
                ret += ' '
            ret += slices[index + 1]
        return ret

    toCheck = [i for i in range(len(flags)) if flags[i] is None]
    bar = RichBar(toCheck, total=len(toCheck), desc='调整分割')

    # 把不确定的进行二分。
    def check(indexes):
        if len(indexes) == 0:
            return

        if len(indexes) == 1:
            bar.inc()
            setIndexes(indexes)
            flags[indexes[0]] = oracle.parse(getStr())
            return
        setIndexes(indexes)
        if not oracle.parse(getStr()):
            resetIndexes(indexes)
            m = len(indexes) // 2
            prefix = indexes[:m]
            suffix = indexes[m:]
            check(prefix)
            check(suffix)
        else:
            bar.inc(len(indexes))
    toCheck = sorted(toCheck,key=lambda x:slices[x])
    check(toCheck)
    bar.close()
    def update_flags():
        for i in range(len(flags)):
            if not flags[i]:
                flags[i] = True
                if oracle.parse(getStr()):
                    return True
                flags[i] = False
        return False
    while update_flags():
        pass
    return flags

