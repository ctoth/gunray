"""Shared Hypothesis strategies and fixtures for gunray test suite."""

from __future__ import annotations

from hypothesis import strategies as st

from gunray.arguments import Argument
from gunray.schema import DefeasibleTheory, Rule
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


# ---- Ground-atom / strict-rule strategies for B1.3 disagreement tests ----
#
# Bias toward collisions: tiny predicate pool, tiny constant pool, optional
# strong-negation flip. These strategies should produce atoms that actually
# disagree often enough that `disagrees` sees non-trivial cases.

PREDICATE_POOL: tuple[str, ...] = ("p", "q", "r", "s", "flies", "bird")
CONSTANT_POOL: tuple[str, ...] = ("x", "y", "z")


@st.composite
def ground_atom_strategy(draw: st.DrawFn) -> GroundAtom:
    predicate = draw(st.sampled_from(PREDICATE_POOL))
    negated = draw(st.booleans())
    if negated:
        predicate = f"~{predicate}"
    # All atoms are unary over the constant pool; keeps strategies simple
    # and guarantees structural matches for strict-rule closure.
    argument = draw(st.sampled_from(CONSTANT_POOL))
    return GroundAtom(predicate=predicate, arguments=(argument,))


@st.composite
def strict_rule_strategy(draw: st.DrawFn) -> GroundDefeasibleRule:
    head = draw(ground_atom_strategy())
    body_size = draw(st.integers(min_value=0, max_value=2))
    body = tuple(draw(ground_atom_strategy()) for _ in range(body_size))
    rule_id = f"s_{draw(st.integers(min_value=0, max_value=99))}"
    return GroundDefeasibleRule(
        rule_id=rule_id,
        kind="strict",
        head=head,
        body=body,
    )


@st.composite
def strict_context_strategy(draw: st.DrawFn) -> tuple[GroundDefeasibleRule, ...]:
    size = draw(st.integers(min_value=0, max_value=4))
    rules = [draw(strict_rule_strategy()) for _ in range(size)]
    return tuple(rules)


# ---- Small defeasible theory strategy for build_arguments properties ----
#
# 3 predicates, 2 constants, up to 3 strict and up to 3 defeasible rules.
# Each theory keeps `2**|defeasible_rules| <= 8` so build_arguments stays
# fast under `max_examples=500`. Biased toward theories with at least a
# few facts so enumeration has something to derive.

_THEORY_PREDICATES: tuple[str, ...] = ("p", "q", "r")
_THEORY_CONSTANTS: tuple[str, ...] = ("a", "b")


def _atom_text(predicate: str, variable: str, negated: bool) -> str:
    marker = "~" if negated else ""
    return f"{marker}{predicate}({variable})"


@st.composite
def small_theory_strategy(draw: st.DrawFn) -> DefeasibleTheory:
    # Facts: a small set, each predicate optionally populated for each
    # constant. Guarantee at least one fact.
    facts: dict[str, list[tuple[str, ...]]] = {}
    for predicate in _THEORY_PREDICATES:
        for constant in _THEORY_CONSTANTS:
            if draw(st.booleans()):
                facts.setdefault(predicate, []).append((constant,))
    if not facts:
        facts[_THEORY_PREDICATES[0]] = [(_THEORY_CONSTANTS[0],)]

    strict_count = draw(st.integers(min_value=0, max_value=2))
    defeasible_count = draw(st.integers(min_value=0, max_value=3))

    def _gen_rule(prefix: str, index: int) -> Rule:
        head_predicate = draw(st.sampled_from(_THEORY_PREDICATES))
        head_negated = draw(st.booleans())
        body_predicate = draw(st.sampled_from(_THEORY_PREDICATES))
        body_negated = draw(st.booleans())
        return Rule(
            id=f"{prefix}{index}",
            head=_atom_text(head_predicate, "X", head_negated),
            body=[_atom_text(body_predicate, "X", body_negated)],
        )

    strict_rules = [_gen_rule("s", i) for i in range(strict_count)]
    defeasible_rules = [_gen_rule("d", i) for i in range(defeasible_count)]

    return DefeasibleTheory(
        facts={pred: set(rows) for pred, rows in facts.items()},
        strict_rules=strict_rules,
        defeasible_rules=defeasible_rules,
        defeaters=[],
        superiority=[],
        conflicts=[],
    )


@st.composite
def theory_with_root_argument_strategy(
    draw: st.DrawFn,
) -> tuple[DefeasibleTheory, Argument]:
    """Draw a ``(theory, root_argument)`` pair for B1.4 dialectical tests.

    Uses ``small_theory_strategy`` under the hood and filters out
    theories that produce zero arguments. The root is picked
    deterministically from ``build_arguments(theory)`` via a drawn
    index, which keeps shrinking simple.
    """
    from hypothesis import assume

    from gunray.arguments import build_arguments

    theory = draw(small_theory_strategy())
    args = list(build_arguments(theory))
    assume(len(args) > 0)
    index = draw(st.integers(min_value=0, max_value=len(args) - 1))
    return theory, args[index]
