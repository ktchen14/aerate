from aerate.engine import Engine


class Renderer(Engine):
    def __init__(self, *args, recipe="aerate.recipe.renderer", **kwargs):
        super().__init__(*args, recipe=recipe, **kwargs)

    def on_unaccepted(self, node, *args, **kwargs):
        return node.xpath("string()")
