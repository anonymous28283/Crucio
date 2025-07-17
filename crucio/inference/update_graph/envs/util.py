import itertools
import queue
import random
from collections import defaultdict
from typing import List, Tuple, Dict, Collection, Set, Optional, Any

import numpy as np
from tqdm import tqdm

from compute_T import build_matrix_by_lookup_c
from crucio.data_types.distribution.matrix import DistributionalMatrix
from crucio.data_types.graph.undirected_graph import UndirectedGraph
from crucio.data_types.interval_example import isConflict, IntervalExample
from crucio.grammar_tool import checkBalance
from crucio.inference.tree import Node, getNtDict, Bubble, buildTree
from crucio.inference.update_graph.env import getParent, Interval
from crucio.inference.update_graph.envs.compress import CompressedDM
from crucio.inference.update_graph.query import MatrixQuerier
from crucio.tokenize import TokenizedContext, Tokens
from crucio.utils.statistics import timer, RecordTime


def extract_all_bubbles(trees: List[Node]):
    bubbles = set()
    for tree in trees:
        bubbles.update(tree.bubbling())
    ntDict = getNtDict(trees)
    bubbles = [i for i in bubbles
               if all(checkBalance(j) for j in i.getValues(ntDict))]
    return bubbles







@timer('is_match_mq_blocked')
def is_match_mq_blocked(b1, b2, contexts, subseqs, dm: DistributionalMatrix, mq: MatrixQuerier):
    cons1 = [[dm.getIndexByContext(j) for j in i] for i in contexts[b1]]
    cons2 = [[dm.getIndexByContext(j) for j in i] for i in contexts[b2]]
    subseqs1 = [[dm.getIndexBySubseq(j) for j in i] for i in subseqs[b1]]
    subseqs2 = [[dm.getIndexBySubseq(j) for j in i] for i in subseqs[b2]]
    return (all(mq.query(sub, con)
                for con in cons1 for sub in subseqs2
                ) and
            all(mq.query(sub, con)
                for con in cons2 for sub in subseqs1
                ))








@timer('build_bubble_map')
def build_bubble_map(bubble: Bubble, bubbles: List[Bubble]):
    # 初始化映射
    bubble_map = {}
    # 计算区间，以判断是否是相关的
    interval1 = Interval(bubble.getIE().left, bubble.getIE().right)
    # 预先计算bubble的父节点
    parent = getParent(bubble)
    # 遍历所有的bubble
    for bubble in bubbles:
        if getParent(bubble) is not parent:
            bubble_map[bubble] = [bubble]
            continue
        interval2 = Interval(bubble.getIE().left, bubble.getIE().right)
        if interval1.isConflict(interval2):
            # Case1. 冲突
            bubble_map[bubble] = []
        elif interval1 == interval2:
            # Case5. 恰好相同
            bubble_map[bubble] = [bubble, Bubble(None, None)]
        elif interval2.isSuper(interval1) and interval2.right == interval1.right:
            # Case3. 右边界对齐，左边在之外
            bubble_map[bubble] = [Bubble(bubble.start, None)]
        elif interval2.isSuper(interval1) and interval2.left == interval1.left:
            # Case7. 左边界对齐，右边在之外
            bubble_map[bubble] = [Bubble(None, bubble.end)]
        else:
            bubble_map[bubble] = [bubble]
    return bubble_map


def replace_placeholder(bubble: Bubble, placeholder, target):
    if bubble.start is placeholder:
        bubble.start = target
    if bubble.end is placeholder:
        bubble.end = target


def transfer_map(old_map: Dict, transfer: Dict):
    transferred_map = {}
    for old_key in old_map:
        for new_key in transfer[old_key]:
            transferred_map[new_key] = old_map[old_key]
    return transferred_map


def get_upper(bubble: Bubble):
    # Case1. bubble.start.left.left 和bubble.end.right.right is None
    # 这种情况是需要把其上面的Bubble考虑
    if bubble.start.left is None:
        return []
    ans = [bubble]
    parent = bubble.start.parent
    if bubble.start.left.left is None and bubble.end.right.right is None and parent is not None:
        ans.extend(get_upper(Bubble(parent, parent)))
    return ans


