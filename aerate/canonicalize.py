import sys

from aerate.schema import is_inline, is_structural

module = sys.modules[__name__]


def canonicalize(cursor):
    handle = getattr(module, f"canonicalize_{cursor.node.tag}", None)

    if handle is not None:
        return handle(cursor)

    if is_inline(cursor.node):
        return canonicalize_inline(cursor)

    root = cursor.node
    cursor.next()
    while cursor and cursor.node.getparent() == root:
        canonicalize(cursor)
    return cursor


def canonicalize_inline(cursor):
    """Canonicalize an inline markup node."""

    if cursor.node.tag in {
        "htmlonly", "manonly", "rtfonly", "latexonly", "docbookonly",
    }:
        return cursor.remove()

    # A canonical markup node must be a leaf node. Lift any children that are
    # inline markup nodes.

    if not cursor.node.text and len(cursor.node) == 0:
        return cursor.remove()

    if len(cursor.node) == 0:
        return cursor.next()

    if not is_inline(cursor.node[0]):
        raise NotImplementedError(
            f"Can't handle <{cursor.node[0].tag}> inside <{cursor.node.tag}>")

    return cursor.lift(cursor.node[0])


def canonicalize_simplesect(cursor):
    if not cursor.node.text and len(cursor.node) == 0:
        return cursor.remove()

    if cursor.node.getprevious() is not None and \
            cursor.node.getprevious().tag == cursor.node.tag and \
            cursor.node.getprevious().attrib == cursor.node.attrib and \
            cursor.node.getprevious().nsmap == cursor.node.nsmap:
        return cursor.adjoin()
    return cursor.skip()


def canonicalize_highlight(cursor):
    root = cursor.node
    cursor.next()
    while cursor and cursor.node.getparent() == root:
        if cursor.node.tag == "ref":
            if root.text is None:
                root.text = cursor.node.xpath("string()")
            else:
                root.text += cursor.node.xpath("string()")
        elif cursor.node.tag == "sp":
            if root.text is None:
                root.text = " "
            else:
                root.text += " "
        cursor.remove()
    return cursor


def canonicalize_para(cursor):
    if not cursor.node.text and len(cursor.node) == 0:
        return cursor.remove()

    if cursor.node.text or is_inline(cursor.node[0]):
        is_simple = True
    elif is_structural(cursor.node[0]):
        is_simple = False
    else:
        raise NotImplementedError(f"Can't handle <{cursor.node.tag}> inside <para>")

    root = cursor.node
    cursor.next()
    while cursor and cursor.node.getparent() == root:
        if not is_inline(cursor.node) and not is_structural(cursor.node):
            raise NotImplementedError(f"Can't handle <{cursor.node.tag}> inside <para>")

        if is_simple and is_structural(cursor.node):
            return cursor.divide().rewind()

        if not is_simple and is_inline(cursor.node):
            return cursor.divide().rewind()

        if not is_simple and is_structural(cursor.node) and cursor.node.tail:
            return canonicalize(cursor.divide_tail())

        canonicalize(cursor)

    return cursor
