import textwrap
import unicodedata

from aerate.rule import RenderEngine
from aerate.schema import DESCRIPTION_TAGS, SchemaError

__all__ = ("renderer",)

renderer = RenderEngine()


class InlineRenderer:
    def __init__(self, prefix, suffix=None):
        self.prefix = prefix
        self.suffix = suffix if suffix is not None else prefix

    @staticmethod
    def escape_head(node, before):
        """
        Return whether to escape with ``\\\\ `` before the rendered ``node``.
        """

        # Inline markup start-strings must start a text block or be immediately
        # preceded by whitespace, one of the ASCII characters:
        #   - : / ' " < ( [ {
        # Or a similar non-ASCII punctuation character from Unicode categories
        # Ps (Open), Pi (Initial quote), Pf (Final quote), Pd (Dash), or Po
        # (Other)

        if not before or before.isspace() or before in {"-", ":", "/"}:
            return False

        if unicodedata.category(before) in {"Pd", "Po"}:
            return False

        # If an inline markup start-string is immediately preceded by one of
        # the ASCII characters:
        #   ' " < ( [ {
        # Or a similar non-ASCII character from Unicode categories Ps (Open),
        # Pi (Initial quote), or Pf (Final quote), it must not be followed by
        # the corresponding closing character from:
        #   ' " ) ] } >
        # Or a similar non-ASCII character from Unicode categories Pe (Close),
        # Pi (Initial quote), or Pf (Final quote). For quotes, matching
        # characters can be any of the quotation marks in international usage.

        if before == "'" and node.text[0] != "'":
            return False

        if before == '"' and node.text[0] != '"':
            return False

        if before == "<" and node.text[0] != ">":
            return False

        if before == "(" and node.text[0] != ")":
            return False

        if before == "[" and node.text[0] != "]":
            return False

        if before == "{" and node.text[0] != "}":
            return False

        if unicodedata.category(before) in {"Ps", "Pi", "Pf"}:
            if unicodedata.category(node.text[0]) not in {"Pe", "Pi", "Pf"}:
                return False

        return True

    @staticmethod
    def escape_tail(node):
        """Return whether to escape the ``node``'s tail with ``\\\\``."""

        # Inline markup end-strings must end a text block or be immediately
        # followed by whitespace, one of the ASCII characters:
        #   - . , : ; ! ? \ / ' " ) ] } >
        # Or a similar non-ASCII punctuation character from Unicode categories
        # Pe (Close), Pi (Initial quote), Pf (Final quote), Pd (Dash), or Po
        # (Other).
        follow = node.tail[:1]

        # If an inline markup node follows this node then we'll handle the
        # escape in its renderer
        if not follow or follow.isspace():
            return False

        if follow in {"-", ".", ",", ":", ";", "!", "?", "\\", "/", "'", '"',
                      ")", "]", "}", ">"}:
            return False

        if unicodedata.category(follow) in {"Pe", "Pi", "Pf", "Pd", "Po"}:
            return False

        return True

    def render(self, node, buffer=""):
        """Render the ``node``."""

        # The inline markup end-string must be separated by at least one
        # character from the start-string.

        # Inline markup start-strings must be immediately followed by
        # non-whitespace. Inline markup end-strings must be immediately
        # preceded by non-whitespace.

        # Handled by trim_inline(), remove_null_inline() in the adjuster

        output = f"{self.prefix}{node.text}{self.suffix}"

        if self.escape_head(node, buffer[-1:]):
            output = f"\\ {output}"

        if self.escape_tail(node):
            output = f"{output}\\"

        return f"{output}{node.tail or ''}"


bold_renderer = InlineRenderer("**")
emphasis_renderer = InlineRenderer("*")
computeroutput_renderer = InlineRenderer("``")
subscript_renderer = InlineRenderer(":subscript:`", "`")
superscript_renderer = InlineRenderer(":superscript:`", "`")


# The simplesect's kind must be "see", "return", "author", "authors",
# "version", "since", "date", "note", "warning", "pre", "post", "copyright",
# "invariant", "remark", "attention", "par", or "rcs"

@renderer.rule("simplesect", when=lambda node: node.get("kind") == "return")
def render_simplesect_return(self, node, before=""):
    prefix = ":return: "
    output = render_simplesect(self, node, before)
    output = textwrap.indent(output, " " * len(prefix)).strip()
    return prefix + output + "\n\n"

@renderer.rule("simplesect", when=lambda node: node.get("kind") in {
    "attention", "note", "warning"})
def render_simplesect_admonition(self, node, before=""):
    prefix = f".. {node.get('kind')}::"
    output = render_simplesect(self, node, before)
    output = textwrap.indent(output, " " * 3)
    return prefix + "\n\n" + output + "\n\n"


@renderer.rule("simplesect")
def render_simplesect(self, node, before=""):
    output = "\n\n".join(
        self.handle(para) for para in node.iterchildren("para")
    ) + "\n\n"
    return output


@renderer.rule("ref", within="para")
def render_ref(self, node, before=""):
    refid = node.attrib["refid"]

    # Must be either "compound" or "member"
    kindref = node.attrib["kindref"]

    # if kindref == "member":
    #     kind, name = object_index.find(kindref, refid)
    #     if kind == "function":
    #         return f":c:func:`{name}`{node.tail}"

    return f"{node.text}{node.tail}"


@renderer.rule("programlisting")
def render_programlisting(self, node, before=""):
    prefix = ".. code-block:: c\n\n"
    output = "\n".join(self.handle(item) for item in node)
    return prefix + textwrap.indent(output, " " * 3)


@renderer.rule("bold")
def render_bold(self, node, before=""):
    return bold_renderer.render(node, before)


@renderer.rule("emphasis")
def render_emphasis(self, node, before=""):
    return emphasis_renderer.render(node, before)


@renderer.rule("computeroutput")
def render_computeroutput(self, node, before=""):
    return computeroutput_renderer.render(node, before)


@renderer.rule("subscript")
def render_subscript(self, node, before=""):
    return subscript_renderer.render(node, before)


@renderer.rule("superscript")
def render_superscript(self, node, before=""):
    return superscript_renderer.render(node, before)


@renderer.rule("para")
def render_para(self, node, before=""):
    output = node.text or ""
    for item in node:
        output += self.handle(item, output)
    return output + "\n\n"


@renderer.rule("parameterlist", when=lambda node: node.get("kind") == "param")
def render_parameterlist(self, node, before=""):
    total_output = ""
    for item in node:
        (name,) = item.xpath("./parameternamelist/parametername")
        (description,) = item.xpath("./parameterdescription")

        output = f":param {name.text}: "
        description_output = self.handle(description)

        output += textwrap.indent(description_output, " " * len(output)).strip()
        total_output += "\n" + output
    return total_output + "\n\n"


@renderer.rule(*DESCRIPTION_TAGS)
def render_description(self, node, before=""):
    output = []
    for item in node:
        if item.tag != "para":
            raise SchemaError(f"Can't handle <{item.tag}> in <{node.tag}>")
        output.append(self.handle(item).rstrip())
    return "\n\n".join(output)
