"""Mermaid gallery: render five dialectical trees as GitHub-native diagrams.

Shows: Garcia & Simari 2004 Def 5.1 dialectical trees for five
visually-distinct cases, rendered through ``render_tree_mermaid`` (see
``src/gunray/dialectic.py:544``) and also written to
``examples/mermaid/<case>.mmd`` for embedding in docs.

The five cases are copied inline from the existing examples so this
script stays self-contained:

1. ``opus`` — platypus specificity (two-node tree). Source:
   ``examples/platypus.py``; Simari & Loui 1992 §5 p.29.
2. ``nixon_diamond`` — equi-specific siblings blocking one another,
   UNDECIDED. Source: ``examples/nixon_diamond.py``; Simari & Loui
   1992 §5 p.30.
3. ``clinical_aspirin`` — three-level medical specificity on
   post-infarct aspirin. Source: ``examples/clinical_drug_safety.py``;
   García & Simari 2004 §4.1 p.17.
4. ``innocent_coerced`` — presumption overridden by evidence with a
   coerced-confession defeater (scenario B). Source:
   ``examples/innocent_until_proven_guilty.py``; García & Simari 2004
   §6.2 p.32.
5. ``rbac_break_glass`` — three-level RBAC cascade resolved by
   specificity alone. Source: ``examples/access_control_break_glass.py``.

Output is deterministic: ``render_tree_mermaid`` assigns node ids
``n0, n1, ...`` via pre-order traversal with sorted children
(``dialectic.py:553``), so running twice produces byte-identical
files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from gunray import (
    Argument,
    CompositePreference,
    DefeasibleTheory,
    GeneralizedSpecificity,
    PreferenceCriterion,
    Rule,
    SuperiorityPreference,
    build_arguments,
    build_tree,
    render_tree_mermaid,
)
from gunray.types import GroundAtom


def _root_for(
    theory: DefeasibleTheory,
    atom: GroundAtom,
    criterion: PreferenceCriterion,
) -> str:
    """Find the argument concluding ``atom`` and render its tree.

    Garcia & Simari 2004 Def 5.1 — the dialectical tree is rooted at
    a specific argument. We iterate ``build_arguments(theory)`` and
    pick the argument whose conclusion matches ``atom`` and whose
    rule set is non-empty (skip strict/empty arguments when a
    defeasible one exists).
    """
    arguments = tuple(build_arguments(theory))
    matches: list[Argument] = [arg for arg in arguments if arg.conclusion == atom]
    if not matches:
        raise AssertionError(f"no argument concludes {atom!r}")

    # ``build_arguments`` does not guarantee a stable iteration order
    # across runs (it fans out over frozenset-valued caches). To keep
    # the rendered .mmd file byte-stable, sort matches by their rule
    # id tuple and pick the smallest — this is a purely cosmetic
    # tiebreak over arguments with the same conclusion, not a
    # semantic choice. Prefer a defeasible (non-empty) derivation so
    # the tree shows real counter-arguments instead of a strict stub.
    def _key(arg: Argument) -> tuple[str, ...]:
        return tuple(sorted(rule.rule_id for rule in arg.rules))

    defeasible = sorted((a for a in matches if a.rules), key=_key)
    strict = sorted((a for a in matches if not a.rules), key=_key)
    root = defeasible[0] if defeasible else strict[0]
    tree = build_tree(root, criterion, theory, universe=arguments)
    return render_tree_mermaid(tree)


# ---------------------------------------------------------------------------
# Case 1 — Opus/platypus specificity.
# ---------------------------------------------------------------------------


def _opus() -> tuple[DefeasibleTheory, GroundAtom, PreferenceCriterion]:
    theory = DefeasibleTheory(
        facts={"platypus": {("plato",)}},
        strict_rules=[Rule(id="s1", head="mammal(X)", body=["platypus(X)"])],
        defeasible_rules=[
            Rule(id="r1", head="~lays_eggs(X)", body=["mammal(X)"]),
            Rule(id="r2", head="lays_eggs(X)", body=["platypus(X)"]),
        ],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )
    atom = GroundAtom(predicate="lays_eggs", arguments=("plato",))
    return theory, atom, GeneralizedSpecificity(theory)


# ---------------------------------------------------------------------------
# Case 2 — Nixon diamond.
# ---------------------------------------------------------------------------


def _nixon() -> tuple[DefeasibleTheory, GroundAtom, PreferenceCriterion]:
    theory = DefeasibleTheory(
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
    atom = GroundAtom(predicate="pacifist", arguments=("nixon",))
    return theory, atom, GeneralizedSpecificity(theory)


# ---------------------------------------------------------------------------
# Case 3 — Clinical aspirin safety, Carol (cardiac-event patient).
# ---------------------------------------------------------------------------


def _clinical_aspirin() -> tuple[DefeasibleTheory, GroundAtom, PreferenceCriterion]:
    theory = DefeasibleTheory(
        facts={"cardiac_event_patient": {("carol",)}},
        strict_rules=[
            Rule(id="s1", head="warfarin_patient(X)", body=["cardiac_event_patient(X)"]),
            Rule(id="s2", head="patient(X)", body=["warfarin_patient(X)"]),
        ],
        defeasible_rules=[
            Rule(id="d1", head='safe("aspirin",X)', body=["patient(X)"]),
            Rule(id="d2", head='~safe("aspirin",X)', body=["warfarin_patient(X)"]),
            Rule(id="d3", head='safe("aspirin",X)', body=["cardiac_event_patient(X)"]),
        ],
        defeaters=[],
        presumptions=[],
        superiority=[],
        conflicts=[],
    )
    atom = GroundAtom(predicate="safe", arguments=("aspirin", "carol"))
    criterion = CompositePreference(
        SuperiorityPreference(theory),
        GeneralizedSpecificity(theory),
    )
    return theory, atom, criterion


# ---------------------------------------------------------------------------
# Case 4 — Innocent-until, scenario B (evidence + confession + coercion).
# ---------------------------------------------------------------------------


def _innocent_coerced() -> tuple[DefeasibleTheory, GroundAtom, PreferenceCriterion]:
    theory = DefeasibleTheory(
        facts={
            "evidence_against": {()},
            "confession": {()},
            "coerced_confession": {()},
        },
        strict_rules=[],
        defeasible_rules=[
            Rule(id="d1", head="~innocent", body=["evidence_against"]),
            Rule(id="d2", head="~innocent", body=["confession"]),
        ],
        defeaters=[
            Rule(id="df1", head="innocent", body=["coerced_confession"]),
        ],
        presumptions=[
            Rule(id="p1", head="innocent", body=[]),
        ],
        superiority=[("d1", "df1")],
        conflicts=[],
    )
    atom = GroundAtom(predicate="innocent", arguments=())
    criterion = CompositePreference(
        SuperiorityPreference(theory),
        GeneralizedSpecificity(theory),
    )
    return theory, atom, criterion


# ---------------------------------------------------------------------------
# Case 5 — RBAC break-glass, Carol (incident commander).
# ---------------------------------------------------------------------------


def _rbac_break_glass() -> tuple[DefeasibleTheory, GroundAtom, PreferenceCriterion]:
    theory = DefeasibleTheory(
        facts={"incident_commander": {("carol",)}},
        strict_rules=[
            Rule(id="s1", head="terminated(X)", body=["incident_commander(X)"]),
            Rule(id="s2", head="team_member(X)", body=["terminated(X)"]),
        ],
        defeasible_rules=[
            Rule(id="d1", head="access(X)", body=["team_member(X)"]),
            Rule(id="d2", head="~access(X)", body=["terminated(X)"]),
            Rule(id="d3", head="access(X)", body=["incident_commander(X)"]),
        ],
        defeaters=[],
        presumptions=[],
        superiority=[],
        conflicts=[],
    )
    atom = GroundAtom(predicate="access", arguments=("carol",))
    criterion = CompositePreference(
        SuperiorityPreference(theory),
        GeneralizedSpecificity(theory),
    )
    return theory, atom, criterion


# ---------------------------------------------------------------------------
# Driver.
# ---------------------------------------------------------------------------


Builder = Callable[[], tuple[DefeasibleTheory, GroundAtom, PreferenceCriterion]]

CASES: tuple[tuple[str, str, Builder], ...] = (
    ("opus", "Opus / platypus specificity — query lays_eggs(plato)", _opus),
    ("nixon_diamond", "Nixon diamond — query pacifist(nixon) (UNDECIDED)", _nixon),
    (
        "clinical_aspirin",
        "Clinical aspirin (three-level specificity) — query safe(aspirin,carol)",
        _clinical_aspirin,
    ),
    (
        "innocent_coerced",
        "Innocent-until scenario B (presumption + defeater) — query innocent",
        _innocent_coerced,
    ),
    (
        "rbac_break_glass",
        "RBAC break-glass cascade — query access(carol)",
        _rbac_break_glass,
    ),
)


def _output_dir() -> Path:
    # Write alongside this script so the .mmd files live with the .py
    # that produced them, per the E8 prompt.
    return Path(__file__).resolve().parent / "mermaid"


def main() -> None:
    out_dir = _output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    for slug, heading, build in CASES:
        theory, atom, criterion = build()
        mermaid = _root_for(theory, atom, criterion)
        print(f"## {heading}")
        print()
        print(mermaid)
        print()
        (out_dir / f"{slug}.mmd").write_text(mermaid + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
