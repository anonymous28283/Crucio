from abc import abstractmethod
from typing import TypeVar, Hashable, Callable, Optional

from crucio.decompose.decompose_forest import DeNode, DeForest
from crucio.decompose.decompose_forest.search import ForestSearcher

T = TypeVar("T", bound=Hashable)
K = TypeVar("K")


class SingleTreeSearchStrategy:

    @abstractmethod
    def search_tree(self, node: DeNode[T], condition: Callable[[T], Optional[K]]):
        pass


class MultiTreeSearchStrategy:

    @abstractmethod
    def search(self, condition: Callable[[T], Optional[K]]) -> Optional[DeNode[T]]:
        pass


class DefaultSTSS(SingleTreeSearchStrategy):
    def search_tree(self, node: DeNode[T], condition: Callable[[T], Optional[K]]):
        while True:
            for child in node.children():
                if not condition(child.value):
                    node = child
                    break
            else:
                break
        return node.value


class FeedbackSTSS(SingleTreeSearchStrategy):
    def __init__(self, feedback: Callable[[T, K], T]):
        self.feedback = feedback

    def search_tree(self, node, condition):
        while True:
            for child in node.children():
                understand = condition(child.value)
                if understand is None:
                    node = child
                    break
                else:
                    reduced = self.feedback(node.value, understand)
                    if reduced != node.value:
                        node = node.add_child(reduced)
                        break
            else:
                break
        return node.value


class DefaultMTSS(MultiTreeSearchStrategy):
    def __init__(self, forest: DeForest[T]):
        self.forest = forest

    def search(self, condition: Callable[[T], Optional[K]]) -> Optional[DeNode[T]]:
        for node in self.forest.roots:
            if condition(node.value):
                continue
            return node


class PriorQueueMTSS(MultiTreeSearchStrategy):
    def __init__(self, forest: DeForest[T]):
        self.forest = forest
        self.priority_map = {i.value: 0 for i in self.forest.roots}

    def _get_roots(self):
        return sorted(self.forest.get_roots(), key=lambda x: self.priority_map[x.value])

    def search(self, condition: Callable[[T], Optional[K]]) -> Optional[DeNode[T]]:
        for node in self._get_roots():
            if condition(node.value):
                self.priority_map[node.value] += 1
                continue
            return node


class PathCacheTSS(MultiTreeSearchStrategy, SingleTreeSearchStrategy):
    def search_tree(self, node: DeNode[T], condition: Callable[[T], Optional[K]]):
        self.__last = self.single.search_tree(node, condition)
        return self.__last

    def __init__(self, forest, multi: MultiTreeSearchStrategy, single: SingleTreeSearchStrategy):
        super().__init__()
        self.forest = multi
        self.__last = None
        self.multi = multi
        self.single = single
        self.forest = forest

    def search(self, condition: Callable[[T], Optional[K]]) -> T:
        if self.__last is not None:
            current = self.forest.get_node(self.__last)
            while condition(current.value) and current.parent:
                current = current.parent
            if not condition(current.value):
                return current
        return self.multi.search(condition)


class StrategyBasedSearcher(ForestSearcher):
    def __init__(self, multi: MultiTreeSearchStrategy, single: SingleTreeSearchStrategy, forest):
        super().__init__(forest)
        self._multi = multi
        self._single = single

    def search(self, condition: Callable[[T], Optional[K]]):
        node = self._multi.search(condition)
        if node is None:
            return None
        return self.search_tree(node, condition)

    def search_tree(self, node, condition):
        return self._single.search_tree(node, condition)


class PathCacheSBS(StrategyBasedSearcher):
    def __init__(self, multi: MultiTreeSearchStrategy, single: SingleTreeSearchStrategy,forest):
        super().__init__(multi, single, forest)
        self.__last = None

    def search_tree(self, node, condition):
        self.__last = self._single.search_tree(node,condition)
        return self.__last

    def __search_cache(self, condition):
        if self.__last is not None:
            current = self.forest.get_node(self.__last)
            while condition(current.value) and current.parent:
                current = current.parent
            if not condition(current.value):
                return self.search_tree(current, condition)

    def search(self, condition: Callable[[T], Optional[K]]):
        cached = self.__search_cache(condition)
        if cached is None:
            return super().search(condition)
        else:
            return cached


