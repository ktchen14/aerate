import os
from sphinx.util import logging
from typing import Any, Tuple, List

from aerate.aerate import Aerate
from sphinx.ext.autodoc import Documenter

logger = logging.getLogger(__name__)


class FunctionDocumenter(Documenter):
    objtype = "cfunction"
    domain = "c"
    directivetype = "function"

    @classmethod
    def can_document_member(cls, member: Any, membername: str, isattr: bool,
                            parent: Any) -> bool:
        """Called to see if a member can be documented by this documenter."""
        print("Can document!", member, membername, isattr, parent)
        return True

    def format_name(self) -> str:
        """Format the name of *self.object*."""

        (definition,) = self.object.node.xpath("./definition")
        (argsstring,) = self.object.node.xpath("./argsstring")
        return definition.text + argsstring.text

    def resolve_name(self, modname: str, parents: Any, path: str, base: Any
                     ) -> Tuple[str, List[str]]:
        return base, []

    def import_object(self) -> bool:
        """Import the object given by *self.modname* and *self.objpath* and set
        it as *self.object*.

        Returns True if successful, False if an error occurred.
        """
        self.object = self.env.app.aerate.index.find_member_by_name(self.modname)
        self.env.app.aerate.adjuster.handle(self.object.node)
        return True

    def get_doc(self, *args, **kwargs) -> List[List[str]]:
        import textwrap
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


def setup(application):
    application.add_autodocumenter(FunctionDocumenter)
    application.aerate = Aerate(os.path.join(application.confdir, "xml"))

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
