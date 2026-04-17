"""Tests for ``gunray.dialectic.render_tree_mermaid`` — Mermaid emitter.

``render_tree_mermaid`` is a pure deterministic GitHub-native Mermaid
flowchart emitter for ``DialecticalNode``. Mirrors ``test_render.py``
shape: leaf case, full-tree snapshot (byte-for-byte ``==``),
determinism guard, and Hypothesis property tests.
"""

from __future__ import annotations

from conftest import theory_with_root_argument_strategy
from hypothesis import given, settings

from gunray.arguments import Argument, build_arguments
from gunray.dialectic import build_tree, render_tree_mermaid
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


def test_render_mermaid_leaf_node() -> None:
    """A childless ``DialecticalNode`` renders to two lines: the
    ``flowchart TD`` header and a single node declaration with the
    ``U`` mark (Garcia & Simari 2004 Procedure 5.1)."""
    theory = _tweety_theory()
    flies_tweety = _find_argument(theory, _ga("flies", "tweety"))
    tree = build_tree(flies_tweety, TrivialPreference(), theory)
    assert tree.children == ()
    rendered = render_tree_mermaid(tree)
    lines = rendered.splitlines()
    assert lines[0] == "flowchart TD"
    assert len(lines) == 2
    assert "flies(tweety)" in lines[1]
    assert "[r1]" in lines[1]
    assert lines[1].endswith(' U"]')


def test_render_mermaid_tweety_opus_snapshot() -> None:
    """Byte-for-byte snapshot of the Tweety opus dialectical tree.

    Root ``flies(opus)`` marks ``D``; child ``~flies(opus)`` marks
    ``U``. Synthetic ids are assigned pre-order via
    ``_sorted_children``.
    """
    theory = _tweety_theory()
    flies_opus = _find_argument(theory, _ga("flies", "opus"))
    tree = build_tree(flies_opus, TrivialPreference(), theory)
    expected = (
        'flowchart TD\n    n0["flies(opus) [r1] D"]\n    n1["~flies(opus) [r2] U"]\n    n0 --> n1'
    )
    assert render_tree_mermaid(tree) == expected


def test_render_mermaid_nixon_diamond_snapshot() -> None:
    """Byte-for-byte snapshot of the Nixon Diamond Mermaid output."""
    theory = _direct_nixon_theory()
    pacifist = _find_argument(theory, _ga("pacifist", "nixon"))
    tree = build_tree(pacifist, TrivialPreference(), theory)
    expected = (
        "flowchart TD\n"
        '    n0["pacifist(nixon) [r2] D"]\n'
        '    n1["~pacifist(nixon) [r1] U"]\n'
        "    n0 --> n1"
    )
    assert render_tree_mermaid(tree) == expected


def test_render_mermaid_is_deterministic() -> None:
    """``render_tree_mermaid`` is pure — two calls on the same node
    are byte-identical. Guard against caching / mutation / hash
    nondeterminism leaking into the emitter."""
    theory = _direct_nixon_theory()
    pacifist = _find_argument(theory, _ga("pacifist", "nixon"))
    tree = build_tree(pacifist, TrivialPreference(), theory)
    assert render_tree_mermaid(tree) == render_tree_mermaid(tree)


@given(theory_with_root=theory_with_root_argument_strategy())
@settings(max_examples=500, deadline=None)
def test_hypothesis_render_mermaid_starts_with_flowchart_header(
    theory_with_root: tuple[DefeasibleTheory, Argument],
) -> None:
    """Property: every rendered Mermaid output starts with ``flowchart TD``."""
    theory, root = theory_with_root
    tree = build_tree(root, TrivialPreference(), theory)
    rendered = render_tree_mermaid(tree)
    assert rendered.splitlines()[0] == "flowchart TD"


@given(theory_with_root=theory_with_root_argument_strategy())
@settings(max_examples=500, deadline=None)
def test_hypothesis_render_mermaid_is_deterministic(
    theory_with_root: tuple[DefeasibleTheory, Argument],
) -> None:
    """Property: any generated dialectical tree renders byte-identically."""
    theory, root = theory_with_root
    tree = build_tree(root, TrivialPreference(), theory)
    assert render_tree_mermaid(tree) == render_tree_mermaid(tree)
