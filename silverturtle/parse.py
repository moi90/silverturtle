import re
from typing import Iterable, List, Optional, Tuple
import itertools
import textwrap


class Block(List["Expression"]):
    def __init__(self, it=None, *, parent: Optional["Block"] = None, indent=None):
        if it is None:
            super().__init__()
        else:
            super().__init__(it)

        self.parent = parent
        self.indent = indent

    def __repr__(self) -> str:
        contents = " ".join(repr(o) for o in self)
        return f"<Block {contents}>"


class Expression:
    regex: re.Pattern

    def __init__(self, *args) -> None:
        self.args = args

    @classmethod
    def try_create(cls, s: str, block: Block):
        m = cls.regex.match(s)
        if m is None:
            return False

        block.append(cls(*m.groups()))
        return True

    def __repr__(self):
        args = " ".join(repr(a) for a in self.args)
        return f"<{self.__class__.__name__} {args}>"

    def __eq__(self, o: object) -> bool:
        return type(o) == type(self) and o.args == self.args


class Comment(Expression):
    pass


class LineComment(Comment):
    pass


class Blank(Expression):
    regex = re.compile(r"^\s*$")


class Node(Expression):
    regex = re.compile(r"([a-zA-Z0-9_-]+)::$")


class Tag(Expression):
    regex = re.compile(r"([a-zA-Z0-9:_.-]+)([*]?)\s*~=\s*(.*)$")


class Meta(Expression):
    regex = re.compile(r"([a-zA-Z0-9:_.-]+)\s*=\s*(.*)$")


class Alias(Expression):
    regex = re.compile(r"=(\w+)$")


_indent_content_re = re.compile("([ \t]*)(.*)")


def split_line(line: str) -> Tuple[str, str]:
    m = _indent_content_re.match(line)
    if m is None:
        raise ValueError(f"{line!r} does not match {_indent_content_re!r}")

    return m[1], m[2]


class ParserError(Exception):
    pass


def gen_ast(lines: Iterable[str]):
    root = Block()
    current_block: Block = root
    for line_no, line in enumerate(lines, start=1):
        line = line.rstrip()

        indent, content = split_line(line)

        if current_block.indent is None:
            current_block.indent = indent

        elif line == "" or current_block.indent == indent:
            pass

        # Indentation is larger than previously
        elif indent.startswith(current_block.indent):
            # Check if previous token was a Node
            prev = None
            for prev in reversed(current_block):
                if isinstance(prev, Blank):
                    pass
                else:
                    break

            if not isinstance(prev, Node):
                raise ParserError(
                    f"Unexpected indent in line {line_no}: {line!r}\nPrevious non-empty token was {prev}."
                )

            b = Block(parent=current_block, indent=indent)
            current_block.append(b)
            current_block = b

        else:
            # Indentation is smaller than previously
            while current_block.indent != indent and current_block.indent.startswith(
                indent
            ):
                if current_block.parent is None:
                    raise ParserError(
                        f"Dedent beyond initial indentation in line {line_no}: {line!r}"
                    )

                current_block = current_block.parent

        if content.startswith("#"):
            current_block.append(Comment(content[1:].strip()))
            continue

        if " #" in content:
            content, comment = content.split(" #", maxsplit=1)
            current_block.append(LineComment(comment.strip()))

        if not (
            Node.try_create(content, current_block)
            or Tag.try_create(content, current_block)
            or Alias.try_create(content, current_block)
            or Blank.try_create(content, current_block)
            or Meta.try_create(content, current_block)
        ):
            raise ParserError(f"Can not parse line {line_no}: {line!r}")

    return root


def split_block_comment(block: Block) -> Tuple[List, List]:
    """Split a block into a block comment (followed by a blank) and the rest."""

    for i, expr in enumerate(block):
        if type(expr) == Comment:
            pass
        elif type(expr) == Blank:
            return block[: i + 1], block[i + 1 :]
        else:
            return [], block[:]

    return [], block[:]


def build_node(node: Node, block: Optional[Block] = None):
    pass


def ast2dict(block: Block, data=None):
    if data is None:
        data = {}
    doc = []
    child = None
    for expr in block:
        if type(expr) == Comment:
            doc.append(expr.args[0])
            continue
        elif type(expr) == Blank:
            if doc and "doc" not in data:
                data["doc"] = "\n".join(doc)
        elif type(expr) == Node:
            child = data.setdefault("children", {})[expr.args[0]] = {}
        elif type(expr) == Block:
            ast2dict(expr, child)
        elif type(expr) == Alias:
            data.setdefault("aliases", []).append(expr.args[0])
        elif type(expr) == Tag:
            tag = data.setdefault("tags", {})[expr.args[0]] = {
                "pattern": expr.args[2],
                "multi": expr.args[1] == "*",
            }
            if doc:
                tag["doc"] = "\n".join(doc)
        elif type(expr) == Meta:
            data.setdefault("meta", {})[expr.args[0]] = expr.args[1]
        else:
            raise ParserError(f"Unexpected expression: {expr!r}")

        # Reset doc
        doc = []

    return data


def compare_blocks(block1: Block, block2: Block):
    def _comparison():
        for expr1, expr2 in itertools.zip_longest(block1, block2):
            if type(expr1) == type(expr2) == Block:
                yield textwrap.indent(compare_blocks(expr1, expr2), "  ")

            elif expr1 == expr2:
                yield f"[ok] {expr1!r}"

            else:
                yield f"[fail] {expr1!r} != {expr2!r}"

    return "\n".join(_comparison())


def format_block(block: Block):
    def _comparison():
        for expr in block:
            if type(expr) == Block:
                yield textwrap.indent(format_block(expr), "  ")
            else:
                yield repr(expr)

    return "\n".join(_comparison())


if __name__ == "__main__":
    import argparse
    from pprint import pprint

    parser = argparse.ArgumentParser()
    parser.add_argument("taxonomy_fn")
    args = parser.parse_args()

    with open(args.taxonomy_fn) as f:
        ast = gen_ast(f)

    print(format_block(ast))

    pprint(ast2dict(ast))
