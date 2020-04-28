from lxml import etree
import os
import textwrap

from aerate.adjust import adjuster
from aerate.render import renderer

SCRIPT_ROOT = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(SCRIPT_ROOT, "xml", "access_8h.xml")) as file:
    parser = etree.XMLParser(ns_clean=True,
                             remove_blank_text=True,
                             remove_comments=True,
                             remove_pis=True)
    document = etree.parse(file, parser)

# for function in reversed(document.xpath(r'//memberdef[@kind="function"]')):
for function in document.xpath(r'//memberdef[@kind="function"]'):
    (definition,) = function.xpath("./definition")
    (argsstring,) = function.xpath("./argsstring")

    print(f".. c:function:: {definition.text}{argsstring.text}\n")

    (briefdescription,) = function.xpath("./briefdescription")
    adjuster.handle(briefdescription)
    output = renderer.handle(briefdescription)
    print(textwrap.indent(output, " " * 3) + "\n\n")

    (detaileddescription,) = function.xpath("./detaileddescription")
    adjuster.handle(detaileddescription)
    output = renderer.handle(detaileddescription)
    print(textwrap.indent(output, " " * 3) + "\n\n")
