from aerate.aerate import Aerate
from aerate.sphinx import FunctionDocumenter
import os


def setup(sphinx):
    sphinx.aerate = Aerate(os.path.join(sphinx.confdir, "xml"))
    sphinx.add_autodocumenter(FunctionDocumenter)

    return {
        "version": "0.0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
