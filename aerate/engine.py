from importlib.util import find_spec

__all__ = ("Engine", "Rule")


class Engine:
    """
    A collection of :class:`Rule`\\s.

    In general an engine maintains a list of rules. When it's asked to handle a
    node an engine will search through this list in order until it finds a rule
    that accepts the node. It will then use this rule to handle the node,
    returning the result of the rule's action.
    """

    def __init__(self, aerate):
        self.aerate = aerate
        self.script = []

    def invoke(self, *args, **kwargs):
        """Invoke the engine to handle the *node*."""

        node = self.retrieve_node(*args, **kwargs)

        for rule in self.iterrule(node):
            result = rule(self, *args, **kwargs)
            if result is NotImplemented:
                continue
            return result
        return self.on_unaccepted(*args, **kwargs)

    def iterrule(self, node):
        """Return an iterator through each rule that will accept the *node*."""
        return (rule for rule in self.script if rule.accept(node))

    def on_unaccepted(self, *args, **kwargs):
        """Handle a *node* that isn't accepted by any rule in the engine."""
        pass

    def retrieve_node(self, node, *args, **kwargs):
        """
        Return the node from a call to :meth:`invoke` with this signature.
        """
        return node

    def load_recipe(self, recipe):
        """
        Load the *recipe* as a recipe file to initialize the engine's script.

        The recipe file is looked up with the same method that'd be used to
        import a module with name *recipe*. Note however that this file is
        loaded with ``exec()`` rather than ``import``. Inside this file the
        global variable *engine* is available to refer to the engine. A recipe
        file should resemble::

            @engine.rule("sample", when=lambda node: node.text)
            def return_text(self, node, *args, **kwargs):
                return node.text

            @engine.rule("sample", when=lambda node: len(node))
            def return_recursive(self, node, *args, **kwargs):
                return "".join(self.invoke(item) for item in node)
        """
        exec(find_spec(recipe).loader.get_code(recipe), {"engine": self})

    def rule(self, *tags, before=None, within=None, **kwargs):
        """
        A decorator to create and insert a rule into the engine.

        The arguments to this decorator are sent to the rule :meth:`initializer
        <Rule>` with some exceptions:

        - If no *tags* are specified then the rule's *tags* will be ``None``.
        - If *within* is a string then the rule's *within* will be a set
            with that value as its only element.

        Furthermore *before* is handled by this decorator to specify the
        placement of the rule in the engine. If *before* is:

        ``None`` or ``False``
            the rule will be appended to the engine

        ``True``, ``all``, or ``any``
            it will be prepended to the engine

        a :class:`Rule`
            it's inserted in the engine before the specified rule

        a callable
            then it's inserted in the engine before the first rule with that
            callable as its action

        a string
            then it's inserted int the engine before the first rule with that
            :meth:`name <Rule.name>`
        """

        action = None

        # Handle a call without an explicit argument list
        if len(tags) == 1 and callable(tags[0]) \
                and before is None \
                and within is None \
                and not kwargs:
            action, *tags = tags

        tags = frozenset(tags) if tags else None

        if before is None or before is False:
            i = len(self.script)
        elif before is True or before in (all, any):
            i = 0
        elif isinstance(before, Rule):
            i = self.script.index(before)
        elif callable(before):
            i = [rule.action for rule in self.script].index(before)
        elif isinstance(before, str):
            i = [rule.name for rule in self.script].index(before)
        else:
            raise TypeError("unexpected type in rule() argument 'before': " +
                            repr(type(before).__name__))

        if within is not None:
            if isinstance(within, str):
                within = [within]
            within = frozenset(within)

        def decorator(action):
            rule = Rule(action, tags=tags, within=within, **kwargs)
            self.script.insert(i, rule)
            return action

        return decorator(action) if action else decorator


class Rule:
    """An action with criteria to decide if it should be called on a node."""

    @staticmethod
    def evaluate(test, node):
        """
        Evaluate *test* as a callable or XPath expression against the *node*.
        """
        return test(node) if callable(test) else node.xpath(test)

    def __init__(self, action, tags=None, within=None, when=None, unless=None):
        self.action = action

        self.tags = tags
        self.within = within
        self.when = when
        self.unless = unless

    def __repr__(self):
        return f"<Rule {self.name} at {id(self):#x}>"

    def __call__(self, *args, **kwargs):
        return self.action(*args, **kwargs)

    @property
    def name(self):
        """
        The action's name, when available, or the name of the action's type.
        """
        return getattr(self.action, "__name__", type(self.action).__name__)

    def accept(self, node):
        """
        Return whether the rule should be called on the *node*.

        If *tags* is specified then it should be a string container. The *node*
        is accepted if its tag is a member of *tags*.

        If *within* is specified then it must be a string iterable. Each string
        must be either a single XML tag (such as ``"node"``) or a ``/``
        delimited sequence of XML tags (such as ``"foo/bar/baz"``). The *node*
        is accepted if any string in *within* represents a **subsequence** of
        the tags in the *node*'s ancestor chain. For example if the tags in the
        *node*'s ancestor chain are::

            c -> b -> a

        Then the *node* is accepted if any of the strings ``"c"``, ``"b"``,
        ``"a"``, ``"c/b"``, ``"c/a"``, ``"b/a"``, or ``"c/b/a""`` are in the
        rule's *within*.

        If *when* is specified then it must be a callable or an XPath
        expression. As a callable it will be called with the *node* as its only
        (positional) argument; as an XPath expression it will be evaluated with
        the *node* as the context node. The *node* is accepted if the result of
        either is ``True`` (or evaluates to ``True``).

        If specified *unless* is like *when* except that its result must be
        ``False`` (or evaluate to ``False``) for the *node* to be accepted.

        If some combination of these criteria are specified then the *node*
        isn't accepted unless all of them accept the *node*.
        """

        if self.tags is not None and node.tag not in self.tags:
            return False

        if self.within is not None:
            for within in self.within:
                ancestor_iter = node.iterancestors()
                for name in within.split("/"):
                    if not any(node.tag == name for node in ancestor_iter):
                        break
                else: break
            else: return False

        if self.when is not None and not self.evaluate(self.when, node):
            return False

        if self.unless is not None and self.evaluate(self.unless, node):
            return False

        return True


class Renderer(Engine):
    """An engine that renders an unaccepted node as its text."""

    def on_unaccepted(self, node, *args, **kwargs):
        return node.xpath("string()")
