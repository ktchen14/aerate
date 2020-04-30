from importlib.util import find_spec


class Rule:
    """A callable with criteria to decide if it should be called on a node."""

    def __init__(self, action, tags=None, within=None, when=None, unless=None):
        self.action = action

        self.tags = tags
        self.within = within
        self.when = when
        self.unless = unless

    def __repr__(self):
        return f"<Rule {self.name} at {id(self):#x}>"

    @property
    def name(self):
        """
        The action's name, when available, or the name of the action's type.
        """
        return getattr(self.action, "__name__", type(self.action).__name__)

    @staticmethod
    def evaluate(test, node):
        """
        Evaluate *test* as a callable or XPath expression against the *node*.
        """
        return test(node) if callable(test) else node.xpath(test)

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

        If some combination of these conditions are specified then the *node*
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

    def __call__(self, *args, **kwargs):
        return self.action(*args, **kwargs)


class Engine:
    def __init__(self):
        self.algorithm = []

    def load_recipe(recipe):
        exec(find_spec(recipe).loader.get_code(recipe), {"engine": self})

    def rule(self, *tags, before=None, within=None, **kwargs):
        """Define a rule on this engine."""

        function = None

        # Handle a call without an explicit argument list
        if len(tags) == 1 and callable(tags[0]) \
                and before is None \
                and within is None \
                and not kwargs:
            function, *tags = tags

        if within is not None:
            if isinstance(within, str):
                within = [within]
            within = frozenset(within)

        def decorator(function):
            rule = Rule(function, tags=tags, within=within, **kwargs)
            self.algorithm.append(rule)
            return function

        return decorator(function) if function else decorator


class Engine:
    def __init__(self):
        self.algorithm = []
        self.memory = {}

    def retrieve_rule(self, node):
        for rule in self.algorithm:
            if rule.accept(node):
                return rule

    def handle_node(self, cursor):
        rule = self.retrieve_rule(cursor.node)
        if rule is None:
            return cursor.next()
        return rule(cursor.node)

    def handle(self, root):
        from aerate.mutation import MutationCursor
        cursor = MutationCursor(root)
        while cursor and (root == cursor.node or root in cursor.node.iterancestors()):
            self.handle_node(cursor)

    def rule(self, *tags, before=None, within=None, **kwargs):
        """Define a rule on this engine."""

        function = None

        # Handle if this decorator is used without an explicit argument list
        if len(tags) == 1 and callable(tags[0]) \
                and before is None \
                and within is None \
                and not kwargs:
            function, *tags = tags

        if within is not None:
            if isinstance(within, str):
                within = [within]
            within = frozenset(within)

        def decorator(function):
            rule = Rule(function, tags=tags, within=within, **kwargs)
            self.algorithm.append(rule)
            return function

        return decorator(function) if function else decorator
