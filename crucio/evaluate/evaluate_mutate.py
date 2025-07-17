import time
from typing import Collection

from tqdm import tqdm

from crucio.data_types import Grammar
from crucio.evaluate.mutate.mutate_examples import evaluateMutatePrecision
from crucio.instantiate.node.core.node_grow.per_prod_limit import PerProdLimitSNG
from crucio.instantiate.symbol.symbol_ins import SngSymbolInstantiator
from crucio.oracle.extend.naive import NaiveExtendOracle
from crucio.oracle.tokenized import TokenizedOracle
from crucio.tokenize import Tokens, Tokenizer
from crucio.utils import str1, harmonic_mean
from crucio.utils.log import Logger, dummy
from crucio.utils.time_out import timeout

from dataclasses import dataclass


@dataclass
class Evaluation:
    p: float
    r: float
    f1: float
    timePerParse: float

    def __str__(self):
        return f'p={self.p}, r={self.r} ,f1={self.f1} ,tPP={self.timePerParse:.4f}'


def f1(p, r):
    return 2 * (p * r) / (p + r)


def sampling(sampler, n=1000, maxRetry=20):
    from crucio.utils.global_bar import progress
    precisionSet = set()
    task = progress.add_task("Sampling", total=n)
    for _ in range(n):
        progress.advance(task)
        length = len(precisionSet)
        max_retry = maxRetry
        retry = 0
        while len(precisionSet) == length:
            precisionSet.add(sampler.instantiateNt())
            retry += 1
            if retry > max_retry:
                break
        if retry > max_retry:
            break
    progress.remove_task(task)
    progress.refresh()
    return precisionSet


@timeout(seconds=60,timeout_return=False)
def parse_timeout(oracle, example):
    return oracle.parse(example)


def evaluateGrammarPm2(grammar: Grammar, oracle: TokenizedOracle, testSet: Collection[str], tokenizer: Tokenizer,
                       logger: Logger = dummy):
    from crucio.utils.global_bar import rqdm
    print('Eval of sampling precision:')
    logger.print('Eval of sampling precision:')
    sampler = SngSymbolInstantiator(PerProdLimitSNG(grammar, 10))
    precisionSet = sampling(sampler)
    precision = 0
    total = 0
    print('Parsing precision set')
    NaiveExtendOracle(oracle).batch(precisionSet, '解析样本')
    for tokens in rqdm(precisionSet):
        logger.print(oracle.ins(tokens))
        total += 1
        if oracle.parse(tokens):
            logger.print("Passed")
            precision += 1
        else:
            logger.print('Failed')
    recall = 0
    print('pS=', precision / total)
    print('Eval of recall:')
    logger.print('Eval of recall:')
    grammarOracle = grammar.getOracle()
    # 0.0319
    tokenized = []
    start = time.time()
    for i in testSet:
        try:
            tokenized.append(tokenizer.tokenize(i))
        except:
            logger.print(i)
            logger.print('Failed by lexical')

    parsed = set()
    for tokens in rqdm(tokenized):
        logger.print(oracle.ins(tokens))
        logger.print(str1(tokens))
        if parse_timeout(grammarOracle,tokens):
            logger.print("Passed")
            parsed.add(tokens)
            recall += 1
        else:
            logger.print("Failed")
    cost = time.time() - start
    print('r=', recall / len(testSet))
    print('Eval of mutate precision:')
    pM = evaluateMutatePrecision(parsed, grammar, oracle)
    print('pM=', pM)
    S = 0
    for prod in grammar.getProds():
        S += len(prod)
    T = len(grammar.getCharset())
    A = len(list(grammar.getProds()))
    return {'pS': precision / total,
            'pM': pM,
            'r': recall / len(testSet),
            'tp': cost/len(testSet) ,
            'NT': len(grammar.getNts()),
            'A': A,
            'l(A)': S / A,
            'S': S,
            'T': T,
            }
