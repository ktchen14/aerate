from aerate.mutation import MutationEngine
from aerate.mutation import extend_tail, extend_text
from aerate.schema import SchemaError, INLINE_TAGS, is_inline, is_structural
import re

engine: MutationEngine = engine  # Stop "F821 undefined name 'engine'"


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


@engine.rule("htmlonly", "manonly", "rtfonly", "latexonly", "docbookonly")
def remove_unused_inline(self, cursor):
    """Remove a ``...only`` node unless it's ``xmlonly``."""
    return cursor.remove()


@engine.rule(*INLINE_TAGS, when="./*")
def lift_nested_inline(self, cursor):
    """Lift an inline markup node inside an inline markup node."""
    if not is_inline(cursor.node[0]):
        raise NotImplementedError(
            f"Can't handle <{cursor.node[0].tag}> inside <{cursor.node.tag}>")
    return cursor.lift(cursor.node[0])


@engine.rule(*INLINE_TAGS, when=lambda node: node.text)
def trim_inline(self, cursor):
    """Lift leading and trailing whitespace from an inline markup node."""

    m = re.match(r'^(\s*)(.*?)(\s*)$', cursor.node.text)
    head, text, tail = m.groups()

    if cursor.node.getprevious() is not None:
        extend_tail(cursor.node.getprevious(), head)
    else:
        extend_text(cursor.node.getparent(), head)

    if tail:
        cursor.node.tail = tail + (cursor.node.tail or "")

    cursor.node.text = text
    return cursor


@engine.rule(*INLINE_TAGS, unless=lambda node: node.text or len(node))
def remove_null_inline(self, cursor):
    """Remove an inline markup node with no text or children."""
    return cursor.remove()


@engine.rule("simplesect", unless=lambda node: node.text or len(node))
def remove_null_simplesect(self, cursor):
    """Remove a ``simplesect`` node with no text or children."""
    return cursor.remove()


@engine.rule("simplesect", when="preceding-sibling::*[1][self::simplesect]")
def absorb_compatible_simplesect(self, cursor):
    """Absorb a ``simplesect`` node into a compatible preceding sibling."""

    if cursor.node.getprevious().tag != cursor.node.tag:
        return cursor.next()

    if cursor.node.getprevious().attrib != cursor.node.attrib:
        return cursor.next()

    if cursor.node.getprevious().nsmap != cursor.node.nsmap:
        return cursor.next()

    return cursor.adjoin()


@engine.rule("para")
def divide_para_by_type(self, cursor):
    """Divide a ``para`` node with both structural and inline markup."""

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


@engine.rule("para", unless=lambda node: node.text or len(node))
def remove_null_para(self, cursor):
    """Remove a ``para`` node with no text or children."""
    return cursor.remove()
