import re
from typing import List, Optional, Tuple
import itertools
import textwrap


class Block(list):
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
    regex = re.compile(r"(\w+)::$")


class Tag(Expression):
    regex = re.compile(r"(\w+)~=(.*)$")


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


def gen_ast(source: str):
    root = Block()
    current_block: Block = root
    for line_no, line in enumerate(source.splitlines()):
        indent, content = split_line(line)

        if current_block.indent is None:
            current_block.indent = indent

        elif line == "" or current_block.indent == indent:
            pass

        # Indentation is larger than previously
        elif indent.startswith(current_block.indent):
            # Check if previous token was a Node
            if not isinstance(current_block[-1], Node):
                raise ParserError(f"Unexpected indent in line {line_no}: {line!r}")

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


def gen_dict(source: str):
    root = gen_ast(source)

    # Root needs to be a block with exactly one node with empty name, optionally followed by a block
    if len


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
