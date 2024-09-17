from abc import ABC, abstractmethod
from typing import Any, List, Mapping, Optional

Child = Any
Attr = Mapping[str, Any]


class AbstractSSMLNode(ABC):
    """Abstract class (ABC) that represents a XML node of SSML.

    SSML: Speech Synthesis Markup Language
    """

    @abstractmethod
    def add(self, child: Child) -> "AbstractSSMLNode":
        """Adds a new node to SSML tree.

        @param child: Child node to be added in the tree.
        @returns: current node
        """

        ...

    @abstractmethod
    def __str__(self) -> str:
        """Returns tree nodes in a string representation"""

        ...


class SSMLNode(AbstractSSMLNode):
    """Concrete class used as a SSML Node that inherits from AbstractSSMLNode

    SSML: Speech Synthesis Markup Language

    @param tag: name of the tag to be on the string representation
    @param attrs: custom attributes to be added on the string representation
    @param children: list of childs to be added on initialization
    """

    def __init__(
        self,
        tag: str,
        attrs: Optional[Attr] = None,
        children: Optional[List[Child]] = None,
    ) -> None:
        self._tag = tag
        self._attrs = attrs or {}
        self._children = children or []

    def __str__(self) -> str:
        """Returns a string representation of text-to-speech using tags HTML like."""

        attrs = " ".join(f'{k}="{v}"' for k, v in self._attrs.items())
        rendered_children = "".join(str(c) for c in self._children)
        return f"<{self._tag}{(' ' if attrs else '')}{attrs}>{rendered_children}</{self._tag}>"

    def add(self, child: Child) -> "SSMLNode":
        """Adds a child with Any type to the children list property.

        @param child: child with Any type to be added to the children list
        @returns: current SSML node
        """

        self._children.append(child)
        return self

    def update_attributes(self, new_attrs: Attr):
        """Updates the attributes of the SSML node.

        @param new_attrs: Dictionary of attributes to update.
        """
        self._attrs.update(new_attrs)

    def clear_ssml(self):
        self._children = []
