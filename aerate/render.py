from aerate.engine import Engine
import unicodedata

__all__ = ("Renderer", "InlineRenderer", "RoleRenderer", "bold_renderer",
           "emphasis_renderer", "computeroutput_renderer",
           "subscript_renderer", "superscript_renderer")


class Renderer(Engine):
    """An engine that renders an unaccepted node as its text."""

    def on_unaccepted(self, node, *args, **kwargs):
        return node.xpath("string()")


class InlineRenderer:
    def __init__(self, prefix, suffix=None, escape=None):
        self.prefix = prefix
        self.suffix = suffix if suffix is not None else self.prefix
        self.escape = escape if escape is not None else self.suffix

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


class RoleRenderer(InlineRenderer):
    def __init__(self, role):
        super().__init__(f":{role}:`", "`")


bold_renderer = InlineRenderer("**")
emphasis_renderer = InlineRenderer("*")
computeroutput_renderer = InlineRenderer("``")
subscript_renderer = RoleRenderer("subscript")
superscript_renderer = RoleRenderer("superscript")
