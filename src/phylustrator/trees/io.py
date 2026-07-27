"""Newick I/O — the only tree format Phylustrator reads or writes.

``read`` / ``loads`` turn a file / string into a :class:`~phylustrator.tree.Tree`; ``write`` / ``dumps``
turn one back. The format is standard Newick with named internal nodes and branch lengths, e.g.
``((A:1,B:1)C:2,D:3)R:0.5;``. Quoted ``'labels'`` and ``[comments]`` are handled, and the root may
carry a stem length (``…)R:0.5;``).
"""

from __future__ import annotations

from pathlib import Path

from .tree import Node, Tree

__all__ = ["read", "loads", "write", "dumps"]

_SPECIAL = set(":,()[];")


def read(path: str | Path) -> Tree:
    """Parse a Newick file into a :class:`Tree`."""
    return loads(Path(path).read_text())


def loads(text: str) -> Tree:
    """Parse a Newick string into a :class:`Tree`."""
    return _Parser(text).parse()


def write(tree: Tree, path: str | Path) -> None:
    """Write a :class:`Tree` to a Newick file."""
    Path(path).write_text(dumps(tree))


def dumps(tree: Tree) -> str:
    """Serialise a :class:`Tree` to a one-line Newick string (with trailing ``;``)."""
    return _emit(tree.root) + ";\n"


# --- serialisation --------------------------------------------------------

def _emit(node: Node) -> str:
    label = _quote(node.name) if node.name else ""
    # The root's stem is written only when it is non-zero; interior/leaf lengths always are.
    length = "" if (node.is_root and node.length == 0.0) else f":{node.length:g}"
    if node.is_leaf:
        return f"{label}{length}"
    inner = ",".join(_emit(child) for child in node.children)
    return f"({inner}){label}{length}"


def _quote(name: str) -> str:
    if any(ch in name for ch in " ,():;'[]\t"):
        return "'" + name.replace("'", "''") + "'"
    return name


# --- parsing --------------------------------------------------------------

class _Parser:
    """A small recursive-descent Newick parser."""

    def __init__(self, text: str) -> None:
        self.s = text
        self.i = 0

    def parse(self) -> Tree:
        root = self._subtree()
        self._skip()
        if self._at() == ";":
            self.i += 1
        return Tree(root)

    def _subtree(self) -> Node:
        node = Node()
        self._skip()
        if self._at() == "(":
            self.i += 1  # '('
            while True:
                node.add_child(self._subtree())
                self._skip()
                nxt = self._at()
                if nxt == ",":
                    self.i += 1
                    continue
                if nxt == ")":
                    self.i += 1
                    break
                raise ValueError(f"expected ',' or ')' near position {self.i}, found {nxt!r}")
        node.name = self._label()
        self._skip()
        if self._at() == ":":
            self.i += 1
            node.length = self._number()
        return node

    def _label(self) -> str | None:
        self._skip()
        if self._at() == "'":
            return self._quoted()
        start = self.i
        while self.i < len(self.s) and self.s[self.i] not in _SPECIAL and not self.s[self.i].isspace():
            self.i += 1
        return self.s[start:self.i] or None

    def _quoted(self) -> str:
        self.i += 1  # opening quote
        chars: list[str] = []
        while self.i < len(self.s):
            ch = self.s[self.i]
            if ch == "'":
                if self.i + 1 < len(self.s) and self.s[self.i + 1] == "'":  # '' -> literal '
                    chars.append("'")
                    self.i += 2
                    continue
                self.i += 1  # closing quote
                break
            chars.append(ch)
            self.i += 1
        return "".join(chars)

    def _number(self) -> float:
        self._skip()
        start = self.i
        while self.i < len(self.s) and (self.s[self.i].isdigit() or self.s[self.i] in "+-.eE"):
            self.i += 1
        return float(self.s[start:self.i])

    def _skip(self) -> None:
        """Advance past whitespace and ``[bracketed comments]`` (which may nest)."""
        while self.i < len(self.s):
            ch = self.s[self.i]
            if ch.isspace():
                self.i += 1
            elif ch == "[":
                depth = 1
                self.i += 1
                while self.i < len(self.s) and depth:
                    if self.s[self.i] == "[":
                        depth += 1
                    elif self.s[self.i] == "]":
                        depth -= 1
                    self.i += 1
            else:
                break

    def _at(self) -> str:
        return self.s[self.i] if self.i < len(self.s) else ""
