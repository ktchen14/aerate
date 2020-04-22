import collections.abc
import os

from lxml import etree
from lxml.etree import XMLParser


class DocumentableObject:
    def __init__(self, node):
        self.node = node

    @property
    def name(self):
        return self.node.find("name").text

    @property
    def id(self):
        return self.attrib["id"]

    @property
    def kind(self):
        return self.attrib["kind"]


class Index(collections.abc.Mapping):
    def __init__(self, doxygen_root):
        self.doxygen_root = doxygen_root

        parser = XMLParser(ns_clean=True,
                           remove_blank_text=True,
                           remove_comments=True,
                           remove_pis=True,
                           strip_cdata=True)

        with open(os.path.join(doxygen_root, "index.xml")) as file:
            self.document = etree.parse(file, parser)

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

    def __getitem__(self, id):
        result = self.document.xpath("//*[@refid=$refid]", refid=id)
        if not result:
            raise KeyError(repr(id))

        # A single object can be in multiple places in Doxygen. e.g.:
        # <compound refid="vector_2common_8h" kind="file"><name>common.h</name>
        #   <member refid="vector_2common_8h_1a269b0ad6ebf33c6a47a1f939d6e94e0a" kind="typedef"><name>blah</name></member>
        #   <member refid="group__vector__module_1ga5b7d6c2eb384dea49554e889ad2740ad" kind="typedef"><name>vector_t</name></member>
        # </compound>
        documentable_object = DocumentableObject(result[0])
        return documentable_object
