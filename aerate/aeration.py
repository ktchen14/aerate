from lxml.etree import Element, ElementTree


class Aeration:
    """
    An "aeration" is a documentable object (either a "compound" or a "member").

    Each aeration is associated with a *node* from ``index.xml``. This will be
    either a ``<compound>`` or a ``<member>``.

    Each aeration is also associated with a "definition" node, or *matter*,
    from the XML file that it or its compound is documented in. This will be
    either a ``<compounddef>`` or a ``<memberdef>``.
    """

    @staticmethod
    def make(aerate, node):
        """
        Make a `CompoundAeration` or `MemberAeration` from a *node*.

        The *node* must be a ``<compound>`` or ``<member>`` node from
        ``index.xml``.
        """

        return {
            "compound": CompoundAeration, "member": MemberAeration,
        }[node.tag](aerate, node)

    def __init__(self, aerate, node):
        self.aerate = aerate

        self._anchor = None
        self._node = node
        self._matter = None

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    @property
    def sphinx(self):
        return self.aerate.sphinx

    @property
    def id(self) -> str:
        """Return the "refid" of the aeration."""
        return self.node.attrib["refid"]

    @property
    def name(self) -> str:
        """Return the name of the aeration."""
        return self.node.find("name").text

    @property
    def kind(self) -> str:
        """Return the "kind" of the aeration."""
        return self.node.attrib["kind"]

    @property
    def anchor(self) -> str:
        """
        Return the string to use as the aeration's name in the directive line.

        The default implementation will return the aeration's name (from its
        ``<name>`` node in its matter). This is fine when an object of a
        specific kind is uniquely identifiable by its name. However, if a kind
        and name doesn't unique identify an object (e.g. objects with the same
        name exist in disparate compilation units), then this implementation
        will result in duplicate declaration issue, causing cross references to
        link to the incorrect documentation.

        To handle this case, an event "aerate-generate-anchor" is available to
        be handled to generate a different *anchor*.
        """

        if self._anchor is None:
            evname = "aerate-generate-anchor"
            anchor = self.sphinx.emit_firstresult(evname, self)
            self._anchor = anchor or self.name
        return self._anchor

    @property
    def node(self) -> Element:
        """Return the *node* of the aeration."""
        return self._node

    @property
    def matter(self) -> Element:
        """Memoize and return the *matter* of the aeration."""
        if self._matter is None:
            self._matter = self.retrieve_matter()
        return self._matter

    def render(self, *args, **kwargs):
        """Render the aeration's *matter*."""
        return self.aerate.render(self.matter, *args, **kwargs)

    def retrieve_matter(self):
        """Return the *matter* (the definition node) of the aeration."""
        raise NotImplementedError("must be implemented in a subclass")


class CompoundAeration(Aeration):
    @property
    def document(self) -> ElementTree:
        """Return the XML document from the definition file of the compound."""
        return self.aerate.load_document(f"{self.id}.xml")

    def retrieve_matter(self):
        result = self.document.xpath("//compounddef[@id=$id]", id=self.id)
        if not result:
            raise LookupError(f"No <compounddef> with id {self.id!r} in "
                              f"{self.id}.xml")
        elif len(result) > 1:
            raise LookupError(f"Multiple <compounddef>s with id {self.id!r} "
                              f"in {self.id}.xml")
        return result[0]


class MemberAeration(Aeration):
    @property
    def compound(self):
        """Return the compound aeration that this member is inside."""
        return self.aerate[self.node.getparent().attrib["refid"]]

    def retrieve_matter(self):
        result = self.compound.matter.xpath("//memberdef[@id=$id]", id=self.id)
        if not result:
            raise LookupError(f"No <memberdef> with id {self.id!r} in "
                              f"{self.compound.id}.xml")
        elif len(result) > 1:
            raise LookupError(f"Multiple <memberdef>s with id {self.id!r} in "
                              f"{self.compound.id}.xml")
        return result[0]
