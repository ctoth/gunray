from __future__ import annotations

from pathlib import Path

from gunray import ClosurePolicy, DefeasibleTheory, GunrayEvaluator, MarkingPolicy, Rule
from gunray.arguments import build_arguments
from gunray.dialectic import build_tree, classify_defeat
from gunray.preference import GeneralizedSpecificity
from gunray.types import GroundAtom


def test_workstream_o_gun_garcia_done() -> None:
    """Sentinel for the Garcia 2004 rewrite workstream."""

    theory = DefeasibleTheory(
        facts={"bird": {("tweety",)}, "penguin": {("tweety",)}},
        strict_rules=[Rule(id="s1", head="bird(X)", body=("penguin(X)",))],
        defeasible_rules=(
            Rule(id="r1", head="flies(X)", body=("bird(X)",)),
            Rule(id="r2", head="~flies(X)", body=("penguin(X)",)),
        ),
        superiority=(),
    )

    model, trace = GunrayEvaluator().evaluate_with_trace(
        theory,
        marking_policy=MarkingPolicy.BLOCKING,
    )

    assert set(model.sections) == {"yes", "no", "undecided", "unknown"}
    assert not {"definitely", "defeasibly", "not_defeasibly"} & set(model.sections)
    assert ("tweety",) in model.sections["yes"]["~flies"]
    assert ("tweety",) in model.sections["no"]["flies"]
    assert trace.arguments
    assert trace.markings

    default_negation_model = GunrayEvaluator().evaluate(
        DefeasibleTheory(
            facts={"a": {()}, "b": {()}},
            defeasible_rules=(
                Rule(id="p_default", head="p", body=("a", "not q")),
                Rule(id="q_counter", head="q", body=("b",)),
            ),
        ),
        marking_policy=MarkingPolicy.BLOCKING,
    )
    assert () in default_negation_model.sections["yes"]["q"]
    assert () in default_negation_model.sections["undecided"]["p"]


def test_garcia_defeat_kind_is_publicly_observable() -> None:
    theory = DefeasibleTheory(
        facts={"bird": {("opus",)}, "penguin": {("opus",)}},
        strict_rules=[Rule(id="s1", head="bird(X)", body=("penguin(X)",))],
        defeasible_rules=(
            Rule(id="r1", head="flies(X)", body=("bird(X)",)),
            Rule(id="r2", head="~flies(X)", body=("penguin(X)",)),
        ),
    )
    arguments = {argument.conclusion: argument for argument in build_arguments(theory)}
    flies = arguments[GroundAtom("flies", ("opus",))]
    not_flies = arguments[GroundAtom("~flies", ("opus",))]
    preference = GeneralizedSpecificity(theory)

    assert classify_defeat(not_flies, flies, preference, theory) == "proper"
    tree = build_tree(flies, preference, theory)
    assert tree.children[0].defeater_kind == "proper"


def test_policy_split_surface_has_no_mixed_policy_enum() -> None:
    import gunray

    assert not hasattr(gunray, "Policy")
    assert MarkingPolicy.BLOCKING.value == "blocking"
    assert ClosurePolicy.RATIONAL_CLOSURE.value == "rational_closure"


def test_garcia_docs_record_section_supersession() -> None:
    root = Path(__file__).resolve().parents[1]
    architecture = (root / "ARCHITECTURE.md").read_text(encoding="utf-8")
    citations = (root / "CITATIONS.md").read_text(encoding="utf-8")
    note = (root / "notes" / "b2_defeater_participation.md").read_text(encoding="utf-8")

    assert "`yes` / `no` / `undecided` / `unknown`" in architecture
    assert "not model fields" in architecture
    assert "Hypothesis comparison" in citations
    assert "WS-O-gun-garcia supersession" in note
