from aerate.engine import Engine
from aerate.mutation import MutationEngine
from aerate.render import Renderer


class Aerate:
    def __init__(self, root):
        self.index = Index(root)
        self.index.aerate = self

        self.adjuster = MutationEngine(self)
        self.adjuster.load_recipe("aerate.recipe.adjuster")

        self.reformer = MutationEngine(self)

        self.renderer = Engine(self)
        self.renderer.load_recipe("aerate.recipe.renderer")

    def render(self, node, *args, **kwargs):
        return self.renderer.invoke(node, *args, **kwargs)


import collections.abc
import os

from lxml import etree
from lxml.etree import XMLParser


class Aeration:
    """
    An Aeration is a documentable object (either a "compound" or a "member").

    Each aeration is associated with an *index_node* from `index.xml` a *node*
    from the compound XML file that it's documented in.

    The *index_node* of an aeration will be either a ``<compound>`` or a
    ``<member>``. The *node* of an aeration will be either a ``<compounddef>``
    or a ``<memberdef>``.
    """

    def __init__(self, aerate, index_node):
        self.aerate = aerate
        self.index_node = index_node
        self._node = None

    @property
    def name(self):
        return self.index_node.find("name").text

    @property
    def id(self):
        return self.index_node.attrib["refid"]

    @property
    def kind(self):
        return self.index_node.attrib["kind"]

    def render(self, *args, **kwargs):
        return self.aerate.render(self, *args, **kwargs)


class CompoundAeration(Aeration):
    @property
    def node(self):
        """Return the definition node associated with the aeration."""

        if self._node is None:
            document = self.aerate.load_document(self.id + ".xml")
            result = document.xpath(r'//compounddef[@id=$id]', id=self.id)

            if len(result) > 1:
                raise LookupError(f"More than one <compounddef> with id {self.id!r} in {file!r}")
            if not result:
                raise LookupError(f"No <compounddef> with id {self.id!r} in {file!r}")

            self._node = result[0]
        return self._node


class MemberAeration(Aeration):
    @property
    def node(self):
        """Return the definition node associated with the aeration."""

        if self._node is None:
            file = self.index_node.getparent().attrib["refid"] + ".xml"
            document = self.aerate.load_document(file)
            result = document.xpath(r'//memberdef[@id=$id]', id=self.id)

            if len(result) > 1:
                raise LookupError(f"More than one <memberdef> with id {self.id!r} in {file!r}")
            if not result:
                raise LookupError(f"No <memberdef> with id {self.id!r} in {file!r}")

            self._node = result[0]
        return self._node


def make_aeration(aerate, node):
    return {
        "compound": CompoundAeration, "member": MemberAeration,
    }[node.tag](aerate, node)


class Index:
    def __init__(self, doxygen_root):
        self.doxygen_root = doxygen_root

        index_path = os.path.join(doxygen_root, "index.xml")
        self.parser = XMLParser(ns_clean=True,
                                remove_blank_text=True,
                                remove_comments=True,
                                remove_pis=True,
                                strip_cdata=True)
        self.document = etree.parse(index_path, self.parser)

        self.aeration_memo = {}
        self.document_memo = {"index.xml": self.document}

    def load_document(self, name):
        if name not in self.document_memo:
            path = os.path.join(self.doxygen_root, name)
            document = etree.parse(path, self.parser)
            self.document_memo[name] = document
        return self.document_memo[name]

    def find_by_id(self, id):
        """Find a documentable object from its id."""

        if id not in self.aeration_memo:
            result = self.document.xpath(
                "//*[(self::compound or self::member) and @refid=$refid]",
                refid=id)
            if not result:
                raise KeyError(repr(id))

            # This is a lookup by id so all results should be identical
            node = result[0]
            self.aeration_memo[id] = make_aeration(self, node)
        return self.aeration_memo[id]

    def find_module_by_name(self, name):
        result = self.document.xpath(r'//compound[name/text()=$name]',
                                     name=name)

        if not result:
            raise KeyError(repr(name))

        if len({node.attrib["refid"] for node in result}) > 1:
            pass
            # raise KeyError(repr(name))

        return make_aeration(self, result[0])

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

        return make_aeration(self, result[0])
