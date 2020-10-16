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
        return {
            "compound": CompoundAeration, "member": MemberAeration,
        }[node.tag](aerate, node)

    def __init__(self, aerate, node):
        self.aerate = aerate

        self._node = node
        self._matter = None

    @property
    def name(self) -> str:
        """Return the name of the aeration."""
        return self.node.find("name").text

    @property
    def id(self) -> str:
        """Return the "refid" of the aeration."""
        return self.node.attrib["refid"]

    @property
    def kind(self) -> str:
        """Return the "kind" of the aeration."""
        return self.node.attrib["kind"]

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
        """Return the *matter* of the aeration."""
        raise NotImplementedError


class CompoundAeration(Aeration):
    @property
    def document(self) -> ElementTree:
        """Return the XML document from the definition file of the compound."""
        return self.aerate.load_document(self.id + ".xml")

    def retrieve_matter(self):
        """Return the *matter* of the aeration."""

        result = self.document.xpath(r'//compounddef[@id=$id]', id=self.id)
        if len(result) > 1:
            raise LookupError(f"Multiple <compounddef>s with id {self.id!r} in {self.id}.xml")
        elif not result:
            raise LookupError(f"No <compounddef> with id {self.id!r} in {self.id}.xml")
        return result[0]


class MemberAeration(Aeration):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._compound = None

    @property
    def compound(self):
        """Return the compound that this member is inside as an aeration."""
        if self._compound is None:
            self._compound = self.aerate.find_by_id(self.node.getparent().attrib["refid"])
        return self._compound

    def retrieve_matter(self):
        """Return the *matter* of the aeration."""

        result = self.compound.matter.xpath(r'//memberdef[@id=$id]', id=self.id)
        if len(result) > 1:
            raise LookupError(f"Multiple <memberdef>s with id {self.id!r} in {self.compound.id}.xml")
        if not result:
            raise LookupError(f"No <memberdef> with id {self.id!r} in {self.compound.id}.xml")
        return result[0]
