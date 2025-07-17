import queue

from lark import Tree

from crucio.data_types import Symbol, Prod
from crucio.instantiate.node.core import SyntaxTree, SyntaxNode
from crucio.tokenize import Tokens, Token
from crucio.utils import str1


def getTreeProd(tree: Tree):
    children = [Symbol(i.data.value) if isinstance(i, Tree) else Symbol(Token(i.value)) for i in tree.children]
    return Prod(tree.data.value, tuple(children))


def larkTree2SyntaxNode(tree: Tree):
    root = SyntaxNode(Symbol(tree.data))
    pairQueue = queue.Queue()
    pairQueue.put((tree, root))
    while not pairQueue.empty():
        larkTree, node = pairQueue.get()
        if not isinstance(larkTree, Tree):
            continue
        larkTree: Tree
        node: SyntaxNode
        prod = getTreeProd(larkTree)
        node.produce(prod)
        for i, child in enumerate(node.getChildren()):
            pairQueue.put((larkTree.children[i], child))
    return root


def attachTokenValue(root: SyntaxNode, tokens: Tokens):
    class Helper:
        def __init__(self):
            self.__index = 0

        def rebuild(self, root: SyntaxNode):
            stack = [(root, 0)]
            visited = {}

            while stack:
                node, state = stack.pop()

                if state == 0:  # not processed node
                    if node.isTerminal():
                        token = tokens[self.__index]
                        self.__index += 1
                        new_node = SyntaxNode(Symbol(token))
                        visited[id(node)] = new_node
                    else:
                        stack.append((node, 1))
                        for child in reversed(node.getChildren()):
                            stack.append((child, 0))
                elif state == 1:
                    children = [visited[id(child)] for child in node.getChildren()]
                    node.setChildren(children)
                    node.setProd(
                        Prod(
                            node.getSymbol().getValue(),
                            tuple(child.getSymbol() for child in children)
                        )
                    )
                    visited[id(node)] = node

            return visited[id(root)]

    return Helper().rebuild(root)


class STParser:
    def __init__(self, grammar):
        self.__grammar = grammar
        self.__parser = grammar.getParser()

    def parse(self, tokens: Tokens):
        tree = self.__parser.parse(str1(tokens))
        root = larkTree2SyntaxNode(tree)
        return SyntaxTree(attachTokenValue(root.getChildren()[0], tokens), self.__grammar)

    def parseSafe(self, tokens: Tokens):
        try:
            tree = self.__parser.parse(str1(tokens))
            root = larkTree2SyntaxNode(tree)
            return SyntaxTree(attachTokenValue(root.getChildren()[0], tokens), self.__grammar)
        except:
            return None
