from aerate.rule import RuleEngine
from aerate.schema import SchemaError, INLINE_TAGS, is_inline, is_structural

__all__ = ("canonicalization_engine",)

canonicalization_engine = engine = RuleEngine()


@engine.rule("para", unless=lambda node: node.text or len(node))
def remove_null_para(self, cursor):
    return cursor.remove()


@engine.rule("para")
def canonicalize_para(self, cursor):
    if cursor.node.text or is_inline(cursor.node[0]):
        is_simple = True
    elif is_structural(cursor.node[0]):
        is_simple = False
    else:
        raise SchemaError(f"Can't handle <{cursor.node.tag}> inside <para>")

    for node in cursor.node:
        if not is_inline(node) and not is_structural(node):
            raise SchemaError(f"Can't handle <{node.tag}> inside <para>")

        if is_simple and is_structural(node):
            return cursor.divide(node)

        if not is_simple and is_inline(node):
            return cursor.divide(node)

        if not is_simple and is_structural(node) and node.tail:
            return cursor.divide_tail(node)
    return cursor


@engine.rule("ref", within="highlight")
def textualize_highlight_ref(self, cursor):
    if cursor.node.getparent().text is None:
        cursor.node.getparent().text = cursor.node.xpath("string()")
    else:
        cursor.node.getparent().text += cursor.node.xpath("string()")
    return cursor.remove()


@engine.rule("sp", within="highlight")
def textualize_highlight_sp(self, cursor):
    if cursor.node.getparent().text is None:
        cursor.node.getparent().text = " "
    else:
        cursor.node.getparent().text += " "
    return cursor.remove()


@engine.rule("simplesect", unless=lambda node: node.text or len(node))
def remove_null_simplesect(self, cursor):
    """Remove a ``simplesect`` node with no text or children."""
    return cursor.remove()


@engine.rule("simplesect", when="preceding-sibling::*[1][self::simplesect]")
def absorb_identical_simplesect(self, cursor):
    """Absorb a ``simplesect`` into a compatible preceding sibling."""

    if cursor.node.getprevious().tag != cursor.node.tag:
        return cursor.next()

    if cursor.node.getprevious().attrib != cursor.node.attrib:
        return cursor.next()

    if cursor.node.getprevious().nsmap != cursor.node.nsmap:
        return cursor.next()

    return cursor.adjoin()


@engine.rule(*INLINE_TAGS, unless=lambda node: node.text or len(node))
def remove_null_inline(self, cursor):
    """Remove an inline markup node with no text or children."""
    return cursor.remove()


@engine.rule("htmlonly", "manonly", "rtfonly", "latexonly", "docbookonly")
def remove_unused_inline(self, cursor):
    """Remove a ``only`` node unless it's ``xmlonly``."""
    return cursor.remove()


@engine.rule(*INLINE_TAGS, when="./*")
def lift_nested_inline(self, cursor):
    """Lift an inline markup node inside an inline markup node."""
    if not is_inline(cursor.node[0]):
        raise NotImplementedError(
            f"Can't handle <{cursor.node[0].tag}> inside <{cursor.node.tag}>")
    return cursor.lift(cursor.node[0])
