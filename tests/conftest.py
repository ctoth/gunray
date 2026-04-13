"""Shared Hypothesis strategies and fixtures for gunray test suite."""

from __future__ import annotations

from hypothesis import strategies as st

from gunray.arguments import Argument
from gunray.types import GroundAtom, GroundDefeasibleRule


def make_ground_atom(predicate: str, *args: str | int) -> GroundAtom:
    return GroundAtom(predicate=predicate, arguments=tuple(args))


def make_ground_defeasible_rule(rule_id: str, head_predicate: str) -> GroundDefeasibleRule:
    return GroundDefeasibleRule(
        rule_id=rule_id,
        kind="defeasible",
        head=make_ground_atom(head_predicate, "x"),
        body=(),
    )


RULE_POOL: tuple[GroundDefeasibleRule, ...] = (
    make_ground_defeasible_rule("r1", "p"),
    make_ground_defeasible_rule("r2", "q"),
    make_ground_defeasible_rule("r3", "s"),
    make_ground_defeasible_rule("r4", "t"),
)

CONCLUSION: GroundAtom = make_ground_atom("h", "x")


@st.composite
def arguments_strategy(draw: st.DrawFn) -> Argument:
    """Hypothesis strategy building an ``Argument`` from a fixed pool of rules."""

    indices = draw(
        st.sets(
            st.integers(min_value=0, max_value=len(RULE_POOL) - 1),
            max_size=len(RULE_POOL),
        )
    )
    rules = frozenset(RULE_POOL[i] for i in indices)
    return Argument(rules=rules, conclusion=CONCLUSION)
