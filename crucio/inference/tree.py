from collections import defaultdict
from dataclasses import dataclass
from typing import List, Union, Optional

from colored import bg, attr

from crucio.data_types import Prod, Symbol, Grammar
from crucio.data_types.interval_example import IntervalExample
from crucio.tokenize import Token, Tokens, TokenizedContext
from crucio.utils.statistics import timer


@dataclass
class Node:
    value: Union[Token, str, None] = None
    index: Optional[int] = None
    example: Tokens = None
    left: Optional["node"] = None
    right: Optional["node"] = None
    child: Optional["node"] = None
    parent: Optional["node"] = None
    lm = None
    rm = None

    def getProds(self):
        if self.child is None:
            return []
        ans = []
        nt = self.value
        ans.append(Prod(nt, tuple(Symbol(child.value) for child in self.children())))
        for child in self.children():
            ans.extend(child.getProds())
        return ans

    def getContext(self):
        if self.child is not None and self.child.right.right is None:
            return TokenizedContext((), ())
        leftmost = self.leftmost()
        rightmost = self.rightmost()
        example = leftmost.example
        prefix = example[:leftmost.index]
        suffix = example[rightmost.index + 1:]
        return TokenizedContext(prefix, suffix)

    def children(self):
        if self.child is None:
            return []
        first = self.child.right
        while first.right is not None:
            yield first
            first = first.right

    @timer('lookup')
    def lookup(self, nt):
        if self.child is None:
            return []
        ans = []
        if self.value == nt:
            ans.append(self)
        for child in self.children():
            ans.extend(child.lookup(nt))
        return ans

    def isTerminal(self):
        return isinstance(self.value, Token)

    def leftmost(self):
        if self.lm is not None:
            return self.lm
        if self.child is None:
            return self
        self.lm = self.child.right.leftmost()
        return self.lm

    def rightmost(self):
        if self.rm is not None:
            return self.rm
        if self.child is None:
            return self
        first = self.child
        while first.right.right is not None:
            first = first.right
        self.rm = first.rightmost()
        return self.rm

    def getSeq(self):
        if self.child is not None and self.child.right.right is None:
            return ()
        leftmost = self.leftmost()
        rightmost = self.rightmost()
        return leftmost.example[leftmost.index:rightmost.index + 1]

    def bubbling(self):
        if self.child is None:
            return []
        bubbles = []
        first = self.child.right
        while first.right is not None:
            second = first
            while second.right is not None:
                bubbles.append(Bubble(first, second))
                second = second.right
            first = first.right
        first = self.child.right
        while first.right is not None:
            bubbles.extend(first.bubbling())
            first = first.right
        return bubbles

    def pretty(self, indent: str = "", is_last: bool = True):
        connector = "└── " if is_last else "├── "
        print(f"{indent}{connector}{repr(self.value)}")

        child_indent = indent + ("    " if is_last else "│   ")

        children = []
        if self.child:
            children.append(('child', self.child))

        for i, (label, node) in enumerate(children):
            is_last_child = i == len(children) - 1
            print(f"{child_indent}({label})")
            node.pretty(child_indent, is_last_child)

        if self.right:
            self.right.pretty(indent, is_last)


    def pretty0(self, indent: str = "", is_last: bool = True):
        connector = "└── " if is_last else "├── "
        ans = ''
        ans += (f"{indent}{connector}{repr(self.value)}") + '\n'

        child_indent = indent + ("    " if is_last else "│   ")

        children = []
        if self.child:
            children.append(('child', self.child))

        for i, (label, node) in enumerate(children):
            is_last_child = i == len(children) - 1
            ans += f"{child_indent}({label})" + '\n'
            ans += node.pretty0(child_indent, is_last_child)

        if self.right:
            ans += self.right.pretty0(indent, is_last)
        return ans

    def pretty_highlight(self, start: "node", end: "node", indent: str = "", is_last: bool = True,
                         in_range: bool = False):

        if self is start:
            in_range = True
        highlight = in_range
        if self is end:
            highlight = True
            next_in_range = False
        else:
            next_in_range = in_range

        connector = "└── " if is_last else "├── "
        value_str = repr(self.value)
        if highlight:
            value_str = f"{bg('yellow')}{attr('bold')}{value_str}{attr('reset')}"
        print(f"{indent}{connector}{value_str}")

        children = []
        if self.child: children.append(('child', self.child))

        child_indent = indent + ("    " if is_last else "│   ")
        for i, (label, node) in enumerate(children):
            is_last_child = (i == len(children) - 1)
            print(f"{child_indent}({label})")
            node.pretty_highlight(start, end, child_indent, is_last_child, next_in_range)

        if self.right:
            self.right.pretty_highlight(start, end, indent, is_last, next_in_range)


    def pretty_highlight0(self, start: "node", end: "node", indent: str = "", is_last: bool = True,
                         in_range: bool = False):

        ans = ''
        if self is start:
            in_range = True
        highlight = in_range
        if self is end:
            highlight = True
            next_in_range = False
        else:
            next_in_range = in_range

        connector = "└── " if is_last else "├── "
        value_str = repr(self.value)
        if highlight:
            value_str = f"{bg('yellow')}{attr('bold')}{value_str}{attr('reset')}"
        ans += f"{indent}{connector}{value_str}" +'\n'

        children = []
        if self.child: children.append(('child', self.child))

        child_indent = indent + ("    " if is_last else "│   ")
        for i, (label, node) in enumerate(children):
            is_last_child = (i == len(children) - 1)
            ans += f"{child_indent}({label})" +'\n'
            ans += node.pretty_highlight0(start, end, child_indent, is_last_child, next_in_range)

        if self.right:
            ans += self.right.pretty_highlight0(start, end, indent, is_last, next_in_range)
        return ans

    def __eq__(self, other):
        return id(self) == id(other)

    def __hash__(self):
        return hash(id(self))

