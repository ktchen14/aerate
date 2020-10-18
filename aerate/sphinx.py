from aerate.aerate import Aerate, Aeration
from docutils.parsers.rst import directives
from sphinx.ext.autodoc import Documenter
from sphinx.util import logging
from typing import Any, Tuple, List

__all__ = ("FunctionDocumenter", "TypeDocumenter", "StructDocumenter")

logger = logging.getLogger(__name__)


class AerationDocumenter(Documenter):
    """Specialized, abstract Documenter subclass for an `Aeration`."""

    # The "kind" of aeration to be handled by a subclass of this documenter
    aerationtype: str

    domain = "c"

    @classmethod
    def can_document_member(cls, member: Any, *args, **kwargs) -> bool:
        """Subclasses should only document a specific "kind" of Aeration."""
        if not isinstance(member, Aeration):
            return False
        return member.kind == cls.aerationtype

    @property
    def aerate(self) -> Aerate:
        """The `Aerate` instance in the documenter's Sphinx application."""
        if self.env.app.aerate is None:
            self.env.app.aerate = Aerate(self.env.app)
        return self.env.app.aerate

    def import_object(self) -> bool:
        """Set *self.object* to be the aeration to be documented."""

        self.object = self.aerate.find_member_by_name(self.modname)
        if self.object.kind != self.aerationtype:
            logger.warning(f"auto{self.objtype} name must reference a {self.aerationtype}")
            return False
        self.aerate.adjuster.handle(self.object.matter)
        return True

    def get_doc(self, *args, **kwargs) -> List[List[str]]:
        buffer = ""

        for prefix in ("brief", "detailed", "inbody"):
            (node,) = self.object.matter.xpath(f"./{prefix}description")
            output = self.aerate.render(node, before=buffer)
            if not output:
                continue
            buffer += ("\n\n" if buffer else "") + output

        return [buffer.splitlines()]

    def resolve_name(self, modname: str, parents: Any, path: str, base: Any
                     ) -> Tuple[str, List[str]]:
        """Return the name of the object to document as the module name."""
        return base, []


class FunctionDocumenter(AerationDocumenter):
    aerationtype = "function"
    objtype = "aeratefunction"
    directivetype = "function"

    option_spec = {
        **AerationDocumenter.option_spec,
        "file": directives.unchanged,
    }

    def format_name(self) -> str:
        anchor = self.object.anchor
        type_text = self.object.matter.xpath("string(./type)")
        (definition_node,) = self.object.matter.xpath("./definition")
        (argsstring_node,) = self.object.matter.xpath("./argsstring")
        return f"{type_text} {anchor}{argsstring_node.text}"
        # return definition_node.text + argsstring_node.text


class TypeDocumenter(AerationDocumenter):
    aerationtype = "typedef"
    objtype = "aeratetype"
    directivetype = "type"

    def format_name(self) -> str:
        (type_node,) = self.object.matter.xpath("./type")
        (name_node,) = self.object.matter.xpath("./name")
        return type_node.text + name_node.text


class StructDocumenter(AerationDocumenter):
    aerationtype = "struct"
    objtype = "aeratestruct"
    directivetype = "struct"

    def format_name(self) -> str:
        (type_node,) = self.object.matter.xpath("./type")
        (name_node,) = self.object.matter.xpath("./name")
        return type_node.text + name_node.text
