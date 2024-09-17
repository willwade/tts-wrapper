from . import AbstractSSMLNode, Child, SSMLNode


class BaseSSMLRoot(AbstractSSMLNode):
    def __init__(self) -> None:
        self._inner = SSMLNode("speak")
        self._root = self._inner

    def __str__(self) -> str:
        return str(self._root)

    def add(self, child: Child) -> "AbstractSSMLNode":
        self._inner.add(child)
        return self
