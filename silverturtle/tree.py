import textwrap
from typing import Iterable, List, Mapping, Optional, TypeVar
import re
import itertools


def sorted_if(it, sort, *, key=None):
    if sort:
        return sorted(it, key=key)
    return it


class Tag:
    def __init__(self, name, pattern, comment: Optional[str]):
        self.name = name
        self.pattern = pattern
        self.comment = comment

        self._parts = None

    @classmethod
    def from_dict(
        cls,
        data: Mapping,
        *,
        name: Optional[str] = None,
    ):
        return cls(
            name, pattern=data.get("pattern", ""), comment=data.get("comment", None)
        )

    @classmethod
    def from_source(cls, source):
        ...

    @staticmethod
    def _expand_ranges(pat):
        matches = list(re.finditer(r"\{(\d+)\.\.(\d+)\}", pat))
        offset = 0

        parts = []
        for m in matches:
            start, stop = m.span()
            parts.append((pat[offset:start],))
            offset = stop

            parts.append(range(int(m[1]), int(m[2]) + 1))

        parts.append((pat[offset:],))

        for expansion in itertools.product(*parts):
            yield "".join(str(x) for x in expansion)

    @property
    def parts(self) -> List[str]:
        if self._parts is not None:
            return self._parts

        self._parts = []
        for part in self.pattern.split("|"):
            self._parts.extend(self._expand_ranges(part))

        return self._parts

    @property
    def values(self):
        return ["" if p == "*" else p for p in self.parts]

    def match(self, query):
        query = query.lower()

        if query in self.name.lower():
            for p in self.parts:
                if p == "*":
                    yield f"{self.name}="
                elif p == "?":
                    yield f"{self.name}"
                    yield f"{self.name}=no"
                else:
                    yield f"{self.name}={p}"

        for p in self.parts:
            if query in p.lower():
                yield f"{self.name}={p}"


class Node:
    def __init__(
        self,
        name,
        *,
        parent: Optional["Node"] = None,
        children: Optional[List["Node"]] = None,
        tags: Optional[List[Tag]] = None,
        aliases: Optional[List[str]] = None,
        comment: Optional[str] = None,
    ):
        self.name = name
        self.parent = parent

        if children is None:
            children = []

        if tags is None:
            tags = []

        if aliases is None:
            aliases = []

        self.children = children
        self.tags = tags
        self.aliases = aliases
        self.comment = comment

    @classmethod
    def from_dict(
        cls,
        data: Mapping,
        *,
        name: Optional[str] = None,
        parent: Optional["Node"] = None,
    ):
        if not data:
            data = {}

        if name is None:
            name = ""

        tags = [Tag.from_dict(v, name=k) for k, v in data.get("tags", {}).items()]
        aliases = data.get("aliases", [])
        comment = data.get("comment", None)

        node = cls(name, parent=parent, tags=tags, aliases=aliases, comment=comment)
        node.children = [
            cls.from_dict(c, name=n, parent=node)
            for n, c in data.get("children", {}).items()
        ]
        return node

    def format(self, indent=2, sort=True):
        result = [f"{self.name}::"]

        prefix = " " * indent

        if self.comment:
            result.append(prefix + f"# {self.comment}")
            result.append("")

        for t in sorted_if(self.tags, sort, key=lambda t: t.name):
            if t.comment:
                result.append(prefix + f"# {t.comment}")
            result.append(prefix + f"{t.name}~={t.pattern}")

        if self.tags:
            result.append("")

        for a in self.aliases:
            result.append(prefix + f"={a}")

        if self.aliases:
            result.append("")

        for c in sorted_if(self.children, sort, key=lambda c: c.name):
            result.append(textwrap.indent(c.format(indent=indent), prefix))

        return "\n".join(result)

    def __repr__(self):
        return f"<Node {self.name}>"

    def __str__(self):
        return self.format()
