import collections.abc
import functools

MARKUP = {
    "ulink", "bold", "s", "strike", "underline", "emphasis",
    "computeroutput", "subscript", "superscript", "center", "small", "del",
    "ins", "htmlonly", "manonly", "xmlonly", "rtfonly", "latexonly",
    "docbookonly", "image", "dot", "msc", "plantuml", "anchor", "formula",
    "ref", "emoji", "linebreak",
}


def canonicalize_inline(cursor):
    """Canonicalize an inline markup node."""

    # A canonical markup node must be a leaf node. Lift any children that are
    # inline markup nodes.

    if not cursor.node.text and len(cursor.node) == 0:
        return cursor.remove()

    if len(cursor.node) == 0:
        return cursor.next()

    if cursor.node[0].tag not in MARKUP:
        raise f"Can't nest <{cursor.node[0].tag}> in <{cursor.node.tag}>"

    return cursor.lift(cursor.node[0])


def canonicalize_simple_para(cursor):
    if not cursor.node.text and len(cursor.node) == 0:
        return cursor.remove()

    node = cursor.node
    cursor.next()
    while cursor and cursor.node.getparent() == node:
        canonicalize_inline(cursor)


def canonicalize_para(node):
    if not cursor.node.text and len(cursor.node) == 0:
        return cursor.remove()

    # If the para node contains text then it's a text para
    is_text = True if node.text else None

    node = cursor.node
    cursor.next()
    while cursor and cursor.node.getparent() == node:
        if is_text is True and cursor.node.tag not in MARKUP:
            return cursor.lift()

        if is_text is True and cursor.node.tag in MARKUP:
            canonicalize_markup(cursor)
            continue

        if is_text is False and cursor.node.tag not in MARKUP:
            cursor.next()
            continue

        if is_text is False and cursor.node.tag in MARKUP:
            return cursor.divide()
