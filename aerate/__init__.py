from sphinx.util import logging
from typing import Any, Tuple, List

from docutils import nodes
from docutils.parsers.rst import Directive
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
        return "void " + self.name + "()"

    def resolve_name(self, modname: str, parents: Any, path: str, base: Any
                     ) -> Tuple[str, List[str]]:
        return base, []

    def import_object(self) -> bool:
        return True

    def get_doc(self, *args, **kwargs) -> List[List[str]]:
        from lxml import etree
        import os
        import re
        import textwrap

        from aerate.canonicalize import canonicalize_para
        from aerate.mutation import MutationCursor
        from aerate.render import render_para

        SCRIPT_ROOT = os.path.dirname(os.path.realpath(__file__))

        actual_out = ""

        with open(os.path.join(SCRIPT_ROOT, "..", "xml", "insert_8h.xml")) as file:
            parser = etree.XMLParser(ns_clean=True,
                                    remove_blank_text=True,
                                    remove_comments=True,
                                    remove_pis=True)
            document = etree.parse(file, parser)

        # for function in reversed(document.xpath(r'//memberdef[@kind="function"]')):
        for function in document.xpath(r'//memberdef[@kind="function"]'):
            (definition,) = function.xpath("./definition")
            (argsstring,) = function.xpath("./argsstring")

            # print(f".. c:function:: {definition.text}{argsstring.text}\n")

            (briefdescription,) = function.xpath("./briefdescription")

            output = []
            for node in briefdescription:
                if node.tag != "para":
                    raise NotImplementedError(f"Can't handle <{node.tag}> in <briefdescription>")
                para_output = render_para(node)
                output.append(para_output.rstrip())
            actual_out += "\n\n".join(output) + "\n\n"
            # print(textwrap.indent("\n\n".join(output), " " * 3) + "\n\n")

            (detaileddescription,) = function.xpath("./detaileddescription")
            cursor = MutationCursor(detaileddescription).next()
            while cursor:
                if detaileddescription not in cursor.node.iterancestors():
                    break

                if cursor.node.tag != "para":
                    raise NotImplementedError(f"Can't handle <{cursor.node.tag}> in <{cursor.root.tag}>")

                canonicalize_para(cursor)

            # from lxml import etree
            # print(etree.tostring(detaileddescription, pretty_print=True).decode("utf-8"))
            # break

            output = []
            for node in detaileddescription:
                if node.tag != "para":
                    raise NotImplementedError(f"Can't handle <{node.tag}> in <detaileddescription>")
                para_output = render_para(node)
                output.append(para_output.rstrip())
            actual_out += "\n\n".join(output) + "\n\n"
            # print(textwrap.indent("\n\n".join(output), " " * 3) + "\n\n")

            return [actual_out.splitlines()]


def setup(application):
    application.add_autodocumenter(FunctionDocumenter)
    application.aerate = None

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
