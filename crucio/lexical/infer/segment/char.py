from typing import List

from crucio.data_types.lexical import Segmentation


def segment_by_char(examples: List[str]):
    segs = []
    for example in examples:
        segs.append(Segmentation(tuple(i for i in example)))
    return segs
