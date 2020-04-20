from lxml import etree

from aerate.mutation import MutationCursor


def make_cursor(text, move_to_tag=None):
    cursor = MutationCursor(etree.fromstring(text))
    if move_to_tag is not None:
        while cursor.node.tag != move_to_tag:
            cursor.next()
    return cursor


def test_move_to():
    cursor = make_cursor("<root><a/></root>")
    target = etree.SubElement(cursor.root, "target")
    assert cursor.move_to(target).node == target


def test_next_with_child_element():
    cursor = make_cursor("<root><target/></root>")
    assert cursor.next().node.tag == "target"


def test_next_with_sibling_element():
    cursor = make_cursor("<root><a/><target/></root>", move_to_tag="a")
    assert cursor.next().node.tag == "target"


def test_next_parent():
    cursor = make_cursor("<root><a><b/></a><target/></root>", move_to_tag="b")
    assert cursor.next().node.tag == "target"


def test_remove():
    cursor = make_cursor("<root><a/><b/><c/></root>", move_to_tag="b")
    cursor.remove()
    assert cursor.node.tag == "c"
