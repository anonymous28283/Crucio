from typing import Hashable, Dict, Optional, Collection

from crucio.oracle import ExtendOracle, Oracle


class NaiveExtendOracle(ExtendOracle):
    def __init__(self, oracle: Oracle):
        self.oracle = oracle

    def batch(self, items: Collection[Hashable], desc='ParseBatch') -> Dict[Hashable, bool]:
        from crucio.utils.global_bar import rqdm
        return {item: self.parse(item) for item in rqdm(items, desc)}

    def parse(self, item: Hashable) -> bool:
        return self.oracle.parse(item)
