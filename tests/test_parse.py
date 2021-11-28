from silverturtle.parse import (
    Block,
    Comment,
    LineComment,
    Node,
    Tag,
    compare_blocks,
    gen_ast,
    Blank,
    split_block_comment,
)


def test_gen_ast():
    source = """\
    Foo::
        # Comment Foo
        tag~=A|B|* # Line comment

        Bar::
            # Comment Bar

    Baz::
    """

    ast_expected = Block(
        [
            Node("Foo"),
            Block(
                [
                    Comment("Comment Foo"),
                    LineComment("Line comment"),
                    Tag("tag", "A|B|*"),
                    Blank(),
                    Node("Bar"),
                    Block(
                        [
                            Comment("Comment Bar"),
                            Blank(),
                        ]
                    ),
                ]
            ),
            Node("Baz"),
            Blank(),
        ]
    )

    ast = gen_ast(source)

    print()
    print(compare_blocks(ast, ast_expected))

    assert ast == ast_expected
    # assert_block_equal(ast, ast_expected)


def test_split_block_comment_success():
    block_comment = [Comment(""), Comment(""), Blank()]
    tail = [Comment("")]
    block = Block(None)
    block.extend(block_comment)
    block.extend(tail)

    result = split_block_comment(block)

    assert result[0] == block_comment
    assert result[1] == tail


def test_split_block_comment_fail():
    content = [Comment(""), Comment(""), Node("Foo")]
    block = Block(content)

    result = split_block_comment(block)

    assert result[0] == []
    assert result[1] == content
