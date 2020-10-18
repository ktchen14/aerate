from aerate.aeration import Aeration
from aerate.mutation import MutationEngine
from aerate.render import Renderer
from lxml import etree
from lxml.etree import XMLParser
import os


class Aerate:
    def __init__(self, sphinx):
        self.sphinx = sphinx

        # The XML parser and Doxygen root to be used to load each document
        self.parser = XMLParser(ns_clean=True,
                                remove_blank_text=True,
                                remove_comments=True,
                                remove_pis=True,
                                strip_cdata=True)
        self.doxygen_root = sphinx.config.aerate_doxygen_root

        self.aeration_memo = {}
        self.document_memo = {}

        self.document = self.load_document("index.xml")

        self.adjuster = MutationEngine(self)
        self.adjuster.load_recipe("aerate.recipe.adjuster")

        self.reformer = MutationEngine(self)

        self.renderer = Renderer(self)
        self.renderer.load_recipe("aerate.recipe.renderer")

    def __getitem__(self, id):
        """Return the aeration of an object from its *id*."""
        if id not in self.aeration_memo:
            node = self.canonical_node_by_id(id)
            self.aeration_memo[id] = Aeration.make(self, node)
        return self.aeration_memo[id]

    def adjust(self, node, *args, **kwargs):
        """Use the configured adjuster to adjust the *node*."""
        return self.adjuster.handle(node, *args, **kwargs)

    def reform(self, node, *args, **kwargs):
        """Use the configured reformer to reform the *node*."""
        return self.reformer.handle(node, *args, **kwargs)

    def render(self, node, *args, **kwargs):
        """Use the configured renderer to render the *node*."""
        return self.renderer.invoke(node, *args, **kwargs)

    def load_document(self, name):
        """Load and memoize an XML document from the Doxygen root."""

        if name not in self.document_memo:
            path = os.path.join(self.doxygen_root, name)
            self.document_memo[name] = etree.parse(path, self.parser)
        return self.document_memo[name]

    def aeration_of(self, node):
        if node.tag == "compound":
            id = node.attrib["refid"]
            if id not in self.aeration_memo:
                self.aeration_memo[id] = CompoundAeration(self, node)
            return self.aeration_memo[id]

        if node.tag == "member":
            return self[node.attrib["refid"]]

        if node.tag == "compounddef":
            return self[node.attrib["id"]]

        if node.tag == "memberdef":
            return self[node.attrib["id"]]

        raise ValueError(f"Node <{node.tag}> isn't a <compound>, <member>, <compounddef>, or <memberdef>")

    def find_file(self, name):
        result = self.document.xpath(
            r'//compound[@kind="file" and name/text()=$name]',
            name=os.path.basename(name))

        for node in result:
            aeration = self.aeration_of(node)
            (location_node,) = aeration.matter.xpath("/location")
            if location_node is None or location_node.get("file") != name:
                continue
            return aeration

    def find_module_by_name(self, name):
        result = self.document.xpath(r'//compound[name/text()=$name]',
                                     name=name)

        if not result:
            raise KeyError(repr(name))

        if len({node.attrib["refid"] for node in result}) > 1:
            pass
            # raise KeyError(repr(name))

        return Aeration.make(self, result[0])

    def find_member_by_name(self, name):
        result = self.document.xpath(r'.//member[name/text()=$name]', name=name)

        if not result:
            raise LookupError(f"No member with name {name!r}")

        if len(result) == 1:
            id = result[0].attrib["refid"]
            if id not in self.aeration_memo:
                self.aeration_memo[id] = Aeration.make(result[0])
            return self.aeration_memo[id]

        ids = {node.attrib["refid"] for node in result}
        if len(ids) > 1:
            raise LookupError(f"Too many results for {name!r}")
        id = result[0].attrib["refid"]
        return self[id]

    # def find_member_by_name(self, name, module=None):
    #     if module is None:
    #         search_root = self.document
    #     elif not isinstance(module, Aeration):
    #         search_root = self.find_module_by_name(module).index_node
    #     else:
    #         search_root = module.index_node

    #     result = search_root.xpath(r'.//member[name/text()=$name]', name=name)

    #     if not result:
    #         raise KeyError(repr(name))
    #     elif len(result) > 1:
    #         pass
    #         # raise KeyError(repr(name))

    #     return Aeration.make(self, result[0])

    def canonical_node_by_id(self, id):
        """Return the canonical <compound> or <member> node for an *id*."""

        # Search for a <compound> or <member> node with a refid = id
        result = self.document.xpath(
            "//*[(self::compound or self::member) and @refid=$id]",
            id=id)

        if not result:
            raise LookupError(f"No <compound> or <member> with refid {id!r} in index.xml")

        # Return a unique result
        if len(result) == 1:
            return result[0]

        # A <compound> should be unique in index.xml. If there are multiple
        # results, then each should be a <member> with a <compound> parent. The
        # canonical node is the one that's located inside of a <compound> with
        # a refid that's a prefix of the <member>'s refid. If more than one
        # <member> satisfies this requirement, then the one inside the
        # <compound> with the longest refid is the canonical one. Two refids
        # can't be the same length if both are a prefix of a <member>'s refid.
        last_resort = result[0]
        result = list(filter(
            lambda node: node.attrib["refid"].startswith(node.getparent().attrib["refid"]),
            result))

        if len(result) == 1:
            return result[0]
        elif not result:
            # If we can't find a canonical node with this criteria then return
            # any node
            return last_resort

        return max(result, key=lambda node: len(node.getparent()["refid"]))
