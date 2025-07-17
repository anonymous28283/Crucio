import queue
from typing import List, Union

from colored import bg, attr

from crucio.data_types import Prod, Symbol, Grammar
from crucio.tokenize import Token, Tokens

TAB = '  '


class SyntaxNode:
    def __init__(self, symbol: Symbol, prod: Prod = None) -> None:
        assert symbol is not None
        self._symbol = symbol
        self._prod = prod
        if prod is not None:
            assert not self._symbol.isTerminal() and self._symbol.getValue() == self._prod.getNt()
        self._subNodes = [SyntaxNode(symbol) for symbol in prod] if prod is not None else []

    def getProd(self):
        return self._prod

    def getProds(self):
        if self._prod is None:
            return set()
        prods = {self._prod}
        for subNode in self._subNodes:
            prods = prods.union(subNode.getProds())
        return prods

    def isFree(self):
        return not self.isTerminal() and self._prod is None

    def getSymbol(self):
        return self._symbol

    def isTerminal(self):
        return self._symbol.isTerminal()

    def __eq__(self, value: "SyntaxNode") -> bool:
        return self.toTokens() == value.toTokens()
        # return str(self) == str(value)

    def __hash__(self) -> int:
        return hash(self.toTokens())
        # return hash(str(self))

    def __str__(self) -> str:
        if self.getProd() is None:
            if not self._symbol.isTerminal():
                return bg('blue') + str(self._symbol) + attr('reset')
            return str(self._symbol)
        ret = [bg('blue') + self._prod.getNt() + attr('reset') + ':']
        for subNode in self._subNodes:
            ret.append('\n'.join([TAB + i for i in str(subNode).split('\n')]))
        return '\n'.join(ret)

    def produce(self, prod: Prod):
        assert self._prod is None
        self._prod = prod
        self._subNodes = [SyntaxNode(symbol) for symbol in prod]

    def getChildren(self) -> List["SyntaxNode"]:
        return self._subNodes

    def setProd(self, prod: Prod):
        self._prod = prod

    def setChildren(self, children: List["SyntaxNode"]):
        self._subNodes = children

    def copy(self):
        # 创建根节点副本
        ret = SyntaxNode(self.getSymbol(), self.getProd())

        # 栈用于管理待处理节点（原节点与对应的副本节点）
        stack = [(self, ret)]

        while stack:
            original, copy = stack.pop()
            copy._subNodes = []
            # 遍历原节点的子节点
            for sub_node in original._subNodes:
                # 创建子节点的副本
                sub_node_copy = SyntaxNode(sub_node.getSymbol(), sub_node.getProd())
                # 添加到当前副本的 _subNodes 列表
                copy._subNodes.append(sub_node_copy)
                # 将子节点和对应的副本节点压入栈，继续处理
                stack.append((sub_node, sub_node_copy))

        return ret

    def __toTokens(self) -> List[Token]:
        if self.isTerminal():
            return [self.getSymbol().getValue()]
        if self._prod is None:
            print('symbol=', self._symbol)
            raise Exception("Not Complete Syntax Tree")

        stack = [(self, 0)]  # 栈存储 (节点, 当前处理的符号索引)
        result = []

        while stack:
            node, index = stack.pop()

            # 如果节点是终结符，直接加入结果
            if node.isTerminal():
                result.append(node.getSymbol().getValue())
                continue

            if node._prod is None:
                print('symbol=', node._symbol)
                raise Exception("Not Complete Syntax Tree")

            # 如果索引小于当前节点的符号数，处理符号
            if index < len(node._prod):
                symbol = node._prod[index]

                # 将当前节点和下一个符号的索引推回堆栈
                stack.append((node, index + 1))

                if symbol.isTerminal():
                    # 如果是终结符，直接加入结果
                    result.append(symbol.getValue())
                else:
                    # 如果是非终结符，将子节点推入堆栈
                    stack.append((node.getChildren()[index], 0))

        return result

    def toTokens(self) -> Tokens:
        return tuple(self.__toTokens())


class StaticSyntaxNode(SyntaxNode):
    def __init__(self, sn: SyntaxNode) -> None:
        super().__init__(sn.getSymbol(), sn.getProd())
        self._subNodes = tuple(StaticSyntaxNode(i) for i in sn._subNodes)
        self._str = None

    def __str__(self) -> str:
        if self._str is not None:
            return self._str
        if self.getProd() is None:
            if not self._symbol.isTerminal():
                self._str = bg('blue') + str(self._symbol) + attr('reset')
                return self._str
            self._str = str(self._symbol)
            return self._str
        ret = [bg('blue') + self._prod.getNt() + attr('reset') + ':']
        for subNode in self._subNodes:
            ret.append('\n'.join([TAB + i for i in str(subNode).split('\n')]))
        self._str = '\n'.join(ret)
        return self._str

    def produce(self, prod: Prod):
        raise Exception('Static Syntax node is Not Producable')

    def getChildren(self) -> List["SyntaxNode"]:
        return list(self._subNodes)

    def copy(self):
        import copy
        ret = StaticSyntaxNode(self)
        ret._subNodes = copy.deepcopy(self._subNodes)
        return ret


class SyntaxTree:
    def __init__(self, root: Union[str, SyntaxNode], grammar: Grammar) -> None:
        if isinstance(root, str):
            self.__root = SyntaxNode(Symbol(root))
        else:
            self.__root = root.copy()
        self.__grammar = grammar

    def getGrammar(self):
        return self.__grammar

    def getRoot(self):
        return self.__root

    def getProds(self):
        return self.__root.getProds()

    def __str__(self) -> str:
        return str(self.getRoot())

    def toTokens(self):
        return self.__root.toTokens()

    def getFreeNodes(self) -> List["SyntaxNode"]:
        """
        穷举所有节点，选取其中可以grow的节点
        :return:
        """
        ret = []
        q = queue.Queue()
        q.put(self.__root)
        while not q.empty():
            node: SyntaxNode = q.get()
            if node.isFree():
                ret.append(node)
            elif not node.isTerminal():
                for subNode in node.getChildren():
                    q.put(subNode)
        return ret

    def copy(self) -> "SyntaxTree":
        ret = SyntaxTree('', self.__grammar)
        ret.__root = self.__root.copy()
        return ret


class SyntaxForest:
    def __init__(self, roots: List["SyntaxNode"]) -> None:
        self.__roots = roots

    def getRoots(self) -> List["SyntaxNode"]:
        return self.__roots

    def __str__(self):
        return "\n".join(map(str, self.__roots))
