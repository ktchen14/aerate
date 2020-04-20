import re
import unicodedata


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

def render_simplesect(node, before=""):
    # Must be "see", "return", "author", "authors", "version", "since", "date",
    # "note", "warning", "pre", "post", "copyright", "invariant", "remark",
    # "attention", "par", or "rcs"
    kind = node.get("kind")
    return f"{node.tail}"

def render_ref(node, before=""):
    refid = node.attrib["refid"]

    # Must be either "compound" or "member"
    kindref = node.attrib["kindref"]

    if kindref == "compound":
        result = object_index.xpath("/compound[@kindref=$kindref][@refid=$refid]", kindref=kindref, refid=refid)

    return f"{node.text}{node.tail}"

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
        if item.tag == "ref":
            output += render_ref(item, output)
    return output