def get_lower(bubble: Bubble):
    ans = [bubble]
    # Case2. bubble.start = bubble.end
    # 这种情况是需要把下面的Bubble考虑
    child = bubble.start.child
    if bubble.start is bubble.end and child is not None:
        left = bubble.start.child.right
        right = left
        while right.right.right is not None:
            right = right.right
        ans.extend(get_lower(Bubble(left, right)))
    return ans



def get_uppers(nt: str, ntDict: dict):
    ans = {Bubble(node, node) for node in ntDict[nt]}
    while True:
        before = len(ans)
        for b in set(ans):
            if b.isProd():
                nt = b.parent.value
                for node in ntDict[nt]:
                    ans.add(Bubble(node, node))
        if len(ans) == before:
            break
    return ans


def get_node_prod(node: Node):
    start = node.child.right
    end = start
    while end.right.right is not None:
        end = end.right
    return Bubble(start, end)


def bubbles_update_context(nt: str, ntDict: dict):
    # 当前非终结符下的所有Bubble都需要更新
    # 如果当前非终结符下的Bubble是非终结符，我们需要重复该步骤.
    # 但是当前非终结符不需要更新.
    ans = set()
    nodes = ntDict[nt]
    for node in nodes:
        prod = get_node_prod(node)
        ans.add(prod)
        if prod.isNt():
            ans.update(bubbles_update_context(prod.getNt(), ntDict))
    return ans


def bubbles_update_context_iter(nt: str, ntDict: dict):
    # 当前非终结符下的所有Bubble都需要更新
    # 如果当前非终结符下的Bubble是非终结符，我们需要重复该步骤.
    # 但是当前非终结符不需要更新.
    ans = set()
    q = queue.Queue()
    q.put(nt)
    visited = {nt}
    while not q.empty():
        nt = q.get()
        nodes = ntDict[nt]
        for node in nodes:
            prod = get_node_prod(node)
            ans.add(prod)
            if prod.isNt() and prod.getNt() not in visited:
                q.put(prod.getNt())
                visited.add(prod.getNt())
    return ans


def bubbles_update_subseq(nt: str, ntDict: dict):
    # 当前非终结符对应的Bubble需要更新
    # 当前非终结符的parent如果也是非终结符，也需要更新。(要求当前非终结符对应的是完整的Prod)
    # 针对所有都是如此
    ans = set()
    nodes = ntDict[nt]
    for node in nodes:
        bubble = Bubble(node, node)
        ans.add(bubble)
        parent: Optional[Node] = node.parent
        if parent is not None and parent.parent is not None and bubble.isProd():
            ans.update(bubbles_update_subseq(parent.value, ntDict))
    return ans


def bubbles_update_subseq_iter(nt: str, ntDict: dict):
    # 当前非终结符对应的Bubble需要更新
    # 当前非终结符的parent如果也是非终结符，也需要更新。(要求当前非终结符对应的是完整的Prod)
    # 针对所有都是如此
    q = queue.Queue()
    q.put(nt)
    visited = {nt}
    ans = set()
    while not q.empty():
        nt = q.get()
        nodes = ntDict[nt]
        for node in nodes:
            bubble = Bubble(node, node)
            ans.add(bubble)
            parent: Optional[Node] = node.parent
            if (parent is not None and parent.parent is not None and bubble.isProd() and
                    parent.value not in visited):
                visited.add(parent.value)
                q.put(parent.value)
    return ans


def build_flatten_trees(examples):
    return [buildTree(example) for example in examples]


@timer('build_graph')
def build_graph(adjacent_mat):
    g = UndirectedGraph()
    n = adjacent_mat.shape[0]
    for i, j in itertools.combinations(range(n), 2):
        if adjacent_mat[i, j]:
            g.addEdge(i, j, True)
    return g




@timer('get_valid_clique')
def get_valid_clique(cliques, coverages, oracle):
    # 更新n，使用n+1来预测
    for clique in sorted(cliques, key=len, reverse=True):
        for i in sorted(coverages[clique]):
            if i in oracle.cache:
                continue
            if not oracle.parse(i):
                return clique
    return None


