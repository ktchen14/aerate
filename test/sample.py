from lxml import etree
from aerate.mutation import MutationCursor


def SampleCursor(document: str, on: str=None):
    """Return a mutation cursor on ``document`` at a node."""

    parser = etree.XMLParser(remove_blank_text=True)
    cursor = MutationCursor(etree.fromstring(document, parser))
    if on is not None:
        while cursor.node.tag != on:
            cursor.next()
    else:
        node = cursor.root.find(".//cursor")
        if node is not None:
            cursor.move_to(node)
    return cursor


class semantic:
    """Used to test semantic equivalent of two XML documents."""

    def __init__(self, document: str):
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.fromstring(document, parser)
        self.expected = etree.tostring(root, method="c14n2")

    def __eq__(self, other):
        if not isinstance(other, etree._Element):
            return NotImplemented
        text = etree.tostring(other, method="c14n2")
        return self.expected == text
