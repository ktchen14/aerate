from aerate.engine import Engine


class Renderer(Engine):
    def on_unaccepted(self, node, *args, **kwargs):
        return node.xpath("string()")
