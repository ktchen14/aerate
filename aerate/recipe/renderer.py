from aerate.engine import Renderer
from aerate.schema import (
    DESCRIPTION_TAGS, SchemaError, is_inline, is_structural,
)
from aerate.render import (
    escape_text, ulink_renderer, bold_renderer, emphasis_renderer,
    math_renderer, computeroutput_renderer, subscript_renderer,
    superscript_renderer, xref_func_renderer, xref_macro_renderer)
import re
import textwrap

engine: Renderer = engine  # Stop "F821 undefined name 'engine'"


# The simplesect's kind must be "see", "return", "author", "authors",
# "version", "since", "date", "note", "warning", "pre", "post", "copyright",
# "invariant", "remark", "attention", "par", or "rcs"

@engine.rule("simplesect", when=lambda node: node.get("kind") == "return")
def render_simplesect_return(self, node, before=""):
    prefix = ":return: "
    output = render_simplesect(self, node, before)
    output = textwrap.indent(output, " " * len(prefix)).strip()
    return prefix + output + "\n\n"


@engine.rule("simplesect", when=lambda node: node.get("kind") in {
    "attention", "note", "warning"})
def render_simplesect_admonition(self, node, before=""):
    prefix = f".. {node.get('kind')}::"
    output = render_simplesect(self, node, before)
    output = textwrap.indent(output, " " * 3)
    return prefix + "\n\n" + output + "\n\n"


@engine.rule("simplesect", when=lambda node: node.get("kind") == "remark")
def render_simplesect_remark(self, node, before=""):
    prefix = f".. admonition:: Remark"
    output = render_simplesect(self, node, before)
    output = textwrap.indent(output, " " * 3)
    return prefix + "\n\n" + output + "\n\n"


@engine.rule("simplesect", when=lambda node: node.get("kind") == "see")
def render_simplesect_see(self, node, before=""):
    prefix = ".. seealso::"
    output = render_simplesect(self, node, before)
    output = textwrap.indent(output, " " * 3)
    return prefix + "\n\n" + output + "\n\n"


@engine.rule("simplesect", when=lambda node: node.get("kind") == "par")
def render_simplesect_par(self, node, before=""):
    prefix = ".. admonition:: " + node.xpath("./title/text()")[0]
    output = render_simplesect(self, node, before)
    output = textwrap.indent(output, " " * 3)
    return prefix + "\n\n" + output + "\n\n"


@engine.rule("simplesect")
def render_simplesect(self, node, before=""):
    output = "\n\n".join(
        self.invoke(para) for para in node.iterchildren("para")
    ) + "\n\n"
    return output


@engine.rule("ref", within="para", when=lambda node: node.get("external"))
def render_ref_external(self, node, before=""):
    return f"`!{node.text}`{node.tail or ''}"


@engine.rule("ref", within="para")
def render_ref(self, node, before=""):
    refid = node.attrib["refid"]
    try:
        target = self.aerate[refid]
    except LookupError:
        return f"`!{node.text}`{node.tail or ''}"

    if target.kind == "function":
        if node.text in {target.anchor, f"{target.anchor}()"}:
            inside = node.text
        else:
            inside = f"{node.text} <{target.anchor}>"
        return xref_func_renderer.render_text(inside, node.tail, before)
    elif target.kind == "define":
        if node.text == target.anchor:
            inside = node.text
        else:
            inside = f"{node.text} <{target.anchor}>"
        return xref_macro_renderer.render_text(inside, node.tail, before)
    elif target.kind == "typedef":
        if target.name == node.text:
            return f":c:type:`{target.name}`{node.tail or ''}"
        else:
            return f":c:type:`{node.text} <{target.name}>`{node.tail or ''}"

    return f"`!{node.text}`{node.tail or ''}"


@engine.rule("programlisting")
def render_programlisting(self, node, before=""):
    prefix = ".. code-block:: c\n\n"
    output = "\n".join(self.invoke(item) for item in node)
    return prefix + textwrap.indent(output, " " * 3)


@engine.rule("ulink")
def render_ulink(self, node, before=""):
    return ulink_renderer.render(node, before)


@engine.rule("bold")
def render_bold(self, node, before=""):
    return bold_renderer.render(node, before)


@engine.rule("emphasis")
def render_emphasis(self, node, before=""):
    return emphasis_renderer.render(node, before)


