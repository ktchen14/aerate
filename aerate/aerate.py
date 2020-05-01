from aerate.engine import Engine
from aerate.index import Index
from aerate.mutation import MutationEngine
from aerate.render import Renderer


class Aerate:
    def __init__(self, root):
        self.index = Index(root)
        self.index.aerate = self

        self.adjuster = MutationEngine(self, recipe="aerate.recipe.adjuster")
        self.renderer = Renderer(self)

    def render(self, node, *args, **kwargs):
        return self.renderer.invoke(node, *args, **kwargs)
