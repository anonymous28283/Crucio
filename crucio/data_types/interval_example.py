from dataclasses import dataclass

from colored import attr, bg

from crucio.tokenize import Tokens, Token, TokenizedContext
from crucio.utils import str1
from crucio.utils.statistics import timer


@dataclass(frozen=True, eq=True)
class IntervalExample:
    example: Tokens
    left: int
    right: int

    def __str__(self):
        return str1(self.prefix() + (Token('#'),) + self.value() + (Token('#'),) + self.suffix())

    def pretty(self, bg_color="green"):
        reset = attr("reset")  # Reset color styles
        pretty_value = "".join(f"{bg(bg_color)} {str(token)} {reset}" for token in self.value())
        return str1(self.prefix() + (Token(pretty_value),) + self.suffix())

    def assembly(self, ie: "IntervalExample"):
        return self.prefix() + ie.value() + self.suffix()

    def prefix(self):
        return self.example[:self.left]

    def value(self):
        return self.example[self.left:self.right]

    def suffix(self):
        return self.example[self.right:]

    def context(self):
        return TokenizedContext(self.prefix(), self.suffix())


@timer('isConflict')
def isConflict(a: IntervalExample, b: IntervalExample) -> bool:
    if a.example != b.example:
        return False  # not same example
    if a.right <= b.left or b.right <= a.left:
        return False  # not overlap
    if (a.left <= b.left and a.right >= b.right) or (b.left <= a.left and b.right >= a.right):
        return False  # is subset
    return True  # overlap and not subset


