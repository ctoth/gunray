"""Garcia-answer section tests for ``DefeasibleEvaluator`` (B1.6).

These tests exercise the public ``DefeasibleModel.sections`` four-key
contract (``yes`` / ``no`` / ``undecided`` / ``unknown``) from Garcia
& Simari 2004 Def 5.3, p. 120.
"""

from __future__ import annotations

import gunray.defeasible as defeasible_module
from gunray import (
    ClosurePolicy,
    DefeasibleEvaluator,
    DefeasibleModel,
    DefeasibleTheory,
    DefeasibleTrace,
    GunrayEvaluator,
    MarkingPolicy,
    Rule,
    TraceConfig,
)


def _tweety_theory() -> DefeasibleTheory:
    """Scout 5.1 / README Tweety. ``bird(opus)`` is strict via ``s1``."""
    return DefeasibleTheory(
        facts={"bird": {("tweety",), ("opus",)}, "penguin": {("opus",)}},
        strict_rules=[Rule(id="s1", head="bird(X)", body=["penguin(X)"])],
        defeasible_rules=[
            Rule(id="r1", head="flies(X)", body=["bird(X)"]),
            Rule(id="r2", head="~flies(X)", body=["penguin(X)"]),
        ],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )


def _direct_nixon_theory() -> DefeasibleTheory:
    """Scout 5.2 direct Nixon — pacifist conflict under TrivialPreference."""
    return DefeasibleTheory(
        facts={"republican": {("nixon",)}, "quaker": {("nixon",)}},
        strict_rules=[],
        defeasible_rules=[
            Rule(id="r1", head="~pacifist(X)", body=["republican(X)"]),
            Rule(id="r2", head="pacifist(X)", body=["quaker(X)"]),
        ],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )


def _strict_only_theory() -> DefeasibleTheory:
    """Scout 5.6 strict-only fixture — exercises the strict-only shortcut."""
    return DefeasibleTheory(
        facts={"edge": {("a", "b"), ("b", "c")}},
        strict_rules=[
            Rule(id="r1", head="path(X, Y)", body=["edge(X, Y)"]),
            Rule(id="r2", head="path(X, Z)", body=["edge(X, Y)", "path(Y, Z)"]),
        ],
        defeasible_rules=[],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )


def _missing_body_theory() -> DefeasibleTheory:
    """Defeasible rule whose body literal has no argument anywhere.

    ``flies(X) :- bird(X), injured(X)``: ``bird(tweety)`` is a fact
    but ``injured(tweety)`` is neither a fact nor derivable. The
    grounded ``flies(tweety)`` argument therefore has no valid body
    activation, so no argument exists and the literal must NOT
    appear in the ``yes`` section.
    """
    return DefeasibleTheory(
        facts={"bird": {("tweety",)}},
        strict_rules=[],
        defeasible_rules=[
            Rule(id="r1", head="flies(X)", body=["bird(X)", "injured(X)"]),
        ],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )


def _strict_complement_theory() -> DefeasibleTheory:
    """Strict non-flight should force the opposite literal to NO."""

    return DefeasibleTheory(
        facts={"penguin": {("tweety",)}},
        strict_rules=[
            Rule(id="s1", head="bird(X)", body=["penguin(X)"]),
            Rule(id="s2", head="~flies(X)", body=["penguin(X)"]),
        ],
        defeasible_rules=[
            Rule(id="r1", head="flies(X)", body=["bird(X)"]),
        ],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )


def _default_negation_self_defeat_theory() -> DefeasibleTheory:
    """Garcia & Simari 2004 pp. 125-126: not L assumptions cannot derive L."""

    return DefeasibleTheory(
        facts={"bird": {("tweety",)}, "penguin": {("tweety",)}},
        strict_rules=[],
        defeasible_rules=[
            Rule(id="r1", head="flies(X)", body=["bird(X)", "not penguin(X)"]),
            Rule(id="r2", head="~flies(X)", body=["penguin(X)"]),
        ],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )


