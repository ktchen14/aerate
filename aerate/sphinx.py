from aerate.aerate import Aerate
from aerate.index import Aeration
from sphinx.ext.autodoc import Documenter
from sphinx.util import logging
from typing import Any, Tuple, List

__all__ = ("FunctionDocumenter",)

logger = logging.getLogger(__name__)


class AerateDocumenter(Documenter):
    domain = "c"

    @property
    def aerate(self) -> Aerate:
        """The `Aerate` instance in the documenter's Sphinx application."""
        return self.env.app.aerate


class FunctionDocumenter(AerateDocumenter):
    objtype = "cfunction"
    directivetype = "function"

    @classmethod
    def can_document_member(cls, member: Any, *args, **kwargs) -> bool:
        return isinstance(member, Aeration)

    def format_name(self) -> str:
        (definition_node,) = self.object.node.xpath("./definition")
        (argsstring_node,) = self.object.node.xpath("./argsstring")
        return definition_node.text + argsstring_node.text

    def resolve_name(self, modname: str, parents: Any, path: str, base: Any
                     ) -> Tuple[str, List[str]]:
        return base, []

    def import_object(self) -> bool:
        """Import the object given by *self.modname* and *self.objpath* and set
        it as *self.object*.

        Returns True if successful, False if an error occurred.
        """

        self.object = self.aerate.index.find_member_by_name(self.modname)
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
