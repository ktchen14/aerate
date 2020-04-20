STRUCTURAL_MARKUP = {
    "hruler", "preformatted", "programlisting", "verbatim", "indexentry",
    "orderedlist", "itemizedlist", "simplesect", "title", "variablelist",
    "table", "heading", "dotfile", "mscfile", "diafile", "toclist", "language",
    "parameterlist", "xrefsect", "copydoc", "blockquote", "parblock",
}

INLINE_MARKUP = {
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

    if cursor.node[0].tag not in INLINE_MARKUP:
        raise NotImplementedError(
            f"Can't nest <{cursor.node[0].tag}> in <{cursor.node.tag}>")

    return cursor.lift(cursor.node[0])


def canonicalize_simple_para(cursor):
    if not cursor.node.text and len(cursor.node) == 0:
        return cursor.remove()

    node = cursor.node
    cursor.next()
    while cursor and cursor.node.getparent() == node:
        canonicalize_inline(cursor)


def canonicalize_para(cursor):
    if not cursor.node.text and len(cursor.node) == 0:
        return cursor.remove()

    if cursor.node.text or cursor.node[0].tag in INLINE_MARKUP:
        is_simple = True
    elif cursor.node[0].tag in STRUCTURAL_MARKUP:
        is_simple = False
    else:
        raise NotImplementedError(f"Unrecognized node <{cursor.node.tag}>")

    node = cursor.node
    cursor.next()
    while cursor and cursor.node.getparent() == node:
        if cursor.node.tag not in INLINE_MARKUP | STRUCTURAL_MARKUP:
            raise NotImplementedError(f"Unrecognized node <{cursor.node.tag}>")

        if is_simple is True and cursor.node.tag in STRUCTURAL_MARKUP:
            return cursor.divide()

        if is_simple is True and cursor.node.tag in INLINE_MARKUP:
            canonicalize_inline(cursor)
            continue

        if is_simple is False and cursor.node.tag in STRUCTURAL_MARKUP:
            cursor.next()
            continue

        if is_simple is False and cursor.node.tag in INLINE_MARKUP:
            return cursor.divide()
