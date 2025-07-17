from typing import List

from crucio.data_types.lexical import Segmentation
from crucio.oracle.string import CachedStringOracle


def replace_seg(seg, target, replacement):
    ret = ''
    for i in seg.slices:
        if i == target:
            ret += replacement
        else:
            ret += i
    return ret


def is_char_sensitive(char, segs: List[Segmentation], oracle: CachedStringOracle):
    from crucio.utils.global_bar import rqdm
    if all(char not in seg.slices for seg in segs):
        return True
    elif all(oracle.parse(replace_seg(seg, char, char + char)) for seg in rqdm(segs, desc=f'{repr(char)}Sensitivity')):

        if char != ' ':
            return not all(oracle.parse(replace_seg(i, char, ' ')) for i in rqdm(segs, desc=f'{repr(char)}Sensitivity2'))
        return False
    else:
        return True


def get_insensitive_chars(segs: List[Segmentation], oracle: CachedStringOracle) -> List[str]:
    ans = []
    for char in ' \t\n\r':
        if not is_char_sensitive(char, segs, oracle):
            ans.append(char)
    return ans