def _default_negation_attack_theory() -> DefeasibleTheory:
    """Garcia & Simari 2004 p. 126 Def 6.3: arguments attack not L assumptions."""

    return DefeasibleTheory(
        facts={"a": {()}, "b": {()}},
        strict_rules=[],
        defeasible_rules=[
            Rule(id="p_default", head="p", body=["a", "not q"]),
            Rule(id="q_counter", head="q", body=["b"]),
        ],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )


# ---------- Sections projection paper examples ----------------------------


def test_tweety_sections_projection() -> None:
    """Garcia 04 §5 Tweety / Simari 92 §5 Opus: warranted-answer
    projection under ``GeneralizedSpecificity``.

    - ``bird(tweety)``, ``bird(opus)``, ``penguin(opus)`` are all in
      the strict closure of ``Π``: ``bird(opus)`` follows from
      ``penguin(opus)`` via ``s1``. They are YES answers.
    - ``flies(tweety)`` has only the defeasible rule ``r1@tweety``
      and no counter-argument exists, so its tree marks ``U`` and it
      lands in ``yes``.
    - Under Block 2's ``GeneralizedSpecificity`` (Simari 92 Lemma 2.4),
      ``~flies(opus)`` is strictly more specific than ``flies(opus)``
      because ``penguin(opus)`` strict-closes to ``bird(opus)`` but
      not vice versa. The ``~flies(opus)`` argument properly defeats
      the ``flies(opus)`` argument, so ``~flies(opus)`` is YES and
      ``flies(opus)`` is NO.
    """
    evaluator = GunrayEvaluator()
    model = evaluator.evaluate(_tweety_theory(), marking_policy=MarkingPolicy.BLOCKING)

    assert set(model.sections) <= {"yes", "no", "undecided", "unknown"}
    assert ("tweety",) in model.sections["yes"]["bird"]
    assert ("opus",) in model.sections["yes"]["~flies"]
    assert ("opus",) in model.sections["no"]["flies"]

    assert model.sections["yes"]["bird"] == {("tweety",), ("opus",)}
    assert model.sections["yes"]["penguin"] == {("opus",)}
    assert ("tweety",) in model.sections["yes"]["flies"]

    # Block-2 Opus resolution: ~flies(opus) is warranted, flies(opus)
    # is not warranted.
    assert ("opus",) in model.sections["yes"]["~flies"]
    assert ("opus",) in model.sections["no"]["flies"]

    # Opus must NOT remain in undecided under GeneralizedSpecificity.
    undecided_flies = model.sections.get("undecided", {}).get("flies", set())
    assert ("opus",) not in undecided_flies


def test_nixon_sections_projection() -> None:
    """Scout 5.2 direct Nixon: ``pacifist(nixon)`` and
    ``~pacifist(nixon)`` are mutually blocking under
    ``TrivialPreference``. Garcia 04 Def 5.3 returns UNDECIDED for
    both literals; both must land in ``undecided``."""
    evaluator = GunrayEvaluator()
    model = evaluator.evaluate(_direct_nixon_theory(), marking_policy=MarkingPolicy.BLOCKING)

    assert "undecided" in model.sections
    assert ("nixon",) in model.sections["undecided"]["pacifist"]
    assert ("nixon",) in model.sections["undecided"]["~pacifist"]

    # Strict facts are YES answers.
    assert ("nixon",) in model.sections["yes"]["republican"]
    assert ("nixon",) in model.sections["yes"]["quaker"]


def test_strict_only_sections_projection() -> None:
    """Scout 5.6 strict-only path closure: every derived path is YES."""
    evaluator = GunrayEvaluator()
    model = evaluator.evaluate(_strict_only_theory(), marking_policy=MarkingPolicy.BLOCKING)

    expected_paths = {("a", "b"), ("b", "c"), ("a", "c")}
    assert model.sections["yes"]["path"] == expected_paths
    assert model.sections["no"] == {}
    assert model.sections["undecided"] == {}
    assert model.sections["unknown"] == {}


