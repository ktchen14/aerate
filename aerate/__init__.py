from aerate.aerate import Aerate
from aerate.sphinx import FunctionDocumenter, TypeDocumenter, StructDocumenter
import os


import sphinx.domains.c

# Define an "aerate_id" option on CObject
from docutils.parsers.rst import directives
sphinx.domains.c.CObject.option_spec["aerate_id"] = directives.unchanged

from typing import cast
origin_add_target_and_index = sphinx.domains.c.CObject.add_target_and_index
def aerate_add_target_and_index(self, ast, sig, signode):
    args = (self, ast, sig, signode)
    domain = cast(sphinx.domains.c.CDomain, self.env.get_domain("c"))

    aerate_id = self.options.get("aerate_id")
    if aerate_id is None or aerate_id in domain.aerate:
        return origin_add_target_and_index(*args)

    keys = set(domain.objects.keys())
    result = origin_add_target_and_index(*args)
    for name in domain.objects.keys() - keys:
        domain.aerate[aerate_id] = name

    return result
sphinx.domains.c.CObject.add_target_and_index = aerate_add_target_and_index

# Define CDomain.aerate as a readable property
def aerate(self):
    return self.data.setdefault("aerate", {})  # id -> fullname
sphinx.domains.c.CDomain.aerate = property(aerate)

# Insert an "aerate" item into CDomain.initial_data
sphinx.domains.c.CDomain.initial_data["aerate"] = {}  # id -> fullname

# Handle CDomain.aerate in CDomain.clear_doc
origin_clear_doc = sphinx.domains.c.CDomain.clear_doc
def aerate_clear_doc(self, docname: str) -> None:
    result = origin_clear_doc(self, docname)
    for id, fullname in list(self.aerate.items()):
        object = self.objects.get(fullname)
        if object is not None and object[0] == docname:
            del self.aerate[id]
    return result
sphinx.domains.c.CDomain.clear_doc = aerate_clear_doc

# Handle CDomain.aerate in CDomain.merge_domaindata
origin_merge_domaindata = sphinx.domains.c.CDomain.merge_domaindata
def aerate_merge_domaindata(self, docnames, otherdata):
    result = origin_merge_domaindata(self, docnames, otherdata)

    ourObjects = self.data["objects"]
    ourAerate = self.data["aerate"]
    for id, fullname in otherdata["aerate"].items():
        object = ourObjects.get(fullname)
        if object is not None and object[0] in docnames:
            if id not in ourAerate:
                ourAerate[id] = fullname

    return result
sphinx.domains.c.CDomain.merge_domaindata = aerate_merge_domaindata

# Look in CDomain.aerate in CDomain._resolve_xref_inner
from sphinx.util.nodes import make_refnode
origin__resolve_xref_inner = sphinx.domains.c.CDomain._resolve_xref_inner
def aerate__resolve_xref_inner(self, env, fromdocname, builder, typ, target,
                               node, contnode):
    args = (self, env, fromdocname, builder, typ, target, node, contnode)

    if not target.startswith("aerate_id="):
        return origin__resolve_xref_inner(*args)

    fullname = self.aerate.get(target[len("aerate_id="):])
    if fullname is None:
        return None, None

    object = self.objects.get(fullname)
    if object is None:
        return None, None

    docname, node_id, objtype = object
    return make_refnode(builder, fromdocname, docname, node_id, contnode,
                        fullname), objtype
sphinx.domains.c.CDomain._resolve_xref_inner = aerate__resolve_xref_inner


def setup(sphinx):
    sphinx.setup_extension("sphinx.ext.autodoc")

    # The location of the XML output from Doxygen (should be the same as the
    # XML_OUTPUT option in Doxygen). The default is an "xml" subdirectory in
    # the directory containing the Sphinx configuration file (`conf.py`).
    sphinx.add_config_value("aerate_doxygen_root",
                            os.path.join(sphinx.confdir, "xml"),
                            "env")

    sphinx.aerate = None
    sphinx.add_autodocumenter(FunctionDocumenter)
    sphinx.add_autodocumenter(TypeDocumenter)
    sphinx.add_autodocumenter(StructDocumenter)

    return {"version": "0.0.1", "parallel_read_safe": True}
