# See https://github.com/doxygen/doxygen/blob/master/templates/xml/compound.xsd


class SchemaError(Exception):
    """Raised when a node is encountered that's unexpected from the schema."""


DESCRIPTION_TAGS = {
    "briefdescription", "detaileddescription", "inbodydescription",
    "parameterdescription"
}

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
}


def is_description(node):
    return node.tag in DESCRIPTION_TAGS


def is_inline(node):
    return node.tag in INLINE_TAGS


def is_structural(node):
    return node.tag in STRUCTURAL_TAGS
