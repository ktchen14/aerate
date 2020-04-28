from lxml import etree
import pytest
from aerate.adjust import adjuster
from test.sample import semantic


def SampleDocument(text):
    parser = etree.XMLParser(remove_blank_text=True)
    return etree.fromstring(text, parser)


def test_unused_inline():
    document = SampleDocument("""
        <root>
            <htmlonly>test</htmlonly>
            <manonly>test</manonly>
            <rtfonly>test</rtfonly>
            <latexonly>test</latexonly>
            <docbookonly>test</docbookonly>
        </root>
    """)
    adjuster.handle(document)
    assert document == semantic("<root/>")


def test_lift_nested_inline():
    document = SampleDocument("<root><bold>a<para>b</para></bold></root>")
    with pytest.raises(NotImplementedError):
        adjuster.handle(document)

    document = SampleDocument("""
        <root>a<bold>b<emphasis>c</emphasis>d</bold>e</root>
    """)
    adjuster.handle(document)
    assert document == semantic("""
        <root>a<bold>b</bold><emphasis>c</emphasis><bold>d</bold>e</root>
    """)


def test_trim_inline():
    document = SampleDocument("<root>a<bold>  test  </bold>c</root>")
    adjuster.handle(document)
    assert document == semantic("<root>a  <bold>test</bold>  c</root>")
