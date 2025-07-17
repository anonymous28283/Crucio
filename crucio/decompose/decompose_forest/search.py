from abc import abstractmethod
from typing import Callable, TypeVar, Generic, Hashable, Optional

T = TypeVar("T", bound=Hashable)
K = TypeVar("K")


class ForestSearcher(Generic[T]):
    def __init__(self, forest):
        self.forest = forest

    @abstractmethod
    def search(self, condition: Callable[[T], Optional[K]]):
        pass

    @abstractmethod
    def search_tree(self, node, condition):
        pass


class DefaultSearcher(ForestSearcher[T]):
    def search(self, condition: Callable[[T], Optional[K]]) -> T:
        for node in self.forest.roots:
            if condition(node.value):
                continue
            return self.search_tree(node, condition)

    def search_tree(self, node, condition):
        while True:
            for child in node.children():
                if not condition(child.value):
                    node = child
                    break
            else:
                break
        return node.value


class BarDefaultSearcher(DefaultSearcher[T]):
    def search_tree(self, node, condition):
        print('search decomposition tree')
        while True:
            print(len(node.value))
            for child in node.children():
                if not condition(child.value):
                    node = child
                    break
            else:
                break
        return node.value


class PathCacheSearcher(ForestSearcher[T]):
    def search_tree(self, node, condition):
        return self.__searcher.search_tree(node, condition)

    def __init__(self, searcher: ForestSearcher[T]):
        super().__init__(searcher.forest)
        self.__searcher = searcher
        self.__last = None

    def search(self, condition: Callable[[T], Optional[K]]) -> T:
        if self.__last is not None:
            current = self.forest.get_node(self.__last)
            while condition(current.value) and current.parent:
                current = current.parent
            if not condition(current.value):
                self.__last = self.search_tree(current, condition)
                return self.__last
        self.__last = self.__searcher.search(condition)
        return self.__last

class BarPathCacheSearcher(ForestSearcher[T]):
    def search_tree(self, node, condition):
        return self.__searcher.search_tree(node, condition)

    def __init__(self, searcher: ForestSearcher[T]):
        super().__init__(searcher.forest)
        self.__searcher = searcher
        self.__last = None

    def get_path(self):
        path = [self.forest.get_node(self.__last)]
        while path[-1].parent is not None:
            path.append(path[-1].parent)
        return path
    def search(self, condition: Callable[[T], Optional[K]]) -> T:
        if self.__last is not None:
            report = ''
            report += f'recover from '
            path = self.get_path()
            with TaskProgress(len(path),f'Search={len(path[0].value)}') as tp:
                for node in path:
                    report += f'{len(node.value)}->'
                    tp.advance(1,f'Search={len(node.value)}')
                    if not condition(node.value):
                        self.__last = self.search_tree(node, condition)
                        report += 'passed'
                        print(report)
                        return self.__last
                report += 'failed'
                print(report)
        self.__last = self.__searcher.search(condition)
        return self.__last


class PrioritySearcher(ForestSearcher[T]):
    def search_tree(self, node, condition):
        return self.__searcher.search_tree(node, condition)

    def __init__(self, searcher: ForestSearcher[T]):
        super().__init__(searcher.forest)
        self.priority_map = {i.value: 0 for i in self.forest.roots}
        self.__searcher = searcher

    def _get_roots(self):
        return sorted(self.forest.get_roots(), key=lambda x: self.priority_map[x.value])

    def search(self, condition: Callable[[T], Optional[K]]) -> T:
        for node in self._get_roots():
            if condition(node.value):
                self.priority_map[node.value] += 1
                continue
            return self.search_tree(node, condition)


from crucio.utils.global_bar import TaskProgress


class BarPrioritySearcher(PrioritySearcher):
    def __init__(self, searcher: ForestSearcher[T],desc='解析数量'):
        super().__init__(searcher)
        self.__bar = TaskProgress(total=len(self.priority_map),initial_description=desc)
        self.__bar.__enter__()

    def get_progress(self):
        return len(list(filter(lambda x: self.priority_map[x] > 0, self.priority_map)))

    def search(self, condition):
        ans = super().search(condition)
        n = self.get_progress()
        self.__bar.set_current(n)
        if ans is None:
            self.__bar.__exit__(None, None, None)
        return ans
