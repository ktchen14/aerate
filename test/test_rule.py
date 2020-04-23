import pytest
from aerate.rule import RuleEngine


def SampleCursor(document: str, on: str=None):
    """Return a mutation cursor on ``document`` at a node."""

    parser = etree.XMLParser(remove_blank_text=True)
    cursor = MutationCursor(etree.fromstring(document, parser))
    if on is not None:
        while cursor.node.tag != on:
            cursor.next()
    else:
        node = cursor.root.find(".//cursor")
        if node is not None:
            cursor.move_to(node)
    return cursor


@pytest.fixture
def engine():
    return RuleEngine()


def test_rule_engine_rule_none(engine):
    @engine.rule
    def rule(cursor):
        pass

    assert rule.tags == frozenset()


def test_rule_engine_rule_tags(engine):
    @engine.rule("a", "b")
    def rule(cursor):
        pass

    assert rule.tags == {"a", "b"}


def test_rule_engine_rule_when(engine):
    when = lambda node: True

    @engine.rule(when=when)
    def rule(cursor):
        pass

    assert rule.when == when


# def test_rule_engine(engine):
