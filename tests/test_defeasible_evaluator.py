"""Sections-projection unit tests for ``DefeasibleEvaluator`` (B1.6).

These tests exercise the public ``DefeasibleModel.sections`` four-key
contract (``definitely`` / ``defeasibly`` / ``not_defeasibly`` /
``undecided``) that propstore and the conformance suite consume. They
assert the section projection rules from Garcia & Simari 2004 §5
applied to the paper-pipeline output:

- ``definitely`` iff some ``⟨frozenset(), h⟩`` argument exists.
- ``defeasibly`` iff some ``⟨A, h⟩`` argument's tree marks ``U``,
  OR ``definitely``.
- ``not_defeasibly`` iff some ``⟨A, complement(h)⟩`` argument's tree
  marks ``U`` AND NOT ``definitely``.
- ``undecided`` iff arguments exist for ``h`` or ``complement(h)``
  but neither is warranted.

Atoms whose predicate is not in the theory's language at all
(``Answer.UNKNOWN``) are omitted from every section.
"""

from __future__ import annotations

from gunray import (
    DefeasibleEvaluator,
    DefeasibleModel,
    DefeasibleTrace,
    DefeasibleTheory,
    GunrayEvaluator,
    Policy,
    Rule,
    TraceConfig,
)
import gunray.defeasible as defeasible_module


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
    appear in the ``defeasibly`` section.
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


# ---------- Sections projection paper examples ----------------------------


def test_tweety_sections_projection() -> None:
    """Garcia 04 §5 Tweety / Simari 92 §5 Opus: strict+defeasible
    projection under ``GeneralizedSpecificity``.

    - ``bird(tweety)``, ``bird(opus)``, ``penguin(opus)`` are all in
      the strict closure of ``Π``: ``bird(opus)`` follows from
      ``penguin(opus)`` via ``s1``. They land in ``definitely`` and
      (because every strict derivation is also a defeasible
      derivation per the prompt's rules) also in ``defeasibly``.
    - ``flies(tweety)`` has only the defeasible rule ``r1@tweety``
      and no counter-argument exists, so its tree marks ``U`` and it
      lands in ``defeasibly``.
    - Under Block 2's ``GeneralizedSpecificity`` (Simari 92 Lemma 2.4),
      ``~flies(opus)`` is strictly more specific than ``flies(opus)``
      because ``penguin(opus)`` strict-closes to ``bird(opus)`` but
      not vice versa. The ``~flies(opus)`` argument properly defeats
      the ``flies(opus)`` argument, so ``~flies(opus)`` is warranted
      and ``flies(opus)`` lands in ``not_defeasibly``.
    """
    evaluator = GunrayEvaluator()
    model = evaluator.evaluate(_tweety_theory(), Policy.BLOCKING)

    assert model.sections["definitely"]["bird"] == {("tweety",), ("opus",)}
    assert model.sections["definitely"]["penguin"] == {("opus",)}

    assert model.sections["defeasibly"]["bird"] == {("tweety",), ("opus",)}
    assert model.sections["defeasibly"]["penguin"] == {("opus",)}
    assert ("tweety",) in model.sections["defeasibly"]["flies"]

    # Block-2 Opus resolution: ~flies(opus) is warranted, flies(opus)
    # is not warranted.
    assert ("opus",) in model.sections["defeasibly"]["~flies"]
    assert ("opus",) in model.sections["not_defeasibly"]["flies"]

    # Opus must NOT remain in undecided under GeneralizedSpecificity.
    undecided_flies = model.sections.get("undecided", {}).get("flies", set())
    assert ("opus",) not in undecided_flies


