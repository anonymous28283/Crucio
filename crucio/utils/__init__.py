from typing import Any, Iterable
from crucio.consts import SEP
from colored import bg, attr


def str1(obj: Any):
    if isinstance(obj, Iterable):
        return ' '.join(map(str, obj))
    return str(obj)
def prettyTokens(t):
    return ''.join([i.value for i in t])


def title(s):
    print(bg('yellow') + SEP)
    print(s)
    print(SEP + attr('reset'))


def harmonic_mean(*args):
    """
    Calculate the harmonic mean of all the given arguments.

    Parameters:
        *args: A variable number of arguments, all must be positive numbers.

    Returns:
        float: The harmonic mean of the arguments.

    Raises:
        ValueError: If no arguments are provided or if any argument is non-positive.
    """
    if not args:
        raise ValueError("At least one argument is required to calculate the harmonic mean.")
    if any(x <= 0 for x in args):
        raise ValueError("All arguments must be positive numbers.")

    n = len(args)
    denominator = sum(1 / x for x in args)
    return n / denominator