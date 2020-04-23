from aerate.schema import INLINE_TYPE, is_inline, is_structural
from aerate.rule import RuleEngine

engine = RuleEngine()

@engine.rule(*INLINE_TYPE, when="./*")
def canonicalize_inline(engine, cursor):
    """Lift an inline markup node inside an inline markup node."""
    if not is_inline(cursor.node[0]):
        raise NotImplementedError(
            f"Can't handle <{cursor.node[0].tag}> inside <{cursor.node.tag}>")
    return cursor.lift(cursor.node[0])

@engine.rule("htmlonly", "manonly", "rtfonly", "latexonly", "docbookonly")
def remove_unused_inline(engine, cursor):
    """Remove a ``only`` node unless it's ``xmlonly``."""
    return cursor.remove()

@engine.rule(*INLINE_TYPE, unless=lambda node: node.text or len(node))
def remove_null_inline(engine, cursor):
    """Remove an inline markup node with no text or children."""
    return cursor.remove()

@engine.rule("simplesect", when="preceding-sibling::*[1][self::simplesect]")
def canonicalize_simplesect(engine, cursor):
    """Absorb a ``simplesect`` into a compatible preceding sibling."""

    if cursor.node.getprevious().tag != cursor.node.tag:
        return cursor.next()

    if cursor.node.getprevious().attrib != cursor.node.attrib:
        return cursor.next()

    if cursor.node.getprevious().nsmap != cursor.node.nsmap:
        return cursor.next()

    return cursor.adjoin()

@engine.rule("simplesect", unless=lambda node: node.text or len(node))
def remove_null_simplesect(engine, cursor):
    """Remove a ``simplesect`` node with no text or children."""
    return cursor.remove()

@engine.rule("ref", inside="highlight")
def textualize_highlight_ref(engine, cursor):
    if cursor.node.getparent().text is None:
        cursor.node.getparent().text = cursor.node.xpath("string()")
    else:
        cursor.node.getparent().text += cursor.node.xpath("string()")
    return cursor.remove()

@engine.rule("sp", inside="highlight")
def textualize_highlight_sp(engine, cursor):
    if cursor.node.getparent().text is None:
        cursor.node.getparent().text = " "
    else:
        cursor.node.getparent().text += " "
    return cursor.remove()

@engine.rule("para")
def canonicalize_para(engine, cursor):
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
            return engine.handle(cursor.divide_tail())

        engine.handle(cursor)

    return cursor

@engine.rule("para", unless=lambda node: node.text or len(node))
def remove_null_para(engine, cursor):
    return cursor.remove()