def assembly_cons_subs(cons, subs):
    return {con.assembly(sub) for con in cons for sub in subs}


def fold_bubble(bubble: Bubble, nt, bubbles: List[Bubble]):
    bubble_map = build_bubble_map(bubble, bubbles)
    # Step2. 折叠当前Bubble
    nt_node = bubble.fold(nt)
    # Step3. 替换占位符
    for value in bubble_map.values():
        for b in value:
            replace_placeholder(b, None, nt_node)
    return bubble_map, list(set().union(*bubble_map.values()))


def compress_bubble_map(bubble_map1: Dict[Bubble, List[Bubble]], bubble_map2: Dict[Bubble, List[Bubble]]):
    """
    压缩两个Bubble map
    :param bubble_map1:
    :param bubble_map2:
    :return:
    """
    bubble_map = defaultdict(list)
    for bubble1 in bubble_map1:
        for bubble2 in bubble_map1[bubble1]:
            for bubble3 in bubble_map2[bubble2]:
                bubble_map[bubble1].append(bubble3)
    return bubble_map


@timer('fold_bubbles')
def fold_bubbles(fold: Collection[Bubble], nt, bubbles: List[Bubble]):
    bubble_map = {bubble: [bubble] for bubble in bubbles}
    for bubble in sorted(fold, key=len, reverse=True):
        single_bubble_map, bubbles = fold_bubble(bubble, nt, bubbles)
        bubble_map = compress_bubble_map(bubble_map, single_bubble_map)
    return bubble_map, bubbles


@timer('build_matrix_by_lookup_c_wrapped')
def build_matrix_by_lookup_c_wrapped(
        n: int,
        row_map: List[int],
        col_map: List[int],
        matrix
) -> np.ndarray:
    return build_matrix_by_lookup_c(n, row_map, col_map, matrix.mat)



def reverse_map(m: Dict[Any, Collection[Any]]):
    reversed_m = {}
    for k, vs in m.items():
        for v in vs:
            reversed_m[v] = k
    return reversed_m


def reverse_multi_list_map(m: List[List[int]], n: int):
    reversed_m = [0] * n
    for k, vs in enumerate(m):
        for v in vs:
            reversed_m[v] = k
    return reversed_m


def reverse_list_map(lst: List):
    return {v: k for k, v in enumerate(lst)}


def translate_bubble_map(bubble_map: Dict[Bubble, Collection[Bubble]], old_bubbles, new_bubbles) -> List[List]:
    new_bubbles_inv = reverse_list_map(new_bubbles)
    return [[new_bubbles_inv[i] for i in bubble_map[bubble]] for bubble in old_bubbles]


@timer('update_con_sub')
def update_con_sub(nt_bubbles: List[int],
                   approx_cons: List[int],
                   approx_subs: List[int],
                   con_related_bubbles: Collection[int],
                   sub_related_bubbles: Collection[int],
                   cdm: CompressedDM):
    """
    更新上下文和子串
    :param nt_bubbles: nt相关的bubble
    :param approx_cons: 粗略的上下文
    :param approx_subs: 粗略的子串
    :param con_related_bubbles: 需要更新con的bubble
    :param sub_related_bubbles: 需要更新sub的bubble
    :param cdm: 压缩分布矩阵
    :return:
    """
    # 计算nt相关的上下文和子串
    nt_cons = {approx_cons[i] for i in nt_bubbles}
    nt_subs = {approx_subs[i] for i in nt_bubbles}
    # 更新相关的上下文和子串
    blocked_cons = [frozenset([i]) for i in approx_cons]
    blocked_subs = [frozenset([i]) for i in approx_subs]
    for i in con_related_bubbles:
        blocked_cons[i] |= nt_cons
    for i in sub_related_bubbles:
        blocked_subs[i] |= nt_subs
    # cdm进行压缩
    rows_map, cols_map = cdm.compress(blocked_subs, blocked_cons)
    # 获取更新后的
    new_subs = [rows_map[i] for i in blocked_subs]
    new_cons = [cols_map[i] for i in blocked_cons]
    return new_cons, new_subs


