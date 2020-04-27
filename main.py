from lxml import etree
import os
import re
import textwrap

from aerate.canonicalize import canonicalization_engine
from aerate.canonicalize import canonicalize_para
from aerate.mutation import MutationCursor
from aerate.render import render_para

SCRIPT_ROOT = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(SCRIPT_ROOT, "xml", "insert_8h.xml")) as file:
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

    output = []
    for node in briefdescription:
        if node.tag != "para":
            raise NotImplementedError(f"Can't handle <{node.tag}> in <briefdescription>")
        para_output = render_para(node)
        output.append(para_output.rstrip())
    print(textwrap.indent("\n\n".join(output), " " * 3) + "\n\n")

    (detaileddescription,) = function.xpath("./detaileddescription")
    canonicalization_engine.handle(detaileddescription)
    # while cursor:
    #     if detaileddescription not in cursor.node.iterancestors():
    #         break

    #     if cursor.node.tag != "para":
    #         raise NotImplementedError(f"Can't handle <{cursor.node.tag}> in <{cursor.root.tag}>")

    #     canonicalize_para(cursor)

    # from lxml import etree
    # print(etree.tostring(detaileddescription, pretty_print=True).decode("utf-8"))
    # break

    output = []
    for node in detaileddescription:
        if node.tag != "para":
            raise NotImplementedError(f"Can't handle <{node.tag}> in <detaileddescription>")
        para_output = render_para(node)
        output.append(para_output.rstrip())
    print(textwrap.indent("\n\n".join(output), " " * 3) + "\n\n")

    break


        # paras += [render_para(para)]
    # emit("\n\n".join(paras))

    # print(function.get("id"))
