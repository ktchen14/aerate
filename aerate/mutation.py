from __future__ import annotations


class MutationCursor:
    def __init__(self, root):
        self._root = root
        self.node = root

    def __bool__(self):
        return self.node is not None

    @property
    def root(self):
        """Return the root node of the cursor that it can't escape."""
        return self._root

    def move_to(self, node) -> MutationCursor:
        """Move the cursor to the ``node``."""
        self.node = node
        return self

    def next(self) -> MutationCursor:
        """Move the cursor to the next node in sequence."""

        try:
            return self.move_to(self.node[0])
        except IndexError:
            return self.skip()

    def rewind(self) -> MutationCursor:
        if self.node.getprevious() is not None:
            return self.move_to(self.node.getprevious())
        return self.move_to(self.node.getparent())

    def skip(self) -> MutationCursor:
        """Skip the cursor's node."""

        if self.node.getnext() is not None:
            return self.move_to(self.node.getnext())

        for ancestor in self.node.iterancestors():
            if ancestor.getnext() is not None:
                return self.move_to(ancestor.getnext())

        self.node = None
        return self

    def adjoin(self, node=None):
        """
        Join the node to its previous sibling node.
        """

        node = node if node is not None else self.node

        to = node.getprevious()

        if node.text:
            if len(to):
                if to[-1].tail is not None:
                    to[-1].tail = f"{to[-1].tail}{node.text}"
                else:
                    to[-1].tail = node.text
            else:
                if to.text is not None:
                    to.text = f"{to.text}{node.text}"
                else:
                    to.text = node.text

        if node.tail:
            if to.tail is not None:
                to.tail = f"{to.tail}{node.tail}"
            else:
                to.tail = node.tail

        to.extend(node.iterchildren())

        if node == self.node or node in set(self.node.iterancestors()):
            self.next()
        node.getparent().remove(node)
        return self

    def divide(self, node=None):
        """
        Divide the parent of ``node`` at ``node``.

        The ``node``'s parent is duplicated and added to the tree immediately
        following the original. Then ``node`` and its following siblings are
        reparented into this duplicate. The parent node is always kept intact,
        even if it has no text and ``node`` is its first child.

        If ``node`` is ``None`` then the cursor's node will be used. In either
        case this operation doesn't move the cursor.

        For example if ``node`` is ``<target>`` in this tree:

        .. code-block:: xml

           <parent>
               prefix
               <target>text</target>
               suffix
           </parent>

        Then when ``<target>`` is divided this will become:

        .. code-block:: xml

           <parent>
               prefix
           </parent>
           <parent>
               <target>text</target>
               suffix
           </parent>

        This doesn't work on the root node or a direct child of the root node.
        """

        node = node if node is not None else self.node

        parent = node.getparent()
        continuation = node.makeelement(node.getparent().tag,
                                        node.getparent().attrib,
                                        node.getparent().nsmap)

        continuation.extend([node] + list(node.itersiblings()))
        parent.addnext(continuation)

        return self

    def divide_tail(self, node=None):
        """
        Divide the parent of ``node`` on the ``node``'s tail text.

        .. code-block:: xml

           <parent>
               prefix
               <target>text</target>
               tail
               <sample/>
               suffix
           </parent>

        Then when ``<target>`` is divided on its tail text this will become:

        .. code-block:: xml

           <parent>
               prefix
               <target>text</target>
           </parent>
           <parent>
               tail
               <sample/>
               suffix
           </parent>

        This doesn't work on the root node or a direct child of the root node.
        """

        node = node if node is not None else self.node

        parent = node.getparent()
        continuation = node.makeelement(node.getparent().tag,
                                        node.getparent().attrib,
                                        node.getparent().nsmap)
        continuation.text = node.tail
        node.tail = None
        continuation.extend(node.itersiblings())
        parent.addnext(continuation)

        return self

    def lift(self, node=None):
        """
        Lift ``node`` to become a sibling of its parent.

        If ``node`` has tail text or siblings following it, then its parent is
        duplicated and this duplicate is added to the tree immediately
        following the lifted ``node``. This duplicate is used as the parent of
        the tail text and the ``node``'s following siblings. The parent node is
        always kept intact, even if it has no text and ``node`` is its first
        child.

        If ``node`` is ``None`` then the cursor's node will be used. In either
        case this operation doesn't move the cursor.

        For example if ``node`` is ``<target>`` in this tree:

        .. code-block:: xml

           <parent>
               prefix
               <target>text</target>
               suffix
           </parent>

        Then when ``<target>`` is lifted this will become:

        .. code-block:: xml

           <parent>
               prefix
           </parent>
           <target>text</target>
           <parent>
               suffix
           </parent>

        This doesn't work on the root node or a direct child of the root node.
        """

        node = node if node is not None else self.node

        parent = node.getparent()

        if node.tail or len(node.itersiblings()):
            continuation = node.makeelement(parent.tag,
                                            parent.attrib,
                                            parent.nsmap)
            continuation.text = node.tail
            node.tail = None
            continuation.extend(list(node.itersiblings()))

        parent.addnext(node)

        if continuation is not None:
            parent.addnext(continuation)

        return self

    def remove(self, node=None):
        """
        Remove ``node`` from the document.

        If ``node`` has tail text then that text is reparented to a different
        node as appropriate.

        If ``node`` is ``None`` then the cursor's node will be used. In this
        case, or if ``node`` is an ancestor of the cursor's node, then the
        cursor is advanced before the node is removed. Otherwise this operation
        doesn't move the cursor.

        For example if ``node`` is ``None`` and the cursor is on ``<target>``
        in this tree:

        .. code-block:: xml

           <parent>
               prefix
               <one />
               <target>text</target>
               <two />
               suffix
           </parent>

        Then when ``<target>`` is removed this will become:

        .. code-block:: xml

           <parent>
               prefix
               <one />
               <two />
               suffix
           </parent>

        With the cursor on ``<two>``. Note that all descendants of the node to
        be removed are also removed.

        This doesn't work on the root node.
        """

        node = node if node is not None else self.node

        if node == self.node or node in set(self.node.iterancestors()):
            self.next()

        if node.tail:
            if node.getprevious() is not None:
                node.getprevious().tail = f"{node.getprevious().tail}{node.tail}"
            else:
                node.getparent().text = f"{node.getparent().text}{node.tail}"
        node.getparent().remove(node)

        return self