@timer('get_nt_dict')
def get_nt_dict(bubbles: Collection[Bubble]):
    nt_dict = defaultdict(set)
    for bubble in bubbles:
        if bubble.isNt():
            nt_dict[bubble.getNt()].add(bubble.start)
    return nt_dict


@timer('fold_bubbles_and_update')
def fold_bubbles_and_update(bubbles_fold, nt, old_bubbles, cons, subs, cdm):
    """

    :param cdm:
    :param bubbles_fold:
    :param nt:
    :param old_bubbles:
    :param cons:
    :param subs:
    :return:
    """
    """
    Step1. fold all Bubbles
    """
    with RecordTime('fold all Bubbles'):
        bubble_map, new_bubbles = fold_bubbles(bubbles_fold, nt, old_bubbles)
        n = len(new_bubbles)
        # 处理映射
        bubble_map_numeric = translate_bubble_map(bubble_map, old_bubbles, new_bubbles)
        inv_bubble_map_numeric = reverse_multi_list_map(bubble_map_numeric, n)
        inv_new_bubbles = reverse_list_map(new_bubbles)
    """
    Step2. construct approx con&sub map
    """
    with RecordTime('construct approx con&sub map'):
        approx_new_cons = [cons[inv_bubble_map_numeric[i]] for i in range(n)]
        approx_new_subs = [subs[inv_bubble_map_numeric[i]] for i in range(n)]
    """
    Step3. compute bubble need update con/sub
    """
    with RecordTime('compute bubble need update con/sub'):
        nt_dict = get_nt_dict(new_bubbles)
        with RecordTime('bubbles_update_subseq'):
            sub_related_bubbles = [inv_new_bubbles[i] for i in bubbles_update_subseq_iter(nt, nt_dict)]
        with RecordTime('bubbles_update_context'):
            con_related_bubbles = [inv_new_bubbles[i] for i in bubbles_update_context_iter(nt, nt_dict)]
    """
    Step4. 计算nt对应的bubble
    """
    with RecordTime('计算nt对应的bubble'):
        nt_bubbles = [inv_new_bubbles[Bubble(i, i)] for i in nt_dict[nt]]
    # Step5. 获取更新后的con/sub
    return new_bubbles, *update_con_sub(nt_bubbles,
                                        approx_new_cons,
                                        approx_new_subs,
                                        con_related_bubbles,
                                        sub_related_bubbles,
                                        cdm
                                        )


@timer('remove_conflict_inv')
def remove_conflict_inv(adj: np.ndarray, bubbles: List["Bubble"]):
    n = len(bubbles)

    # 缓存 ie
    ie_map: List[IntervalExample] = [b.getIE() for b in bubbles]

    # 1. 按 IE 分组
    ie_groups = defaultdict(list)
    for idx, ie in enumerate(ie_map):
        ie_groups[ie.example].append(idx)

    # 2. group 内部冲突检测
    for group in ie_groups.values():
        for i, j in itertools.combinations(group, 2):
            if isConflict(ie_map[i], ie_map[j]):
                adj[i, j] = adj[j, i] = 0


def evaluatePm(trees: List[Node], oracle):
    nt_dict = getNtDict(trees)
    cons_map = defaultdict(set)
    subs_map = defaultdict(set)
    for i in nt_dict:
        for node in nt_dict[i]:
            cons_map[i].add(node.getContext())
            subs_map[i].add(node.getSeq())
    examples = {tree.example for tree in trees}
    samples = set()
    max_retry = 1000 * 20
    while len(samples) < 1000 and max_retry > 0:
        max_retry -= 1
        nt = random.choice(list(nt_dict.keys()))
        random_con = random.choice(list(cons_map[nt]))
        random_sub = random.choice(list(subs_map[nt]))
        random_example = random_con.assembly(random_sub)
        if random_example in examples or random_example in samples:
            continue
        samples.add(random_example)
    passed = 0
    for sample in tqdm(samples):
        if oracle.parse(sample):
            passed += 1
    print('准确率=', passed / len(samples))




"""
1. cons/subs映射 int -> int
2. bubbles 映射 int -> bubble
3. bubbles的反向映射 bubble -> int
4. 多重映射 str -> set[xxx]
需要支持反转
"""
