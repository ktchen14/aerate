import collections.abc
import os

from lxml import etree
from lxml.etree import XMLParser


class Aeration:
    def __init__(self, index, index_node):
        self.index = index
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

    @property
    def node(self):
        if self._node is None:
            compound_node = self.index_node
            if self.index_node.tag == "member":
                compound_node = compound_node.getparent()

            relative_path = compound_node.attrib["refid"] + ".xml"

            document = self.index.load_document(relative_path)
            if self.index_node.tag == "compound":
                result = document.xpath(r'//compounddef[@id=$refid and @kind=$kind]',
                                        refid=self.id, kind=self.kind)
            elif self.index_node.tag == "member":
                result = document.xpath(r'//memberdef[@id=$refid and @kind=$kind]',
                                        refid=self.id, kind=self.kind)
            self._node = result[0]
        return self._node


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
        self.document_memo = {"index.xml": self.document}

    def load_document(self, name):
        if name not in self.document_memo:
            path = os.path.join(self.doxygen_root, name)
            document = etree.parse(path, self.parser)
            self.document_memo[name] = document
        return self.document_memo[name]

    def find(self, kind, id):
        # kind must be either "compound" or "member"
        if kind == "compound":
            result = self.document.xpath("//compound[@refid=$refid]", refid=id)
            if len(result) > 1:
                result = result[0]
        else:
            result = self.document.xpath("//member[@refid=$refid]", refid=id)
            if len(result) > 1:
                result = result[0]
        return result.get("kind"), result.xpath("./name")[0].text

    def find_by_id(self, id):
        result = self.document.xpath("//*[@refid=$refid]", refid=id)
        if not result:
            raise KeyError(repr(id))
        elif len(result) > 1:
            result = result[0]
        return Aeration(self, result)

    def find_module_by_name(self, name):
        result = self.document.xpath(r'//compound[name/text()=$name]',
                                     name=name)
        if not result:
            raise KeyError(repr(name))
        elif len(result) > 1:
            pass
            # raise KeyError(repr(name))

        return Aeration(self, result[0])

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

        return Aeration(self, result[0])
