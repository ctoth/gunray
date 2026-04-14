"""Tests for ``gunray.dialectic.render_tree`` — Unicode tree renderer.

``render_tree`` is a pure deterministic Unicode debugger for
``DialecticalNode``; it is not a paper definition but a deliberate
engineering promotion per the B1.5 dispatch brief. Every node shows
its argument's conclusion, rule ids (sorted), and its ``mark`` per
Garcia & Simari 2004 Procedure 5.1.
"""

from __future__ import annotations

from gunray.arguments import Argument, build_arguments
from gunray.dialectic import DialecticalNode, build_tree, render_tree
from gunray.preference import TrivialPreference
from gunray.schema import DefeasibleTheory, Rule
from gunray.types import GroundAtom


def _ga(predicate: str, *args: str) -> GroundAtom:
    return GroundAtom(predicate=predicate, arguments=tuple(args))


def _tweety_theory() -> DefeasibleTheory:
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


def _find_argument(theory: DefeasibleTheory, conclusion: GroundAtom) -> Argument:
    for arg in build_arguments(theory):
        if arg.conclusion == conclusion:
            return arg
    raise LookupError(f"no argument for {conclusion}")


def test_render_leaf_node() -> None:
    """A childless ``DialecticalNode`` renders to a single line containing
    the conclusion, the sorted rule-id list, and the ``(U)`` marker per
    Garcia & Simari 2004 Procedure 5.1 (leaves mark ``U``)."""
    theory = _tweety_theory()
    flies_tweety = _find_argument(theory, _ga("flies", "tweety"))
    tree = build_tree(flies_tweety, TrivialPreference(), theory)
    assert tree.children == ()
    rendered = render_tree(tree)
    lines = rendered.splitlines()
    assert len(lines) == 1
    assert "flies(tweety)" in lines[0]
    assert "r1" in lines[0]
    assert "(U)" in lines[0]


def test_render_tweety_opus_tree_snapshot() -> None:
    """Snapshot of the dialectical tree rooted at ``⟨{r1@opus}, flies(opus)⟩``.

    Scout Section 5.1 Tweety theory: opus is a penguin, so
    ``~flies(opus)`` is a blocking defeater of ``flies(opus)`` under
    ``TrivialPreference``. The root marks ``D``; the child marks
    ``U``. The exact byte-for-byte string below is the renderer's
    contract — changes require a deliberate update to this snapshot.
    """
    theory = _tweety_theory()
    flies_opus = _find_argument(theory, _ga("flies", "opus"))
    tree = build_tree(flies_opus, TrivialPreference(), theory)
    expected = (
        "flies(opus)  [r1]  (D)\n"
        "└─ ~flies(opus)  [r2]  (U)"
    )
    assert render_tree(tree) == expected


def test_render_nixon_diamond_tree_snapshot() -> None:
    """Snapshot of the Nixon Diamond tree rooted at ``⟨{r2}, pacifist(nixon)⟩``.

    Scout Section 5.2 direct Nixon theory: Garcia & Simari 2004
    Def 5.1 + Def 4.7 give a single-child tree — the pacifist root
    marks ``D`` and the hawk leaf marks ``U``. Def 4.7 cond 3 and
    cond 4 together prevent any grandchild.
    """
    theory = _direct_nixon_theory()
    pacifist = _find_argument(theory, _ga("pacifist", "nixon"))
    tree = build_tree(pacifist, TrivialPreference(), theory)
    expected = (
        "pacifist(nixon)  [r2]  (D)\n"
        "└─ ~pacifist(nixon)  [r1]  (U)"
    )
    assert render_tree(tree) == expected


def test_render_is_deterministic() -> None:
    """``render_tree`` is pure — two calls on the same node are byte-identical.

    This is a guard against any future caching / mutation / hash
    nondeterminism leaking into the renderer. The prompt names it
    explicitly as a dedicated unit test and as a Hypothesis property.
    """
    theory = _direct_nixon_theory()
    pacifist = _find_argument(theory, _ga("pacifist", "nixon"))
    tree = build_tree(pacifist, TrivialPreference(), theory)
    assert render_tree(tree) == render_tree(tree)
