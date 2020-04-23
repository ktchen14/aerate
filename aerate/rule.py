class RuleEngine:
    def __init__(self):
        self.algorithm = []

    def dispatch_rule(self, rule, cursor):
        """
        Call ``rule`` on ``cursor`` if the ``cursor``'s node is matched by ``rule``.

        If ``rule`` doesn't match the ``cursor``'s node then returns ``None``.
        """

        if rule.tags and cursor.node.tag not in rule.tags:
            return None

        if rule.inside:
            tags = frozenset(node.tag for node in cursor.node.iterancestors())
            if not tags & rule.inside:
                return None

        if rule.when is not None:
            if callable(rule.when):
                result = rule.when(cursor.node)
            else:
                result = cursor.node.xpath(rule.when)

            if not result:
                return None

        if rule.unless is not None:
            if callable(rule.unless):
                result = rule.unless(cursor.node)
            else:
                result = cursor.node.xpath(rule.unless)

            if result:
                return None

        return rule(self, cursor)

    def handle(self, cursor):
        while cursor:
            rule = next(rule for rule in reversed(self.algorithm), None)
            self.dispatch_rule(rule, cursor)

    def rule(self, *tags, inside=frozenset(), when=None, unless=None):
        """Define a rule on this engine."""

        if isinstance(inside, str):
            inside = [inside]
        inside = frozenset(inside)

        if len(tags) == 1 and callable(tags[0]) and not inside and when is None and unless is None:
            function, *tags = tags
        else:
            function = None

        def decorator(function):
            function.tags = frozenset(tags)
            function.inside = inside
            function.when = when
            function.unless = unless
            self.algorithm.append(function)
            return function

        return decorator(function) if function else decorator
