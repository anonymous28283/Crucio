import dill

from crucio.dataset.dataload import MultiFileDataLoader
from crucio.evaluate.evaluate_mutate import evaluateGrammarPm2
from crucio.utils.global_bar import stop
from crucio.utils.log import terminal

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('test_path')
    parser.add_argument('log_path')
    args = parser.parse_args()
    with open(f'{args.log_path}.gramdict', 'rb') as f:
        grammar_dict = dill.load(f)
        oracle = grammar_dict['oracle']
        tokenizer = grammar_dict['tokenizer']
        g = grammar_dict['grammar']
    dl = MultiFileDataLoader()
    test_set = dl.load(args.test_path)
    evaluation = evaluateGrammarPm2(g, oracle, test_set, tokenizer, terminal.fork('evaluation'))
    print(evaluation)
    with open(f'{args.log_path}.eval','w') as f:
        print(evaluation,file=f)
    stop()