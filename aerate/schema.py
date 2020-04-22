STRUCTURAL_TYPE = {
    "hruler", "preformatted", "programlisting", "verbatim", "indexentry",
    "orderedlist", "itemizedlist", "simplesect", "title", "variablelist",
    "table", "heading", "dotfile", "mscfile", "diafile", "toclist", "language",
    "parameterlist", "xrefsect", "copydoc", "blockquote", "parblock",
}

INLINE_TYPE = {
    "ulink", "bold", "s", "strike", "underline", "emphasis",
    "computeroutput", "subscript", "superscript", "center", "small", "del",
    "ins", "htmlonly", "manonly", "xmlonly", "rtfonly", "latexonly",
    "docbookonly", "image", "dot", "msc", "plantuml", "anchor", "formula",
    "ref", "emoji", "linebreak",
}

def is_structural(node):
    return node.tag in STRUCTURAL_TYPE

def is_inline(node):
    return node.tag in INLINE_TYPE


class SchemaError(Exception):
    pass
