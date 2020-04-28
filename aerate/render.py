import re
import textwrap
import unicodedata

from aerate.rule import RenderEngine
from aerate.schema import DESCRIPTION_TAGS, SchemaError

render_engine = engine = RenderEngine()


class InlineRenderer:
    prefix: str
    suffix: str

    def escape_head(node, before=""):
        last = before[-1:]

        if not last or last.isspace() or last in {"-", ":", "/"}:
            return False

        if last == "'" and node.text[0] != "'":
            return False

        if last == '"' and node.text[0] != '"':
            return False

        if last == "<" and node.text[0] != ">":
            return False

        if last == "(" and node.text[0] != ")":
            return False

        if last == "[" and node.text[0] != "]":
            return False

        if last == "{" and node.text[0] != "}":
            return False

        last_category = unicodedata.category(last)

        if unicodedata.category(last) in {"Pd", "Po"}:
            return False

        text_category = unicodedata.category(node.text[0])

        if last_category in {"Ps", "Pi", "Pf"} and text_category not in {"Pe", "Pi", "Pf"}:
            return False

        return True

    @classmethod
    def render(cls, node, before=""):
        # The inline markup end-string must be separated by at least one
        # character from the start-string.

        # Inline markup start-strings must be immediately followed by
        # non-whitespace. Inline markup end-strings must be immediately
        # preceded by non-whitespace.

        # Handled by trim_inline() + remove_null_inline() in canonicalization

        output = f"{cls.prefix}{node.text}{cls.suffix}"

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

        # Inline markup start-strings must start a text block or be immediately
        # preceded by whitespace, one of the ASCII characters:
        #   - : / ' " < ( [ {
        # Or a similar non-ASCII punctuation character from Unicode categories
        # Ps (Open), Pi (Initial quote), Pf (Final quote), Pd (Dash), or Po
        # (Other)
        last = before[-1:]

        if not last or last.isspace() or last in {"-", ":", "/"}:
            pass
        elif unicodedata.category(last) in {"Pd", "Po"}:
            pass
        elif last == "'" and node.text[0] != "'":
            pass
        elif last == '"' and node.text[0] != '"':
            pass
        elif last == "<" and node.text[0] != ">":
            pass
        elif last == "(" and node.text[0] != ")":
            pass
        elif last == "[" and node.text[0] != "]":
            pass
        elif last == "{" and node.text[0] != "}":
            pass
        elif unicodedata.category(last) in {"Ps", "Pi", "Pf"} and \
                unicodedata.category(node.text[0]) not in {"Pe", "Pi", "Pf"}:
            pass
        else:
            output = f"\\ {output}"

        # Inline markup end-strings must end a text block or be immediately
        # followed by whitespace, one of the ASCII characters:
        #   - . , : ; ! ? \ / ' " ) ] } >
        # Or a similar non-ASCII punctuation character from Unicode categories
        # Pe (Close), Pi (Initial quote), Pf (Final quote), Pd (Dash), or Po
        # (Other).
        next = node.tail[:1]
        if not next or next.isspace():
            output = f"{output}{node.tail}"
        elif next in ["-", ".", ",", ":", ";", "!", "?", "\\", "/", "'", '"',
                      ")", "]", "}", ">"]:
            output = f"{output}{node.tail}"
        elif unicodedata.category(next) in ["Pe", "Pi", "Pf", "Pd", "Po"]:
            output = f"{output}{node.tail}"
        else:
            output = f"{output}\\{node.tail}"

        return f"{output}"


class BoldRenderer(InlineRenderer):
    prefix = "**"
    suffix = "**"


class EmphasisRenderer(InlineRenderer):
    prefix = "*"
    suffix = "*"


class ComputerOutputRenderer(InlineRenderer):
    prefix = "``"
    suffix = "``"


@engine.rule("simplesect", when=lambda node: node.get("kind") == "return")
def render_simplesect_return(self, node, before=""):
    prefix = ":return: "
    description_output = textwrap.indent(render_simplesect(self, node, before), " " * len(prefix)).strip()
    return prefix + description_output + "\n\n"

@engine.rule("simplesect")
def render_simplesect(self, node, before=""):
    # Must be "see", "return", "author", "authors", "version", "since", "date",
    # "note", "warning", "pre", "post", "copyright", "invariant", "remark",
    # "attention", "par", or "rcs"
    kind = node.get("kind")

    if kind == "attention":
        prefix = ".. attention::"
    elif kind == "note":
        prefix = ".. note::"
    elif kind == "warning":
        prefix = ".. warning::"
    else:
        prefix = None

    output = "\n\n".join(
        self.handle(para) for para in node.iterchildren("para")
    ) + "\n\n"

    if prefix is not None:
        output = prefix + "\n\n" + textwrap.indent(output, " " * 3)

    return output

@engine.rule("ref", within="para")
def render_ref(self, node, before=""):
    refid = node.attrib["refid"]

    # Must be either "compound" or "member"
    kindref = node.attrib["kindref"]

    # if kindref == "member":
    #     kind, name = object_index.find(kindref, refid)
    #     if kind == "function":
    #         return f":c:func:`{name}`{node.tail}"

    return f"{node.text}{node.tail}"


@engine.rule("programlisting")
def render_programlisting(self, node, before=""):
    prefix = ".. code-block:: c\n\n"
    output = "\n".join(self.handle(item) for item in node)
    return prefix + textwrap.indent(output, " " * 3)


@engine.rule("bold")
def render_bold(self, node, before=""):
    return BoldRenderer().render(node, before)


@engine.rule("computeroutput")
def render_computeroutput(self, node, before=""):
    return ComputerOutputRenderer().render(node, before)


@engine.rule("emphasis")
def render_emphasis(self, node, before=""):
    return EmphasisRenderer().render(node, before)


@engine.rule("para")
def render_para(self, node, before=""):
    output = node.text or ""
    for item in node:
        output += self.handle(item, output)
    return output + "\n\n"


@engine.rule("parameterlist", when=lambda node: node.get("kind") == "param")
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


@engine.rule(*DESCRIPTION_TAGS)
def render_description(self, node, before=""):
    output = []
    for item in node:
        if item.tag != "para":
            raise SchemaError(f"Can't handle <{item.tag}> in <{node.tag}>")
        output.append(self.handle(item).rstrip())
    return "\n\n".join(output)
