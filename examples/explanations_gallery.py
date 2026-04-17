"""Explanations gallery: six canonical cases, answer + tree + prose.

For each case, prints the four-valued ``Answer`` verdict, the rendered
dialectical tree (Garcia & Simari 2004 Def 5.1), and the prose
``explain`` output (Garcia & Simari 2004 §6).

Theories are either constructed inline or lifted verbatim from peer
example files / ``tests/test_specificity.py``. Each case cites its
source.
"""

from __future__ import annotations

from gunray import (
    Answer,
    Argument,
    CompositePreference,
    DefeasibleTheory,
    DialecticalNode,
    GeneralizedSpecificity,
    PreferenceCriterion,
    Rule,
    SuperiorityPreference,
    answer,
    build_arguments,
    build_tree,
    explain,
    render_tree,
)
from gunray.types import GroundAtom


def _pick_root(
    theory: DefeasibleTheory,
    conclusion: GroundAtom,
) -> tuple[Argument, tuple[Argument, ...]]:
    """Pick an argument concluding ``conclusion`` as the tree root.

    Garcia & Simari 2004 Def 5.1: a dialectical tree is rooted at a
    specific argument for the query. We pick the first non-empty
    argument for the conclusion; if none exists, we fall back to the
    complement so the gallery still prints a tree.
    """

    arguments = tuple(build_arguments(theory))
    for arg in arguments:
        if arg.conclusion == conclusion and arg.rules:
            return arg, arguments
    complement = GroundAtom(
        predicate=(
            conclusion.predicate[1:]
            if conclusion.predicate.startswith("~")
            else "~" + conclusion.predicate
        ),
        arguments=conclusion.arguments,
    )
    for arg in arguments:
        if arg.conclusion == complement and arg.rules:
            return arg, arguments
    raise RuntimeError(f"no argument found for {conclusion!r} or its complement")


def _render_case(
    name: str,
    theory: DefeasibleTheory,
    query: GroundAtom,
    criterion: PreferenceCriterion,
) -> None:
    verdict = answer(theory, query, criterion)
    root, universe = _pick_root(theory, query)
    tree: DialecticalNode = build_tree(root, criterion, theory, universe=universe)

    print(f"=== {name} ===")
    print(f"query:  {query.predicate}({', '.join(str(a) for a in query.arguments)})")
    print(f"answer: {verdict.name}")
    print()
    print("Dialectical tree:")
    print(render_tree(tree))
    print()
    print("Prose explanation:")
    print(explain(tree, criterion))
    print()
    print("-" * 60)
    print()


# ---------------------------------------------------------------------------
# Case 1 — Opus / Penguin (tests/test_specificity.py:26-39)
# ---------------------------------------------------------------------------

_opus_theory = DefeasibleTheory(
    facts={"bird": {("opus",)}, "penguin": {("opus",)}},
    strict_rules=[Rule(id="s1", head="bird(X)", body=["penguin(X)"])],
    defeasible_rules=[
        Rule(id="r1", head="flies(X)", body=["bird(X)"]),
        Rule(id="r2", head="~flies(X)", body=["penguin(X)"]),
    ],
    defeaters=[],
    superiority=[],
    conflicts=[],
)
_opus_query = GroundAtom(predicate="flies", arguments=("opus",))
_opus_criterion: PreferenceCriterion = GeneralizedSpecificity(_opus_theory)

# Case 2 — Tweety (bird only, uncontested — tests/test_specificity.py:63-83)
_tweety_theory = DefeasibleTheory(
    facts={
        "bird": {("tweety",), ("opus",)},
        "penguin": {("opus",)},
    },
    strict_rules=[Rule(id="s1", head="bird(X)", body=["penguin(X)"])],
    defeasible_rules=[
        Rule(id="r1", head="flies(X)", body=["bird(X)"]),
        Rule(id="r2", head="~flies(X)", body=["penguin(X)"]),
    ],
    defeaters=[],
    superiority=[],
    conflicts=[],
)
_tweety_query = GroundAtom(predicate="flies", arguments=("tweety",))
_tweety_criterion: PreferenceCriterion = GeneralizedSpecificity(_tweety_theory)