@engine.rule("computeroutput")
def render_computeroutput(self, node, before=""):
    return computeroutput_renderer.render(node, before)


@engine.rule("subscript")
def render_subscript(self, node, before=""):
    return subscript_renderer.render(node, before)


@engine.rule("superscript")
def render_superscript(self, node, before=""):
    return superscript_renderer.render(node, before)


@engine.rule("formula", when=lambda node: is_structural(node))
def render_structural_formula(self, node, before=""):
    assert not node.tail, "structural node in <para> shouldn't have tail text"
    prefix = ".. math::\n   :nowrap:\n\n"
    return prefix + textwrap.indent(node.text, " " * 3)


@engine.rule("formula", when=lambda node: is_inline(node))
def render_inline_formula(self, node, before=""):
    render_text = math_renderer.render_text

    # Trim $ from the node text
    text = re.sub(r"^\s*\$\s*", "", node.text)
    text = re.sub(r"\s*\$\s*$", "", text)
    return render_text(text, node.tail, before=before)


@engine.rule("listitem", within="itemizedlist")
def render_listitem(self, node, before=""):
    output = escape_text(node.text or "")
    for item in node:
        if item.tag != "para":
            raise SchemaError(f"Can't handle <{item.tag}> in <{node.tag}>")
        output += self.invoke(item, before=output or "- ")
    output = textwrap.indent(output, " " * 2).strip()
    return f"- {output}\n"

@engine.rule("itemizedlist")
def render_itemizedlist(self, node, before=""):
    output = escape_text(node.text or "")
    for item in node:
        output += self.invoke(item, before=output)
    return output + "\n"

@engine.rule("para")
def render_para(self, node, before=""):
    output = escape_text(node.text or "")
    for item in node:
        output += self.invoke(item, before=output)
    return output + "\n\n"


@engine.rule("parameterlist", when=lambda node: node.get("kind") == "param")
def render_parameterlist(self, node, before=""):
    buffer = ""
    for item in node.xpath("./parameteritem"):
        (name,) = item.xpath("./parameternamelist/parametername[1]/text()")
        (description_node,) = item.xpath("./parameterdescription")

        output = f":param {name}: "
        description_output = self.invoke(description_node, before=output)

        output += textwrap.indent(description_output, " " * len(output)).strip()
        buffer += "\n" + output
    return buffer + "\n\n"


@engine.rule(*DESCRIPTION_TAGS)
def render_description(self, node, before=""):
    output = []
    for item in node:
        if item.tag != "para":
            raise SchemaError(f"Can't handle <{item.tag}> in <{node.tag}>")
        output.append(self.invoke(item).rstrip())
    return "\n\n".join(output)


@engine.rule("memberdef", when=lambda node: node.get("kind") == "function")
def render_function_definition(self, node, buffer=""):
    (definition,) = node.xpath("./definition")
    (argsstring,) = node.xpath("./argsstring")

    output = f".. c:function:: {definition.text}{argsstring.text}\n\n"

    (briefdescription,) = node.xpath("./briefdescription")
    description_output = self.invoke(briefdescription)
    output += textwrap.indent(description_output, " " * 3) + "\n\n"

    (detaileddescription,) = node.xpath("./detaileddescription")
    description_output = self.invoke(detaileddescription)
    output += textwrap.indent(description_output, " " * 3) + "\n\n"

    (inbodydescription,) = node.xpath("./inbodydescription")
    description_output = self.invoke(inbodydescription)
    output += textwrap.indent(description_output, " " * 3) + "\n\n"

    return output


@engine.rule("memberdef", when=lambda node: node.get("kind") == "typedef")
def render_typedef_definition(self, node, buffer=""):
    (type_node,) = node.xpath("./type")
    (name_node,) = node.xpath("./name")

    output = f".. c:type:: {type_node.text} {name_node.text}\n\n"

    (briefdescription,) = node.xpath("./briefdescription")
    description_output = self.invoke(briefdescription)
    output += textwrap.indent(description_output, " " * 3) + "\n\n"

    (detaileddescription,) = node.xpath("./detaileddescription")
    description_output = self.invoke(detaileddescription)
    output += textwrap.indent(description_output, " " * 3) + "\n\n"

    (inbodydescription,) = node.xpath("./inbodydescription")
    description_output = self.invoke(inbodydescription)
    output += textwrap.indent(description_output, " " * 3) + "\n\n"

    return output
