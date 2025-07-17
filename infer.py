import time
from typing import List

from crucio.config import Config
from crucio.dataset.dataload import MultiFileDataLoader
from crucio.oracle.string import ExternalOracle, CachedStringOracle
from crucio.utils.global_bar import stop, rqdm
from crucio.utils.log import dummy
from crucio.utils.statistics import showStatistics
from learn import run_crucio3
from monitor import initial_monitor

def validate_oracle(oracle: CachedStringOracle, examples: List[str]):
    for example in rqdm(examples, desc='CheckDataset'):
        if not oracle.parse(example):
            raise Exception(f'{example} does not accepted by oracle')

def infer_cfg(parser_path,train_path,log_path, logger=dummy):
    oracle = ExternalOracle(parser_path)
    dl = MultiFileDataLoader()
    train_set = dl.load(train_path)
    if len(train_set) == 0:
        print('No examples')
        exit(0)
    # check dataset
    validate_oracle(oracle, train_set)
    start = time.time()
    lexical,grammar,tokenizedOracle = run_crucio3(oracle,train_set)
    cost = time.time()-start
    grammar_dict = {
        'grammar':grammar,
        'tokenizer':lexical.getTokenizer(),
        'oracle': tokenizedOracle
    }
    call_time = oracle.call_time
    calls = oracle.calls
    with open(log_path,'w') as f:
        print('call_time=', call_time,file=f)
        print('calls=', calls,file=f)
        print('t=', cost,file=f)
        print('call_time=', call_time)
        print('calls=', calls)
        print('t=', cost)
    import dill
    with open(f'{log_path}.gramdict','wb') as f:
        dill.dump(grammar_dict,f)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('parser_path')
    parser.add_argument('train_path')
    parser.add_argument('log_path')
    parser.add_argument('--char', action='store_true')
    args = parser.parse_args()
    Config.realInfer = True
    initial_monitor()
    infer_cfg(args.parser_path, args.train_path, args.log_path)
    showStatistics()
    stop()