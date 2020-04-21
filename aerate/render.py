import os
import re
import textwrap
import unicodedata

from aerate.index import Index


SCRIPT_ROOT = os.path.dirname(os.path.realpath(__file__))
object_index = Index(os.path.join(SCRIPT_ROOT, "..", "xml"))


class InlineRenderer:
    prefix: str
    suffix: str

    @classmethod
    def render(cls, node, before=""):
        # The inline markup end-string must be separated by at least one character
        # from the start-string.
        if not node.text:
            return ""

        if node.text.isspace():
            return node.text

        # Inline markup start-strings must be immediately followed by
        # non-whitespace. Inline markup end-strings must be immediately preceded by
        # non-whitespace.
        m = re.match(r'^(\s*)(.+?)(\s*)$', node.text)
        output = f"{cls.prefix}{m[2]}{cls.suffix}{m[3]}"

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
        last = (before + m[1])[-1:]

        if not last or last.isspace():
            output = f"{m[1]}{output}"
        elif last in ["'", '"', "<", "(", "[", "{"]:
            output = f"\\ {m[1]}{output}"
        elif unicodedata.category(last) in ["Ps", "Pi", "Pf"]:
            output = f"\\ {m[1]}{output}"
        elif last in ["-", ":", "/"]:
            output = f"{m[1]}{output}"
        elif unicodedata.category(last) in ["Pd", "Po"]:
            output = f"{m[1]}{output}"
        else:
            output = f"\\ {m[1]}{output}"

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

def render_simplesect_return(node, before=""):
    prefix = ":return: "
    description_output = textwrap.indent(render_description(node), " " * len(prefix)).strip()
    return prefix + description_output + "\n\n"

def render_simplesect(node, before=""):
    # Must be "see", "return", "author", "authors", "version", "since", "date",
    # "note", "warning", "pre", "post", "copyright", "invariant", "remark",
    # "attention", "par", or "rcs"
    kind = node.get("kind")

    if kind == "return":
        return render_simplesect_return(node, before)

    if kind == "attention":
        prefix = ".. attention::"
    elif kind == "note":
        prefix = ".. note::"
    elif kind == "warning":
        prefix = ".. warning::"
    else:
        prefix = None

    output = "\n\n".join(
        render_para(para) for para in node.iterchildren("para")
    ) + "\n\n"

    if prefix is not None:
        output = prefix + "\n\n" + textwrap.indent(output, " " * 3)

    return output

def render_ref(node, before=""):
    refid = node.attrib["refid"]

    # Must be either "compound" or "member"
    kindref = node.attrib["kindref"]

    if kindref == "member":
        kind, name = object_index.find(kindref, refid)
        if kind == "function":
            return f":c:func:`{name}`{node.tail}"

    return f"{node.text}{node.tail}"

def render_programlisting(node, before=""):
    prefix = ".. code-block:: c\n\n"

    output = []
    for codeline in node.iterchildren("codeline"):
        output.append(codeline.xpath("string()"))
    return prefix + textwrap.indent("\n".join(output), " " * 3) + "\n\n"


def render_parameterlist(node, before=""):
    if node.get("kind") != "param":
        return ""

    total_output = ""
    for item in node.iterchildren():
        (name,) = item.xpath("./parameternamelist/parametername")
        (description,) = item.xpath("./parameterdescription")

        output = f":param {name.text}: "
        description_output = render_description(description)

        output += textwrap.indent(description_output, " " * len(output)).strip()
        total_output += "\n" + output
    return total_output + "\n\n"

def render_description(description_node, before=""):
    output = []
    for node in description_node:
        if node.tag != "para":
            raise NotImplementedError(f"Can't handle <{node.tag}> in <{description_node.tag}>")
        para_output = render_para(node)
        output.append(para_output.rstrip())
    return "\n\n".join(output) + "\n\n"

def render_para(node):
    output = node.text or ""
    for item in node.iterchildren():
        if item.tag == "bold":
            output += BoldRenderer.render(item, output)
        if item.tag == "emphasis":
            output += EmphasisRenderer.render(item, output)
        if item.tag == "computeroutput":
            output += ComputerOutputRenderer.render(item, output)
        if item.tag == "simplesect":
            output += render_simplesect(item, output)
        if item.tag == "programlisting":
            output += render_programlisting(item, output)
        if item.tag == "parameterlist":
            output += render_parameterlist(item, output)
        if item.tag == "ref":
            output += render_ref(item, output)
    return output
