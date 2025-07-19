import random
from collections import defaultdict
from typing import Collection

from crucio.grammar_tool.Parser import STParser
from crucio.grammar_tool.extract_con_sub import extractCS
from crucio.oracle.extend.naive import NaiveExtendOracle
from crucio.tokenize import Tokens
from crucio.utils import str1
from crucio.utils.log import Logger
from crucio.utils.statistics import timer


def get_candidates(parser, example: Tokens):
    tree = parser.parse(example).getRoot()

    # IntervalExample

    mutate_list = extractCS(tree)
    grouped_data = defaultdict(list)

    for a, b, c in mutate_list:
        grouped_data[(a, b)].append(c)
    return grouped_data




@timer('mutate examples')
def mutateExamples2(parser, examples: Collection[Tokens]):
    from crucio.utils.global_bar import rqdm, TaskProgress
    if len(examples) == 0:
        return set()
    contexts = defaultdict(set)
    values = defaultdict(set)
    for example in rqdm(examples, '解析'):
        for k, v in get_candidates(parser, example).items():
            for nt in v:
                contexts[nt].add(k[1])
                values[nt].add(k[0])

    # 将字典的项转换为列表并打乱
    mutated = set()
    # 进行遍历
    with TaskProgress(initial_description='变异', total=1000) as bar:
        logger = Logger().fork('mutateExamples')
        maxRetry = 100 * 1000
        while len(mutated) < 1000 and maxRetry > 0:
            randomNt = random.choice(list(contexts.keys()))
            randomCtx = random.choice(list(contexts[randomNt]))
            randomTokens = random.choice(list(values[randomNt]))
            logger.print('try', randomNt)
            logger.print(randomCtx)
            logger.print(str1(randomTokens))
            example1 = randomCtx.assembly(randomTokens)
            if example1 not in examples and example1 not in mutated and len(mutated) < 1000:
                mutated.add(example1)
                bar.advance(1)
            else:
                maxRetry -= 1
    return set(mutated)


def evaluateSwapPrecision(examples, grammar, oracle):
    parser = STParser(grammar)
    mutated = mutateExamples2(parser, examples)
    NaiveExtendOracle(oracle).batch(mutated,'解析样本')
    return len({i for i in mutated if oracle.parse(i)}) / len(mutated) if len(mutated) > 0 else 1