def test_missing_body_literal_is_not_yes() -> None:
    """Regression preserved from the deleted ``test_defeasible_core.py``.

    ``flies(X) :- bird(X), injured(X)`` with ``bird(tweety)`` but no
    ``injured(tweety)``: the defeasible rule has no valid body
    activation, so no argument for ``flies(tweety)`` exists. The
    literal must NOT appear in the ``yes`` section. Its
    predicate ``flies`` IS in the language, but the literal has no
    argument and no warranted complement, so it should also not
    appear in ``no`` or ``undecided`` (no argument for either side).
    """
    evaluator = DefeasibleEvaluator()
    model = evaluator.evaluate(_missing_body_theory(), marking_policy=MarkingPolicy.BLOCKING)

    flies_yes = model.sections.get("yes", {}).get("flies", set())
    assert ("tweety",) not in flies_yes

    # bird(tweety) is a fact and is a YES answer.
    assert ("tweety",) in model.sections["yes"]["bird"]


def test_strict_complement_projects_opposite_literal_to_no() -> None:
    """A strict complement should make the opposite literal NO."""

    evaluator = GunrayEvaluator()
    model = evaluator.evaluate(_strict_complement_theory(), marking_policy=MarkingPolicy.BLOCKING)

    assert ("tweety",) in model.sections["yes"]["~flies"]
    assert ("tweety",) in model.sections["no"]["flies"]


def test_default_negated_body_rejects_self_defeating_argument() -> None:
    """Garcia & Simari 2004 pp. 125-126 Def 6.2 condition 2."""

    model = GunrayEvaluator().evaluate(
        _default_negation_self_defeat_theory(),
        marking_policy=MarkingPolicy.BLOCKING,
    )

    assert ("tweety",) in model.sections["yes"]["~flies"]
    assert ("tweety",) in model.sections["no"]["flies"]


def test_argument_for_default_negated_literal_attacks_assumption() -> None:
    """Garcia & Simari 2004 p. 126 Def 6.3 default-negation attack point."""

    model = GunrayEvaluator().evaluate(
        _default_negation_attack_theory(),
        marking_policy=MarkingPolicy.BLOCKING,
    )

    assert () in model.sections["yes"]["q"]
    assert () in model.sections["undecided"]["p"]


def test_direct_defeasible_evaluator_routes_closure_policy_to_closure_evaluator(
    monkeypatch,
) -> None:
    """Closure policies belong to the closure evaluator, even on direct calls."""

    theory = DefeasibleTheory(defeasible_rules=(Rule(id="d1", head="b", body=("a",)),))
    calls: list[tuple[DefeasibleTheory, ClosurePolicy, TraceConfig | None]] = []

    class StubClosureEvaluator:
        def evaluate_with_trace(
            self,
            routed_theory: DefeasibleTheory,
            routed_policy: ClosurePolicy,
            trace_config: TraceConfig | None = None,
        ) -> tuple[DefeasibleModel, DefeasibleTrace]:
            calls.append((routed_theory, routed_policy, trace_config))
            return (
                DefeasibleModel(sections={"yes": {"sentinel": {()}}}),
                DefeasibleTrace(config=trace_config or TraceConfig()),
            )

    monkeypatch.setattr(
        defeasible_module,
        "ClosureEvaluator",
        StubClosureEvaluator,
        raising=False,
    )

    model = DefeasibleEvaluator().evaluate(
        theory,
        closure_policy=ClosurePolicy.RATIONAL_CLOSURE,
    )

    assert model.sections == {"yes": {"sentinel": {()}}}
    assert calls == [(theory, ClosurePolicy.RATIONAL_CLOSURE, None)]
