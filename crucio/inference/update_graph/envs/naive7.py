from typing import List

from crucio.inference.build_dm import build_dm
from crucio.inference.tree import Bubble, buildGrammar
from crucio.inference.update_graph.envs.compress import CompressedDM
from crucio.inference.update_graph.envs.util import build_flatten_trees, extract_all_bubbles, build_graph, \
    assembly_cons_subs, get_valid_clique, fold_bubbles_and_update, \
    build_matrix_by_lookup_c_wrapped, remove_conflict_inv
from crucio.oracle.tokenized import IncrementalOracle
from crucio.utils.global_bar import TaskProgress
from crucio.utils.statistics import RecordTime


def get_coverages(cliques, cons, subs, cdm):
    coverages = {}
    for clique in cliques:
        clique_cons = set()
        clique_subs = set()
        for i in clique:
            clique_cons.update(cdm.cons[cons[i]])
            clique_subs.update(cdm.subs[subs[i]])
        coverages[clique] = assembly_cons_subs(clique_cons, clique_subs)
    return coverages


def infer_dm(examples, dm):
    ntIndex = 1
    # Step1. 构建树
    trees = build_flatten_trees(examples)
    # Step2. 构建当前语法以及oracle.
    g = buildGrammar(trees)
    o: IncrementalOracle = IncrementalOracle(g.getOracle())
    # Step3. 计算bubbles和上下文以及子串
    bubbles: List[Bubble] = extract_all_bubbles(trees)
    cons = [dm.getIndexByContext(bubbles[i].getContext()) for i in range(len(bubbles))]
    subs = [dm.getIndexBySubseq(bubbles[i].getSeq()) for i in range(len(bubbles))]
    # Step4. 构建cdm
    cdm = CompressedDM(dm)
    with TaskProgress(initial_description="后续任务") as tp:
        while True:
            with RecordTime('total'):
                # Step5 构建图
                tp.update_task('构建交换图')
                adj = build_matrix_by_lookup_c_wrapped(len(bubbles), subs, cons, cdm)
                remove_conflict_inv(adj, bubbles)
                graph = build_graph(adj)
                # Step6 构建当前语法
                tp.update_task('构建语法 ')
                g = buildGrammar(trees)
                o.update_oracle(g.getOracle())
                # Step7 计算极大团
                tp.update_task('计算极大团')
                cliques = graph.getFastMaximalCliques(True)
                # Step8 计算覆盖集
                tp.update_task('计算覆盖集')
                coverages = get_coverages(cliques, cons, subs, cdm)
                # Step9. 选取极大团
                tp.update_task('选取极大团')
                clique = get_valid_clique(cliques, coverages, o)
                if clique is None:
                    break
                o.update_cache(coverages[clique])
                # Step10. 合并Bubbles
                tp.update_task('合并Bubble')
                target_bubbles = [bubbles[i] for i in clique]
                nt = f'n{ntIndex}'
                ntIndex += 1
                bubbles, cons, subs = fold_bubbles_and_update(target_bubbles, nt, bubbles, cons, subs, cdm)
                # print(buildGrammar(trees))
            tp.advance(1)
    # showStatistics()
    return buildGrammar(trees)


def infer(examples, oracle):
    dm = build_dm(examples, oracle)
    return infer_dm(examples, dm)


