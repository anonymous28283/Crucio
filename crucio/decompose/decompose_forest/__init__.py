from typing import Iterator, Iterable, Hashable, Dict, List, Callable, TypeVar, Generic, Optional

T = TypeVar("T", bound=Hashable)


class LazyList(Iterable, Generic[T]):
    def __init__(self, iterator: Iterator):
        self.__cached = []
        self.__iterator = iterator

    def add(self, value: T):
        self.__cached.append(value)

    def __iter__(self):
        for i in self.__cached:
            yield i
        for i in self.__iterator:
            self.__cached.append(i)
            yield i


class DeForest(Generic[T]):
    """
    DeForest: recursively strategy root nodes into a forest structure via func
    """

    def __init__(self, func: Callable[[T], Iterator[T]],
                 roots: List[T]) -> None:
        self.node_map: Dict[T, LazyList[T]] = {}
        self.parents: Dict[T, T] = {}
        self.dec_func = func
        self.roots = [self.get_node(i) for i in roots]

    def get_node(self, value: T, parent: Optional[T] = None) -> Optional["DeNode[T]"]:
        if value not in self.node_map:
            self.node_map[value] = LazyList(self.dec_func(value))
        if parent is not None:
            self.parents[value] = parent
        return DeNode(value, self)

    def get_roots(self) -> List["DeNode[T]"]:
        return self.roots

    def get_parent(self, value) -> Optional["DeNode[T]"]:
        parent_value = self.parents.get(value,None)
        if parent_value is None:
            return None
        return self.get_node(parent_value)


class DeNode(Generic[T]):
    def __init__(self, value: T, forest: DeForest[T]):
        self._value = value
        self._forest: DeForest[T] = forest

    @property
    def value(self) -> T:
        return self._value

    def children(self):
        for i in self._forest.node_map[self._value]:
            yield self._forest.get_node(i,self.value)

    @property
    def parent(self):
        return self._forest.get_parent(self.value)

    def add_child(self, value):
        self._forest.node_map[self._value].add(value)
        return self._forest.get_node(value,self.value)
