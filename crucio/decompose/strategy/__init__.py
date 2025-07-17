from abc import abstractmethod
from typing import Iterator

from crucio.tokenize import Tokens


class DataDecomposer:
    @abstractmethod
    def decompose(self, tokens: Tokens) -> Iterator[Tokens]:
        pass
