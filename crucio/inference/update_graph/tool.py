from crucio.inference.tree import Bubble


def getRoot(bubble: Bubble):
    root = bubble.start
    while root.parent is not None:
        root = root.parent
    return root
