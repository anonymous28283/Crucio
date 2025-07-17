from typing import List

from crucio.oracle.tokenized import TokenizedOracle
from crucio.tokenize import Tokens, Token
from crucio.utils.statistics import global_dict


def checkAll(values, examples, oracle):
    from crucio.lexical.infer.segment.split import getContexts, Node, getMultiContexts
    from crucio.utils.global_bar import RichBar
    calls = oracle.raw().calls
    count = 0
    contexts = getMultiContexts(values, examples)
    bar = RichBar([0] * (len(values) * len(contexts)), total=len(values) * len(contexts), desc='检查完全等价')
    for context in contexts:
        for value in values:
            count += 1
            bar.inc()
            x = context.assembly([value])
            if not oracle.parse(x):
                global_dict['check'] += oracle.raw().calls - calls

                print('check=', count, '/', len(values) * len(contexts), ',', len(values), len(contexts))
                bar.close()
                return False, (context, value)
    bar.close()
    global_dict['check'] += oracle.raw().calls - calls
    print('check=', len(values) * len(contexts), '/', len(values) * len(contexts), ',', len(values), len(contexts))
    return True, Node(values, next(iter(getContexts(values, examples))))


def checkPartial(values, examples, oracle):
    from Lex.incremental.split import getContexts, Node, getMultiContexts
    from crucio.utils import RichBar
    contexts = getMultiContexts(values, examples)[:10]
    bar = RichBar([0] * (len(values) * len(contexts)), total=len(values) * len(contexts), desc='检查完全等价')
    for context in contexts:
        for value in values:
            bar.inc()
            x = context.assembly([value])
            if not oracle.parse(x):
                bar.close()
                return False, (context, value)
    bar.close()
    return True, Node(values, next(iter(getContexts(values, examples))))


def reduceMC(mc, values, oracle):
    from crucio.lexical.infer.segment.split import MultiContext
    from crucio.utils.global_bar import rqdm
    indexes = mc.indexes
    mc = MultiContext(mc.seq, [])
    for i in indexes:
        mc.indexes.add(i)
        parseResult = [oracle.parse(mc.assembly([value])) for value in rqdm(values, '计算区分')]
        if any(parseResult) and not all(parseResult):
            return parseResult, mc


def buildNode(values: List[Token], examples: List[Tokens], oracle: TokenizedOracle):
    from crucio.lexical.infer.segment.split import Node

    passed, ans = checkAll(values, examples, oracle)
    if passed:
        return ans
    context, value = ans

    parseResult, context = reduceMC(context, values, oracle)
    leftValues = [values[i] for i in range(len(values)) if not parseResult[i]]
    rightValues = [values[i] for i in range(len(values)) if parseResult[i]]
    left = buildNode(leftValues, examples, oracle)
    right = buildNode(rightValues, examples, oracle)
    return Node(values, context, left, right)


def buildDecisionTree2(examples: List[Tokens], oracle: TokenizedOracle):
    global_dict['check'] = 0
    values = list(set().union(*examples))
    return buildNode(values, examples, oracle)
