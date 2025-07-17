from graphviz import Digraph
from matplotlib import image as mpimg

from crucio.tokenize import Token


def visualize_forest(roots, filename="syntax_forest", highlight_nodes=None):
    dot = Digraph()
    visited = set()
    highlight_ids = set(id(n) for n in highlight_nodes) if highlight_nodes else set()

    def node_id(node):
        return str(id(node))

    def node_label(node):
        if isinstance(node.value, Token):
            return node.value.value
        return str(node.value)

    def dfs(node):
        if node is None or id(node) in visited:
            return
        visited.add(id(node))
        nid = node_id(node)
        if id(node) in highlight_ids:
            dot.node(nid, node_label(node), style='filled', fillcolor='yellow')
        else:
            dot.node(nid, node_label(node))
        for child in node.children():
            dfs(child)
            cid = node_id(child)
            if id(child) in highlight_ids:
                dot.node(cid, node_label(child), style='filled', fillcolor='yellow')
            else:
                dot.node(cid, node_label(child))
            dot.edge(nid, cid)

    for root in roots:
        dfs(root)

    out_path = dot.render(filename, format='png', view=False)
    print(f"Saved {out_path}")

    img = mpimg.imread(out_path)
    return img

def visualize_node_tree(root, filename="syntax_tree", highlight_nodes=None):
    dot = Digraph()
    visited = set()
    highlight_ids = set(id(n) for n in highlight_nodes) if highlight_nodes else set()

    def node_id(node):
        return str(id(node))

    def node_label(node):
        if isinstance(node.value, Token):
            return node.value.value
        return str(node.value)

    def dfs(node):
        if node is None or id(node) in visited:
            return
        visited.add(id(node))
        nid = node_id(node)
        if id(node) in highlight_ids:
            dot.node(nid, node_label(node), style='filled', fillcolor='yellow')
        else:
            dot.node(nid, node_label(node))
        for child in node.children():
            cid = node_id(child)
            if id(child) in highlight_ids:
                dot.node(cid, node_label(child), style='filled', fillcolor='yellow')
            else:
                dot.node(cid, node_label(child))
            dot.edge(nid, cid)
            dfs(child)

    dfs(root)

    out_path = dot.render(filename, format='png', view=False)
    print(f"Saved {out_path}")

    img = mpimg.imread(out_path)
    return img