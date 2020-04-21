from lxml import etree
import os


class Index:
    def __init__(self, doxygen_root):
        self.doxygen_root = doxygen_root

        with open(os.path.join(doxygen_root, "index.xml")) as file:
            self.document = etree.parse(file)

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
