"""The tree data model — :class:`Node` and :class:`Tree`.

Structure and traversal only: a tree knows its shape and its branch lengths, and nothing about how it
is laid out or drawn. Nodes keep an ordinary ``__dict__`` (no ``__slots__``), so a layout can annotate
them with coordinates without the tree type ever hearing about drawing.
"""

from __future__ import annotations

from typing import Iterator


class Node:
    """One vertex of a tree: a ``name``, the branch ``length`` up to its parent, and ordered
    ``children``. A leaf has no children; the root has no parent."""

    def __init__(self, name: str | None = None, length: float = 0.0) -> None:
        self.name = name
        self.length = float(length)
        self.parent: Node | None = None
        self.children: list[Node] = []

    @property
    def is_leaf(self) -> bool:
        return not self.children

    @property
    def is_root(self) -> bool:
        return self.parent is None

    def add_child(self, child: "Node") -> "Node":
        """Attach ``child`` below this node (setting its ``parent``) and return it."""
        child.parent = self
        self.children.append(child)
        return child

    def __repr__(self) -> str:
        shape = "leaf" if self.is_leaf else f"{len(self.children)} children"
        return f"Node({self.name!r}, length={self.length:g}, {shape})"


class Tree:
    """A rooted tree, reached through its ``root`` node."""

    def __init__(self, root: Node) -> None:
        self.root = root

    def walk(self, order: str = "preorder") -> Iterator[Node]:
        """Iterate over every node. ``order`` is ``"preorder"`` (a node before its children) or
        ``"postorder"`` (children before their node)."""
        if order == "preorder":
            stack = [self.root]
            while stack:
                node = stack.pop()
                yield node
                stack.extend(reversed(node.children))
        elif order == "postorder":
            yield from self._postorder(self.root)
        else:
            raise ValueError(f"order must be 'preorder' or 'postorder', got {order!r}")

    def _postorder(self, node: Node) -> Iterator[Node]:
        for child in node.children:
            yield from self._postorder(child)
        yield node

    @property
    def leaves(self) -> list[Node]:
        """Every terminal node, in left-to-right order."""
        return [node for node in self.walk() if node.is_leaf]

    def find(self, name: str) -> Node | None:
        """The first node with this ``name``, or ``None`` if there is none."""
        return next((node for node in self.walk() if node.name == name), None)

    def depth(self, node: Node) -> float:
        """Root-to-node distance: the branch lengths summed from the root down to ``node``.

        The root's own ``length`` — its *stem*, the branch before the first split — is **excluded**, so
        the root sits at depth 0 and the tree starts at the left of a layout. The stem is still kept on
        ``root.length`` for anyone who wants to draw it; it just never shifts the rest of the tree.
        """
        distance = 0.0
        while node.parent is not None:
            distance += node.length
            node = node.parent
        return distance

    def __repr__(self) -> str:
        return f"Tree(root={self.root!r}, {len(self.leaves)} leaves)"
