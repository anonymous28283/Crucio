import time
from abc import abstractmethod
from typing import Optional, Hashable, Dict, Collection, TypeVar, Generic

from crucio.tokenize import Tokens

T = TypeVar('T', bound=Hashable)


class Oracle(Generic[T]):
    @abstractmethod
    def parse(self, obj: T) -> bool:
        raise Exception('Unimplemented method')


class StringOracle(Oracle[str]):
    @abstractmethod
    def parse(self, example: str) -> bool:
        raise Exception('Unimplemented method')


class TokenOracle(Oracle[Tokens]):
    @abstractmethod
    def parse(self, tokens: Tokens) -> bool:
        pass


class ExtendOracle(Oracle):


    @abstractmethod
    def batch(self, items: Collection[Hashable], desc='ParseBatch') -> Dict[Hashable, bool]:
        pass

    @abstractmethod
    def parse(self, obj: Hashable) -> bool:
        pass


class CachedOracle(Oracle[T]):
    def __init__(self, oracle: Oracle[T]):
        self.__oracle = oracle
        self.cache = {}
        self.call_time = 0
        self.calls = 0

    def parse(self, tokens: T) -> bool:
        if tokens not in self.cache:
            start = time.time()
            self.cache[tokens] = self.__oracle.parse(tokens)
            self.call_time += time.time() - start
            self.calls += 1
        return self.cache[tokens]