# Case 3 — Nixon diamond (examples/nixon_diamond.py)
_nixon_theory = DefeasibleTheory(
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
_nixon_query = GroundAtom(predicate="pacifist", arguments=("nixon",))
_nixon_criterion: PreferenceCriterion = GeneralizedSpecificity(_nixon_theory)

# Case 4 — Royal African elephants (tests/test_specificity.py:86-109)
_elephant_theory = DefeasibleTheory(
    facts={"royal_elephant": {("clyde",)}},
    strict_rules=[
        Rule(id="s1", head="elephant(X)", body=["african_elephant(X)"]),
        Rule(id="s2", head="african_elephant(X)", body=["royal_elephant(X)"]),
    ],
    defeasible_rules=[
        Rule(id="d1", head="~gray(X)", body=["elephant(X)"]),
        Rule(id="d2", head="gray(X)", body=["african_elephant(X)"]),
    ],
    defeaters=[],
    superiority=[],
    conflicts=[],
)
_elephant_query = GroundAtom(predicate="gray", arguments=("clyde",))
_elephant_criterion: PreferenceCriterion = GeneralizedSpecificity(_elephant_theory)

# Case 5 — Innocent until proven guilty, scenario B
# (examples/innocent_until_proven_guilty.py scenario_b)
_innocent_theory = DefeasibleTheory(
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
_innocent_query = GroundAtom(predicate="innocent", arguments=())
_innocent_criterion: PreferenceCriterion = CompositePreference(
    SuperiorityPreference(_innocent_theory),
    GeneralizedSpecificity(_innocent_theory),
)

# Case 6 — Looks-red under red light, scenario B
# (examples/looks_red_under_red_light.py scenario B)
_red_theory = DefeasibleTheory(
    facts={
        "looks_red": {("apple",)},
        "illuminated_by_red_light": {("apple",)},
    },
    strict_rules=[],
    defeasible_rules=[
        Rule(id="d1", head="red(X)", body=["looks_red(X)"]),
    ],
    defeaters=[
        Rule(id="u1", head="~red(X)", body=["illuminated_by_red_light(X)"]),
    ],
    presumptions=[],
    superiority=[],
    conflicts=[],
)
_red_query = GroundAtom(predicate="red", arguments=("apple",))
_red_criterion: PreferenceCriterion = CompositePreference(
    SuperiorityPreference(_red_theory),
    GeneralizedSpecificity(_red_theory),
)


def main() -> None:
    print("Gunray explanations gallery")
    print("=" * 60)
    print()
    _render_case("Opus (penguin specificity)", _opus_theory, _opus_query, _opus_criterion)
    _render_case("Tweety (uncontested bird)", _tweety_theory, _tweety_query, _tweety_criterion)
    _render_case("Nixon diamond", _nixon_theory, _nixon_query, _nixon_criterion)
    _render_case(
        "Royal African elephants",
        _elephant_theory,
        _elephant_query,
        _elephant_criterion,
    )
    _render_case(
        "Innocent until proven guilty (coerced confession)",
        _innocent_theory,
        _innocent_query,
        _innocent_criterion,
    )
    _render_case(
        "Looks-red under red light (undercut)",
        _red_theory,
        _red_query,
        _red_criterion,
    )


# Sanity: expected verdicts per case.
assert answer(_opus_theory, _opus_query, _opus_criterion) is Answer.NO
assert answer(_tweety_theory, _tweety_query, _tweety_criterion) is Answer.YES
assert answer(_nixon_theory, _nixon_query, _nixon_criterion) is Answer.UNDECIDED
assert answer(_elephant_theory, _elephant_query, _elephant_criterion) is Answer.YES
assert answer(_innocent_theory, _innocent_query, _innocent_criterion) is Answer.NO
assert answer(_red_theory, _red_query, _red_criterion) is Answer.UNDECIDED


if __name__ == "__main__":
    main()
