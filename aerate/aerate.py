from aerate.adjust import adjuster
from aerate.index import Index
from aerate.render import renderer

from aerate.rule import RenderEngine, RuleEngine


class Aerate:
    def __init__(self, root):
        self.index = Index(root)
        self.index.aerate = self

        self.adjuster = adjuster
        self.adjuster.aerate = self

        self.renderer = renderer
        self.renderer.aerate = self

    def render(self, node, *args, **kwargs):
        return self.renderer.handle(node, *args, **kwargs)
