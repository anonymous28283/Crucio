from typing import Callable

from crucio.dataset.meta import load_meta
from crucio.grammar_tool.Parser import STParser
from crucio.instantiate.node.core import SyntaxNode
from crucio.tokenize import TokenizedContext, Tokens



def traverse_with_context_iterative(
    node: SyntaxNode,
    all_tokens: Tokens,
    start_index: int,
    callback: Callable[[SyntaxNode, TokenizedContext], None]
) -> int:
    stack = []
    stack.append((node, start_index, 0, 0))  # 初始状态

    while stack:
        current_node, current_start_index, child_index, processed_tokens = stack.pop()

        if current_node.isTerminal():
            # 对于终结符，直接计算上下文并回调
            context = TokenizedContext(
                tuple(all_tokens[:current_start_index]),
                tuple(all_tokens[current_start_index + 1:])
            )
            callback(current_node, context)
            processed_tokens = 1  # 终结符占 1 个 Token

            if stack:
                # 更新父节点的累计 Token 数量
                parent = stack.pop()
                stack.append((parent[0], parent[1], parent[2], parent[3] + processed_tokens))
            continue

        # 非终结符
        children = current_node.getChildren()
        if child_index < len(children):
            child_node = children[child_index]
            stack.append((current_node, current_start_index, child_index + 1, processed_tokens))
            stack.append((child_node, current_start_index + processed_tokens, 0, 0))
        else:
            total_tokens_for_node = processed_tokens
            context = TokenizedContext(
                tuple(all_tokens[:current_start_index]),
                tuple(all_tokens[current_start_index + total_tokens_for_node:])
            )
            callback(current_node, context)

            if stack:
                parent = stack.pop()
                stack.append((parent[0], parent[1], parent[2], parent[3] + total_tokens_for_node))

    return processed_tokens
def extractCS(node: SyntaxNode):
    ans = []

    def record(node: SyntaxNode, context: TokenizedContext) -> None:
        if not node.isTerminal():
            ans.append((node.toTokens(), context,node.getSymbol().getValue()))

    all_tokens = node.toTokens()  # 获取整个树的 Token 列表
    traverse_with_context_iterative(node, all_tokens, 0, record)
    return ans


if __name__ == '__main__':
    meta = load_meta('tinyc')
    parser = STParser(meta.grammar)
    tree = parser.parse(meta.getTokenizer().tokenize('if(a);'))
    for i in extractCS(tree.getRoot()):
        print(i)