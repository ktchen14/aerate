from aerate.aerate import Aerate, Aeration
from sphinx.ext.autodoc import Documenter
from sphinx.util import logging
from typing import Any, Tuple, List

__all__ = ("FunctionDocumenter", "TypeDocumenter", "StructDocumenter")

logger = logging.getLogger(__name__)


class AerateDocumenter(Documenter):
    aerationtype: str
    domain = "c"

    @classmethod
    def can_document_member(cls, member: Any, *args, **kwargs) -> bool:
        return isinstance(member, Aeration) and member.kind == cls.aerationtype

    @property
    def aerate(self) -> Aerate:
        """The :class:`Aerate` instance in the documenter's Sphinx application."""
        return self.env.app.aerate

    def import_object(self) -> bool:
        self.object = self.aerate.index.find_member_by_name(self.modname)
        if self.object.kind != self.aerationtype:
            logger.warning(f"auto{self.objtype} name must be a {self.aerationtype!r}")
            return False
        self.aerate.adjuster.handle(self.object.node)
        return True

    def get_doc(self, *args, **kwargs) -> List[List[str]]:
        output = ""

        (briefdescription,) = self.object.node.xpath("./briefdescription")
        description_output = self.env.app.aerate.render(briefdescription)
        output += description_output + "\n\n"

        (detaileddescription,) = self.object.node.xpath("./detaileddescription")
        description_output = self.env.app.aerate.render(detaileddescription)
        output += description_output + "\n\n"

        (inbodydescription,) = self.object.node.xpath("./inbodydescription")
        description_output = self.env.app.aerate.render(inbodydescription)
        output += description_output + "\n\n"

        return [output.splitlines()]


class FunctionDocumenter(AerateDocumenter):
    aerationtype = "function"
    objtype = "cfunction"
    directivetype = "function"

    def format_name(self) -> str:
        (definition_node,) = self.object.node.xpath("./definition")
        (argsstring_node,) = self.object.node.xpath("./argsstring")
        return definition_node.text + argsstring_node.text

    def resolve_name(self, modname: str, parents: Any, path: str, base: Any
                     ) -> Tuple[str, List[str]]:
        return base, []


class TypeDocumenter(AerateDocumenter):
    aerationtype = "typedef"
    objtype = "ctype"
    directivetype = "type"

    def format_name(self) -> str:
        (type_node,) = self.object.node.xpath("./type")
        (name_node,) = self.object.node.xpath("./name")
        return type_node.text + name_node.text

    def resolve_name(self, modname: str, parents: Any, path: str, base: Any
                     ) -> Tuple[str, List[str]]:
        return base, []

class StructDocumenter(AerateDocumenter):
    aerationtype = "struct"
    objtype = "cstruct"
    directivetype = "struct"

    def format_name(self) -> str:
        (type_node,) = self.object.node.xpath("./type")
        (name_node,) = self.object.node.xpath("./name")
        return type_node.text + name_node.text

    def resolve_name(self, modname: str, parents: Any, path: str, base: Any
                     ) -> Tuple[str, List[str]]:
        return base, []