def test_nixon_sections_projection() -> None:
    """Scout 5.2 direct Nixon: ``pacifist(nixon)`` and
    ``~pacifist(nixon)`` are mutually blocking under
    ``TrivialPreference``. Garcia 04 Def 5.3 returns UNDECIDED for
    both literals; both must land in ``undecided``."""
    evaluator = GunrayEvaluator()
    model = evaluator.evaluate(_direct_nixon_theory(), Policy.BLOCKING)

    assert "undecided" in model.sections
    assert ("nixon",) in model.sections["undecided"]["pacifist"]
    assert ("nixon",) in model.sections["undecided"]["~pacifist"]

    # Strict facts still land in definitely.
    assert ("nixon",) in model.sections["definitely"]["republican"]
    assert ("nixon",) in model.sections["definitely"]["quaker"]


def test_strict_only_sections_projection() -> None:
    """Scout 5.6 strict-only path closure: every derived path lands
    in ``definitely`` (and ``defeasibly``). The strict-only shortcut
    must continue to route through ``SemiNaiveEvaluator``."""
    evaluator = GunrayEvaluator()
    model = evaluator.evaluate(_strict_only_theory(), Policy.BLOCKING)

    expected_paths = {("a", "b"), ("b", "c"), ("a", "c")}
    assert model.sections["definitely"]["path"] == expected_paths
    assert model.sections["defeasibly"]["path"] == expected_paths


def test_missing_body_literal_is_not_defeasibly() -> None:
    """Regression preserved from the deleted ``test_defeasible_core.py``.

    ``flies(X) :- bird(X), injured(X)`` with ``bird(tweety)`` but no
    ``injured(tweety)``: the defeasible rule has no valid body
    activation, so no argument for ``flies(tweety)`` exists. The
    literal must NOT appear in the ``defeasibly`` section. Its
    predicate ``flies`` IS in the language, but the literal has no
    argument and no warranted complement, so it should also not
    appear in ``not_defeasibly`` or ``undecided`` (no argument for
    either side).
    """
    evaluator = DefeasibleEvaluator()
    model = evaluator.evaluate(_missing_body_theory(), Policy.BLOCKING)

    flies_defeasibly = model.sections.get("defeasibly", {}).get("flies", set())
    assert ("tweety",) not in flies_defeasibly

    # bird(tweety) is a fact and lands in definitely + defeasibly.
    assert ("tweety",) in model.sections["definitely"]["bird"]
    assert ("tweety",) in model.sections["defeasibly"]["bird"]


def test_strict_complement_projects_opposite_literal_to_not_defeasibly() -> None:
    """A strict complement should make the opposite literal NO."""

    evaluator = GunrayEvaluator()
    model = evaluator.evaluate(_strict_complement_theory(), Policy.BLOCKING)

    assert ("tweety",) in model.sections["definitely"]["~flies"]
    assert ("tweety",) in model.sections["not_defeasibly"]["flies"]


def test_direct_defeasible_evaluator_routes_closure_policy_to_closure_evaluator(
    monkeypatch,
) -> None:
    """Closure policies belong to the closure evaluator, even on direct calls."""

    theory = DefeasibleTheory(defeasible_rules=(Rule(id="d1", head="b", body=("a",)),))
    calls: list[tuple[DefeasibleTheory, Policy, TraceConfig | None]] = []

    class StubClosureEvaluator:
        def evaluate_with_trace(
            self,
            routed_theory: DefeasibleTheory,
            routed_policy: Policy,
            trace_config: TraceConfig | None = None,
        ) -> tuple[DefeasibleModel, DefeasibleTrace]:
            calls.append((routed_theory, routed_policy, trace_config))
            return (
                DefeasibleModel(sections={"defeasibly": {"sentinel": {()}}}),
                DefeasibleTrace(config=trace_config or TraceConfig()),
            )

    monkeypatch.setattr(
        defeasible_module,
        "ClosureEvaluator",
        StubClosureEvaluator,
        raising=False,
    )

    model = DefeasibleEvaluator().evaluate(theory, Policy.RATIONAL_CLOSURE)

    assert model.sections == {"defeasibly": {"sentinel": {()}}}
    assert calls == [(theory, Policy.RATIONAL_CLOSURE, None)]
