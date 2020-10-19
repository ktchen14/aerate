import re

# See https://github.com/doxygen/doxygen/blob/master/templates/xml/compound.xsd

class SchemaError(Exception):
    """Raised when a node is encountered that's unexpected from the schema."""


DESCRIPTION_TAGS = {
    "briefdescription", "detaileddescription", "inbodydescription",
    "parameterdescription"
}

# A <formula> node is structural if it begins with \[ or \begin{. Otherwise
# it's inline. We'll include "formula" in both INLINE_TAGS and STRUCTURAL_TAGS
# and handle the disambiguation in is_inline() and is_structural().

INLINE_TAGS = {
    "ulink", "bold", "s", "strike", "underline", "emphasis",
    "computeroutput", "subscript", "superscript", "center", "small", "del",
    "ins", "htmlonly", "manonly", "xmlonly", "rtfonly", "latexonly",
    "docbookonly", "image", "dot", "msc", "plantuml", "anchor", "formula",
    "ref", "emoji", "linebreak",
}

STRUCTURAL_TAGS = {
    "hruler", "preformatted", "programlisting", "verbatim", "indexentry",
    "orderedlist", "itemizedlist", "simplesect", "title", "variablelist",
    "table", "heading", "dotfile", "mscfile", "diafile", "toclist", "language",
    "parameterlist", "xrefsect", "copydoc", "blockquote", "parblock",
    "formula",
}


def is_description(node):
    """Return whether the ``node`` is a description type node."""
    return node.tag in DESCRIPTION_TAGS


def is_inline(node):
    """Return whether the ``node`` is an inline markup node."""
    if node.tag == "formula":
        return not re.match(r"\s*(\\\[|\\begin\{)", node.text)
    return node.tag in INLINE_TAGS


def is_structural(node):
    """Return whether the ``node`` is a structural markup node."""
    if node.tag == "formula":
        return re.match(r"\s*(\\\[|\\begin\{)", node.text)
    return node.tag in STRUCTURAL_TAGS
