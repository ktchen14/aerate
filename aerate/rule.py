class Rule:
    def __init__(self, action, tags=None, within=None, when=None, unless=None):
        self.action = action

        self.tags = tags
        self.within = within
        self.when = when
        self.unless = unless

    def __repr__(self):
        return f"<Rule {self.action.__name__} at {id(self):#x}>"

    @staticmethod
    def evaluate(test, node):
        """
        Evaluate ``test`` as a callable or XPath expression against ``node``.
        """
        return test(node) if callable(test) else node.xpath(test)

    def accept(self, node):
        """
        Return whether the rule is configured to handle ``node``.

        If ``tags`` is specified then the ``node``'s tag must be a member of
        ``tags``.

        If ``within`` is specified then it must be an iterable of strings. Each
        string must be either a single XML tag (such as ``"node"``) or a ``/``
        delimited sequence of XML tags (such as ``"foo/bar/baz"``). The rule
        will accept ``node`` if any string in ``within`` represents a
        *subsequence* of the tags in the ``node``'s ancestor chain. For example
        if the tags in the ``node``'s ancestor chain are::

            c -> b -> a

        Then the rule will accept the node if any of the strings ``"c"``,
        ``"b"``, ``"a"``, ``"c/b"``, ``"c/a"``, ``"b/a"``, or ``"c/b/a""`` are
        in the rule's ``within``.

        If ``when`` is specified then it must be a callable or an XPath
        expression. When evaluated against ``node`` the result must be
        ``True``. If specified ``unless`` is just like ``when`` except that
        when evaluated against ``node`` its result must be ``False``.

        If some combination of conditions are specified then the rule won't
        accept the ``node`` unless all of them accept the ``node``.
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

    def handle(self, *args, **kwargs):
        return self.action(*args, **kwargs)


class RuleEngine:
    def __init__(self):
        self.algorithm = []
        self.memory = {}

    def handle_node(self, cursor):
        iterator = self.memory.setdefault(cursor.node, iter(self.algorithm))
        for rule in iterator:
            if rule.accept(cursor.node):
                return rule.handle(self, cursor)
        return cursor.next()

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


class RenderEngine:
    def __init__(self):
        self.algorithm = []

    def handle(self, node, before=""):
        for rule in self.algorithm:
            if rule.accept(node):
                return rule.handle(self, node, before)
        return node.xpath("string()")

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