@dataclass
class Bubble:
    start: Node
    end: Node
    @property
    def nodes(self):
        ret = []
        first = self.start
        while first!=self.end:
            ret.append(first)
            first = first.right
        return ret + [ first]
    def getNt(self):
        assert self.isNt()
        return self.start.value
    def isNt(self):
        return self.start is self.end and not self.start.isTerminal()
    def isProd(self):
        if self.parent.parent is None:
            return False
        return self.start.left.left is None and self.end.right.right is None and self.parent is not None
    @property
    def parent(self):
        return self.start.parent

    def __len__(self):
        start = self.start
        n = 1
        while start != self.end:
            start = start.right
            n += 1
        return n

    def __hash__(self):
        return hash((id(self.start), id(self.end)))

    def __eq__(self, other):
        return self.start is other.start and self.end is other.end

    def fold(self, nt):
        leftBound = self.start.left
        rightBound = self.end.right
        #print(leftBound)
        #print(rightBound)
        newNode = Node(nt)
        newNode.parent = self.start.parent
        rightBound.left = leftBound.right = newNode
        newNode.left = leftBound
        newNode.right = rightBound
        newNode.child = Node()
        newNode.child.parent = newNode
        newNode.child.right = self.start

        self.start.left = newNode.child
        self.end.right = Node()
        self.end.right.parent = newNode
        self.end.right.left = self.end

        current = self.start
        while current.right is not None:
            current.parent = newNode
            current = current.right
        return newNode

    def pretty(self):
        context = self.getContext()
        seq = self.getSeq()
        return IntervalExample(context.assembly(seq), len(context.getPrefix()),
                               len(context.getPrefix() + seq)).pretty()

    @timer('getSeq')
    def getSeq(self):
        leftmost = self.start.leftmost()
        rightmost = self.end.rightmost()
        return leftmost.example[leftmost.index:rightmost.index + 1]
    @timer('getContext')
    def getContext(self):
        leftmost = self.start.leftmost()
        rightmost = self.end.rightmost()
        example = leftmost.example
        prefix = example[:leftmost.index]
        suffix = example[rightmost.index + 1:]
        return TokenizedContext(prefix, suffix)

    @timer('getIE')
    def getIE(self):
        leftmost = self.start.leftmost()
        rightmost = self.end.rightmost()
        example = leftmost.example
        return IntervalExample(example,leftmost.index,rightmost.index+1)

    @timer('getValues')
    def getValues(self, ntDict):
        if self.start == self.end and not self.start.isTerminal():

            nts = {self.start.value}
            while True:
                before = len(nts)
                for nt in set(nts):
                    for tree in ntDict[nt]:
                        from crucio.inference.update_graph.envs.util import get_lower, get_uppers
                        lower = get_lower(Bubble(tree,tree))
                        for i in lower:
                            if i.start is i.end and not i.start.isTerminal():
                                nts.add(i.start.value)
                if len(nts) == before:
                    break
            values = []
            for nt in nts:
                for tree in ntDict[nt]:
                    tree: Node
                    values.append(tree.getSeq())
            return values
        else:
            return [self.getSeq()]



def buildTree(example: Tokens, start='n0'):
    node = Node(start)
    node.child = Node()
    node.child.parent = node
    current = node.child
    for index, token in enumerate(example):
        current.right = Node(token, index, example)
        current.right.left = current
        current.right.parent = node
        current = current.right
    current.right = Node()
    current.right.left = current
    current.right.parent = node
    return node


def buildGrammar(forest: List[Node], start='n0'):
    g = Grammar(start, [])
    for tree in forest:
        for prod in tree.getProds():
            g.addProd(prod)
    return g

def getNtDict(trees):
    ntDict = defaultdict(list)
    def visit(tree:Node):
        if not tree.isTerminal():
            ntDict[tree.value].append(tree)
        for child in tree.children():
            visit(child)
    for tree in trees:
        visit(tree)
    return ntDict
