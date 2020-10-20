from aerate.aeration import Aeration
from aerate.engine import Renderer
from aerate.mutation import MutationEngine
from lxml import etree
from lxml.etree import XMLParser
import os

# The XML parser to be used to load each document
PARSER = XMLParser(
    ns_clean=True, remove_blank_text=True, remove_comments=True,
    remove_pis=True, strip_cdata=True)


class Aerate:
    def __init__(self, sphinx):
        self.sphinx = sphinx
        self.doxygen_root = sphinx.config.aerate_doxygen_root

        self.aeration_memo = {}

        self.document_memo = {}
        self.sentries = set()
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
            self.document_memo[name] = etree.parse(
                os.path.join(self.doxygen_root, name),
                PARSER)
        self.signal_document_used(name)
        return self.document_memo[name]

    def signal_document_used(self, name):
        for sentry in self.sentries:
            sentry.signal_document_used(name)

    def detect_used(self):
        """Return a `DocumentSentry` to observe the instance."""
        return DocumentSentry(self)

    def find_member(self, name, kind=None):
        """Find and return the aeration of a member by *name* and *kind*."""

        if kind is not None:
            result = self.document.xpath(
                ".//member[name/text()=$name and @kind=$kind]",
                name=name,
                kind=kind)
        else:
            result = self.document.xpath(
                ".//member[name/text()=$name]",
                name=name)

        if not result:
            raise LookupError(f"No <member> with name {name!r} in index.xml")
        # TODO: handle this
        return self[result[0].attrib["refid"]]

    def canonical_node_by_id(self, id):
        """Return the canonical <compound> or <member> node for an *id*."""

        # Search for a <compound> or <member> node with a refid = id
        result = self.document.xpath(
            "//*[(self::compound or self::member) and @refid=$id]",
            id=id)

        if not result:
            raise LookupError(f"No <compound> or <member> with refid {id!r} "
                              "in index.xml")

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
        def is_canonical(node):
            parent_id = node.getparent().attrib["refid"]
            id = node.attrib["refid"]
            return id.startswith(parent_id)
        last_resort = result[0]
        result = list(filter(is_canonical, result))

        if len(result) == 1:
            return result[0]
        elif not result:
            # If we can't find a canonical node with this criteria then return
            # any node
            return last_resort

        return max(result, key=lambda node: len(node.getparent()["refid"]))


class DocumentSentry:
    """Used to track the documents used by aerate used over an interval."""

    def __init__(self, aerate):
        self.aerate = aerate
        self.record = set()

    def __enter__(self):
        self.aerate.sentries.add(self)
        return self

    def __exit__(self, *args, **kwargs):
        self.aerate.sentries.remove(self)

    def signal_document_used(self, name):
        self.record.add(name)
