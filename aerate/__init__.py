from aerate.aerate import Aerate
from aerate.sphinx import *
import os


def setup(sphinx):
    sphinx.setup_extension("sphinx.ext.autodoc")

    # The directory where Doxygen's XML output is. This should be the same as
    # the XML_OUTPUT configuration option in Doxygen.
    sphinx.add_config_value("aerate_doxygen_root",
                            os.path.join(sphinx.confdir, "xml"),
                            "env")

    sphinx.aerate = Aerate(sphinx.config.aerate_doxygen_root)
    sphinx.add_autodocumenter(FunctionDocumenter)
    sphinx.add_autodocumenter(TypeDocumenter)
    sphinx.add_autodocumenter(StructDocumenter)

    return {"version": "0.0.1", "parallel_read_safe": True}
