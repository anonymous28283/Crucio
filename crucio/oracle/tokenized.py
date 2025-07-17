from typing import Dict, Collection
from typing import Union, Optional

import dill

from crucio.instantiate.TokenIns import TokenInstantiator
from crucio.oracle import TokenOracle
from crucio.oracle.string import CachedStringOracle
from crucio.tokenize import Tokens
from crucio.utils.statistics import counter, timer

dill.settings['recurse'] = True


class TokenizedOracle(TokenOracle):
    def raw(self):
        return self._oracle

    @timer('TokenizedOracle build')
    def __init__(self, rawOracle: CachedStringOracle, tokenInstantiator: TokenInstantiator):
        self._ti: Optional[TokenInstantiator] = tokenInstantiator
        self._oracle = rawOracle

    def ins(self, x):
        return self._ti.instantiate(x)

    def getIns(self):
        return self._ti

    @counter('TokenizedOracle')
    def parse(self, tokens: Union[Tokens]) -> bool:
        return self._oracle.parse(self._ti.instantiate(tokens))


class CachedTokenOracle(TokenOracle):
    def __init__(self, oracle: TokenOracle):
        self.oracle = oracle
        self.cache = {}

    def update_oracle(self, oracle: TokenOracle):
        self.oracle = oracle

    def parse(self, tokens: Tokens) -> bool:
        if tokens not in self.cache:
            self.cache[tokens] = self.oracle.parse(tokens)
        return self.cache[tokens]

    def get_positives(self):
        return {k for k, v in self.cache.items() if v}

    def update_cache(self, cache: Dict):
        self.cache.update(cache)


class IncrementalOracle(TokenOracle):
    def __init__(self, oracle: TokenOracle):
        self.oracle = oracle
        self.cache = set()

    def update_oracle(self, oracle: TokenOracle):
        self.oracle = oracle

    def parse(self, tokens: Tokens) -> bool:
        if tokens in self.cache:
            return True
        ans = self.oracle.parse(tokens)
        if ans:
            self.cache.add(tokens)
        return ans

    def update_cache(self, cache: Collection):
        self.cache.update(cache)
