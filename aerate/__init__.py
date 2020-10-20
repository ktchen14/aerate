from aerate.sphinx import FunctionDocumenter, MacroDocumenter, TypeDocumenter, StructDocumenter
import os

__all__ = ("setup")


def setup(sphinx):
    sphinx.setup_extension("sphinx.ext.autodoc")

    # The location of the XML output from Doxygen (should be the same as the
    # XML_OUTPUT option in Doxygen). The default is an "xml" subdirectory in
    # the directory containing the Sphinx configuration file (`conf.py`).
    sphinx.add_config_value("aerate_doxygen_root",
                            os.path.join(sphinx.confdir, "xml"),
                            "env")

    sphinx.add_event("aerate-generate-anchor")

    sphinx.aerate = None
    sphinx.add_autodocumenter(FunctionDocumenter)
    sphinx.add_autodocumenter(MacroDocumenter)
    sphinx.add_autodocumenter(TypeDocumenter)
    sphinx.add_autodocumenter(StructDocumenter)

    return {"version": "0.0.1", "parallel_read_safe": True}
