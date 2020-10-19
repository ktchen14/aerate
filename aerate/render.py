import re
import unicodedata

__all__ = (
    "escape_text", "InlineRenderer", "RoleRenderer", "bold_renderer",
    "emphasis_renderer", "computeroutput_renderer", "subscript_renderer",
    "superscript_renderer"
)


def escape_text(text):
    """Escape *text* as normal text."""

    # There are nine inline markup constructs. Five of the constructs use
    # identical start-strings and end-strings to indicate the markup:
    # - emphasis: "*"
    # - strong emphasis: "**"
    # - interpreted text: "`"
    # - inline literals: "``"
    # - substitution references: "|"

    text = re.sub(r"(\*\*|\*|``|`|\|)", r"\\\1", text)

    # Three constructs use different start-strings and end-strings:
    #
    # - inline internal targets: "_`" and "`"
    # - footnote references: "[" and "]_"
    # - hyperlink references: "`" and "`_" (phrases), or just a trailing "_"
    #   (single words)

    # TODO: handle this

    return text


class InlineRenderer:
    def __init__(self, prefix, suffix=None, escape=None):
        """
        Return an object used to render the specified inline markup syntax.

        :param prefix: the inline markup start-string
        :param suffix: the inline markup end-string or *prefix* if unspecified
        :param escape: a string to escape (in addition to a single ``\\``) in
            the inline markup text or *suffix* if unspecified
        """

        self.prefix = prefix
        self.suffix = suffix if suffix is not None else self.prefix
        self.escape = escape if escape is not None else self.suffix

    @staticmethod
    def should_escape_prefix(text, before):
        """
        Return if ``\\ `` should be inserted before the inline markup string.

        :param text: the text to render inside the inline markup
        :param before: the character in the buffer before the inline markup
        """

        # Inline markup start-strings must start a text block or be immediately
        # preceded by whitespace, one of the ASCII characters:
        #   - : / ' " < ( [ {
        # Or a similar non-ASCII punctuation character from Unicode categories
        # Ps (Open), Pi (Initial quote), Pf (Final quote), Pd (Dash), or Po
        # (Other)

        if not before or before.isspace() or before in {"-", ":", "/"}:
            return False

        if before not in {"'", '"', "<", "(", "[", "{"} and \
                unicodedata.category(before) in {"Pd", "Po"}:
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

        # The docutils.utils.punctuation_chars.match_chars(c1, c2) function
        # will test whether `c1` and `c2` are a matching open/close character
        # pair. Use it if available.
        try:
            from docutils.utils.punctuation_chars import match_chars
        except ImportError:
            pass
        else:
            return match_chars(before, text[0])

        # Otherwise use a less accurate heuristic
        if before == "'" and text[0] != "'":
            return False

        if before == '"' and text[0] != '"':
            return False

        if before == "<" and text[0] != ">":
            return False

        if before == "(" and text[0] != ")":
            return False

        if before == "[" and text[0] != "]":
            return False

        if before == "{" and text[0] != "}":
            return False

        if unicodedata.category(before) in {"Ps", "Pi", "Pf"}:
            if unicodedata.category(text[0]) not in {"Pe", "Pi", "Pf"}:
                return False

        return True

    @staticmethod
    def should_escape_suffix(tail):
        """
        Return if ``\\`` should be appended to the inline markup string.

        :param tail: the text that will follow the inline markup
        """

        # Inline markup end-strings must end a text block or be immediately
        # followed by whitespace, one of the ASCII characters:
        #   - . , : ; ! ? \ / ' " ) ] } >
        # Or a similar non-ASCII punctuation character from Unicode categories
        # Pe (Close), Pi (Initial quote), Pf (Final quote), Pd (Dash), or Po
        # (Other).
        follow = tail[:1]

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

    def escape_inline_text(self, text):
        """Escape *text* to be rendered inside of an inline markup string."""

        # Inline markup cannot be nested
        text = text.replace("\\", "\\\\")
        if self.escape:
            text = text.replace(self.escape, f"\\{self.escape}")
        return text

    def render(self, node, *args, **kwargs):
        """Render the *node*."""
        return self.render_text(node.text, node.tail, *args, **kwargs)

    def render_text(self, text, tail, buffer=""):
        """Render *text* as inline markup and its *tail* as normal text."""

        # Inline markup start-strings must be immediately followed by
        # non-whitespace. Inline markup end-strings must be immediately
        # preceded by non-whitespace.

        # Handled by trim_inline(), remove_null_inline() in the adjuster

        # The inline markup end-string must be separated by at least one
        # character from the start-string.
        if not text:
            return escape_text(tail or "")

        # Escape the text before we decide whether to escape the prefix
        text = self.escape_inline_text(text)

        prefix = self.prefix
        if self.should_escape_prefix(text, buffer[-1:]):
            prefix = f"\\ {prefix}"

        # Escape the tail before we decide whether to escape the suffix
        tail = escape_text(tail or '')

        suffix = self.suffix
        if self.should_escape_suffix(tail):
            suffix = f"{suffix}\\"

        return f"{prefix}{text}{suffix}{tail}"


class RoleRenderer(InlineRenderer):
    def __init__(self, role):
        super().__init__(f":{role}:`", "`")


bold_renderer = InlineRenderer("**")
emphasis_renderer = InlineRenderer("*")
computeroutput_renderer = InlineRenderer("``")
subscript_renderer = RoleRenderer("subscript")
superscript_renderer = RoleRenderer("superscript")
