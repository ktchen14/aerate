from lxml import etree

from aerate.mutation import MutationCursor
from test.sample import SampleCursor, semantic


def test_bool_with_none():
    assert not SampleCursor("<root/>").next()


def test_bool_with_node():
    assert SampleCursor("<root/>")


def test_root():
    cursor = SampleCursor("<root><a/></root>")
    cursor.next()
    assert cursor.root.tag == "root"


def test_move_to():
    cursor = SampleCursor("<root><a/></root>")
    target = etree.SubElement(cursor.root, "target")
    assert cursor.move_to(target).node == target


def test_next_to_children():
    cursor = SampleCursor("<root><target/></root>")
    assert cursor.next().node.tag == "target"


def test_next_to_siblings():
    cursor = SampleCursor("<root><cursor/><target/></root>")
    assert cursor.next().node.tag == "target"


def test_next_to_ancestors_next():
    cursor = SampleCursor("""
        <root><a><b><cursor/></b></a><target/></root>
    """)
    assert cursor.next().node.tag == "target"


def test_rewind_to_previous():
    cursor = SampleCursor("""
        <root><a/><target/><cursor/><d/></root>
    """)
    assert cursor.rewind().node.tag == "target"


def test_rewind_to_parent():
    cursor = SampleCursor("""
        <root><a><target><cursor/></target></a></root>
    """)
    assert cursor.rewind().node.tag == "target"


def test_skip_to_siblings():
    cursor = SampleCursor("""
        <root><cursor><b/></cursor><target/></root>
    """)
    assert cursor.skip().node.tag == "target"


def test_skip_to_ancestors_next():
    cursor = SampleCursor("""
        <root><a><cursor><c/></cursor></a><target/></root>
    """)
    assert cursor.skip().node.tag == "target"


def test_stop():
    assert SampleCursor("<root/>").stop().node is None


def test_divide():
    cursor = SampleCursor("""
        <root><item>prefix <cursor/> suffix</item></root>
    """)

    cursor.divide()

    assert cursor.root == semantic("""
        <root>
            <item>prefix </item> <item><cursor/> suffix</item>
        </root>
    """)
    assert cursor.node.tag == "cursor"


def test_remove():
    cursor = SampleCursor("<root><a/><cursor/><c/></root>")
    cursor.remove()
    assert cursor.node.tag == "c"
