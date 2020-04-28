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

for function_node in document.xpath(r'//memberdef[@kind="function"]'):
    adjuster.handle(function_node)
    print(renderer.handle(function_node))
