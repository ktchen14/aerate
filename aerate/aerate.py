from aerate.aeration import Aeration
from aerate.mutation import MutationEngine
from aerate.render import Renderer
from lxml import etree
from lxml.etree import XMLParser
import os


class Aerate:
    def __init__(self, doxygen_root):
        # The XML parser and Doxygen root to be used to load each document
        self.parser = XMLParser(ns_clean=True,
                                remove_blank_text=True,
                                remove_comments=True,
                                remove_pis=True,
                                strip_cdata=True)
        self.doxygen_root = doxygen_root

        self.aeration_memo = {}
        self.document_memo = {}

        self.document = self.load_document("index.xml")

        self.adjuster = MutationEngine(self)
        self.adjuster.load_recipe("aerate.recipe.adjuster")

        self.reformer = MutationEngine(self)

        self.renderer = Renderer(self)
        self.renderer.load_recipe("aerate.recipe.renderer")

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
        """Load and remember an XML document from the Doxygen root."""

        if name not in self.document_memo:
            path = os.path.join(self.doxygen_root, name)
            self.document_memo[name] = etree.parse(path, self.parser)
        return self.document_memo[name]

    def find_by_id(self, id):
        """Return the aeration of an object from its *id*."""

        if id not in self.aeration_memo:
            node = self.canonical_node_by_id(id)
            aeration = Aeration.make(self, node)
            self.aeration_memo[id] = aeration
        return self.aeration_memo[id]

    def find_module_by_name(self, name):
        result = self.document.xpath(r'//compound[name/text()=$name]',
                                     name=name)

        if not result:
            raise KeyError(repr(name))

        if len({node.attrib["refid"] for node in result}) > 1:
            pass
            # raise KeyError(repr(name))

        return Aeration.make(self, result[0])

    def find_member_by_name(self, name, module=None):
        if module is None:
            search_root = self.document
        elif not isinstance(module, Aeration):
            search_root = self.find_module_by_name(module).index_node
        else:
            search_root = module.index_node

        result = search_root.xpath(r'.//member[name/text()=$name]', name=name)

        if not result:
            raise KeyError(repr(name))
        elif len(result) > 1:
            pass
            # raise KeyError(repr(name))

        return Aeration.make(self, result[0])

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
        result = filter(lambda node:
                        node["refid"].startswith(node.getparent()["refid"]),
                        result)

        if len(result) == 1:
            return result[0]
        elif not result:
            # If we can't find a canonical node with this criteria then return
            # any node
            return last_resort

        return max(result, key=lambda node: len(node.getparent()["refid"]))

    def find_file(self, name):
        result = self.document.xpath(
            r'//compound[@kind="file" and name/text()=$name]',
            name=os.path.basename(name))

        for node in result:
            if node["id"] not in self.aeration_memo:
                self.aeration_memo[node["id"]] = make_aeration(self, node)
            aeration = self.aeration_memo[node["id"]]
            (location_node,) = aeration.node.xpath("/location")
            if location_node is None or location_node.get("file") != name:
                continue
            return aeration

