from aerate.aerate import Aerate
from aerate.sphinx import FunctionDocumenter
import os


def setup(application):
    application.aerate = Aerate(os.path.join(application.confdir, "xml"))
    application.add_autodocumenter(FunctionDocumenter)

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
