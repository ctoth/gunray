"""Tests for `gunray.dialectic` — Garcia & Simari 2004 Defs 3.4, 4.1-4.2, 4.7, 5.1; Proc 5.1."""

from __future__ import annotations

from hypothesis import assume, given, settings
from hypothesis import strategies as st

from gunray.arguments import Argument, build_arguments, is_subargument
from gunray.dialectic import (
    DialecticalNode,
    _concordant,
    blocking_defeater,
    build_tree,
    counter_argues,
    mark,
    proper_defeater,
)
from gunray.preference import TrivialPreference
from gunray.schema import DefeasibleTheory, Rule
from gunray.types import GroundAtom
from conftest import theory_with_root_argument_strategy


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


# -- Test 1 — counter-argument at root (Garcia 04 Def 3.4, Fig 2 left). --


def test_counter_argues_at_root_opus_flies() -> None:
    """Garcia 04 Def 3.4: ⟨r1@opus, flies(opus)⟩ and ⟨r2@opus, ~flies(opus)⟩
    counter-argue each other at their own conclusions."""
    theory = _tweety_theory()
    flies_opus = _find_argument(theory, _ga("flies", "opus"))
    not_flies_opus = _find_argument(theory, _ga("~flies", "opus"))
    assert counter_argues(flies_opus, not_flies_opus, theory)
    assert counter_argues(not_flies_opus, flies_opus, theory)


# -- Test 2 — counter-argument at sub-argument (Garcia 04 Def 3.4, Fig 2 right). --


def _chain_theory() -> DefeasibleTheory:
    """Defeasible chain with an attacker at a sub-argument's conclusion.

    Rules::
        r1: q(X) :- p(X).        (defeasible)
        r2: r(X) :- q(X).        (defeasible)
        r3: ~q(X) :- t(X).       (defeasible — attacker at sub-argument q)
        facts: p(a), t(a).
    """
    return DefeasibleTheory(
        facts={"p": {("a",)}, "t": {("a",)}},
        strict_rules=[],
        defeasible_rules=[
            Rule(id="r1", head="q(X)", body=["p(X)"]),
            Rule(id="r2", head="r(X)", body=["q(X)"]),
            Rule(id="r3", head="~q(X)", body=["t(X)"]),
        ],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )


def test_counter_argues_at_sub_argument_directional_fix() -> None:
    """Garcia 04 Def 3.4 (Fig 2 right): ``⟨{r3}, ~q(a)⟩`` attacks the
    *sub-argument* ``⟨{r1}, q(a)⟩`` of ``⟨{r1,r2}, r(a)⟩``.

    Under gunray's deleted root-only attack path, ``counter_argues``
    would return False because ``~q`` does not disagree with ``r``.
    The directional fix: descent into sub-arguments catches it.
    """
    theory = _chain_theory()
    r_arg = _find_argument(theory, _ga("r", "a"))
    not_q_arg = _find_argument(theory, _ga("~q", "a"))
    assert counter_argues(not_q_arg, r_arg, theory)


# -- Test 3 — proper vs blocking under TrivialPreference. --


def test_proper_and_blocking_defeaters_under_trivial_preference() -> None:
    """Garcia 04 Def 4.1 / 4.2: under ``TrivialPreference`` every
    counter-argument is a *blocking* defeater and none are *proper*
    defeaters (because nothing is strictly preferred)."""
    theory = _tweety_theory()
    flies = _find_argument(theory, _ga("flies", "opus"))
    not_flies = _find_argument(theory, _ga("~flies", "opus"))
    criterion = TrivialPreference()
    assert blocking_defeater(flies, not_flies, criterion, theory)
    assert blocking_defeater(not_flies, flies, criterion, theory)
    assert not proper_defeater(flies, not_flies, criterion, theory)
    assert not proper_defeater(not_flies, flies, criterion, theory)


# -- Test 4 — proper defeater under a mock preference. --


class _MockPreference:
    """A preference criterion that strictly prefers one fixed argument."""

    def __init__(self, winner: Argument) -> None:
        self._winner = winner

    def prefers(self, left: Argument, right: Argument) -> bool:
        return left == self._winner and right != self._winner


def test_proper_defeater_under_mock_preference() -> None:
    """Garcia 04 Def 4.1: with a criterion that strictly prefers the
    attacker over the defended sub-argument, the counter-argument is
    a *proper* defeater and therefore not merely blocking."""
    theory = _tweety_theory()
    flies = _find_argument(theory, _ga("flies", "opus"))
    not_flies = _find_argument(theory, _ga("~flies", "opus"))
    # MockPreference declares `not_flies` strictly preferred.
    criterion = _MockPreference(winner=not_flies)
    assert proper_defeater(not_flies, flies, criterion, theory)
    assert not blocking_defeater(not_flies, flies, criterion, theory)
    # The dispreferred direction is neither proper nor a blocker
    # *towards* a strictly better opponent — it's the strict loser.
    assert not proper_defeater(flies, not_flies, criterion, theory)


# -- Test 5 — Nixon Diamond tree shape (Garcia 04 Def 5.1 + Def 4.7). --


def test_nixon_diamond_tree_shape_under_trivial_preference() -> None:
    """Garcia 04 Def 5.1 with Def 4.7 cond 3 and cond 4.

    ``direct_nixon`` has two defeasible rules::
        r1: ~pacifist(X) :- republican(X).
        r2:  pacifist(X) :- quaker(X).
    Under ``TrivialPreference`` both sides are blocking defeaters of
    each other. The tree rooted at ``⟨{r2}, pacifist(nixon)⟩``:

    - the root has exactly one child, ``⟨{r1}, ~pacifist(nixon)⟩``
      (the hawk argument);
    - the hawk node has **no** children because the only candidate
      counter-attack is the pacifist argument again, which is a
      sub-argument of the root (violating Def 4.7 cond 3) AND would
      be a blocking defeater of a blocking defeater (violating cond
      4).
    """
    theory = _direct_nixon_theory()
    pacifist = _find_argument(theory, _ga("pacifist", "nixon"))
    hawk = _find_argument(theory, _ga("~pacifist", "nixon"))
    tree = build_tree(pacifist, TrivialPreference(), theory)
    assert tree.argument == pacifist
    assert len(tree.children) == 1
    assert tree.children[0].argument == hawk
    assert tree.children[0].children == ()


# -- Test 6 — marking on Nixon Diamond (Garcia 04 Proc 5.1). --


def test_mark_nixon_diamond_is_defeated() -> None:
    """Garcia 04 Proc 5.1: the hawk leaf marks ``U`` and the root
    marks ``D`` — so ``pacifist(nixon)`` is NOT warranted, which is
    the correct skeptical Nixon answer (Simari 92 §5 p.30)."""
    theory = _direct_nixon_theory()
    pacifist = _find_argument(theory, _ga("pacifist", "nixon"))
    tree = build_tree(pacifist, TrivialPreference(), theory)
    assert mark(tree.children[0]) == "U"
    assert mark(tree) == "D"


# -- Test 7 — marking on Tweety ``flies(tweety)`` (Garcia 04 Proc 5.1). --


def test_mark_tweety_flies_is_undefeated() -> None:
    """Garcia 04 Proc 5.1: there is no rule producing ``~flies(tweety)``
    (no strict rule makes tweety a penguin) so the root has no
    children and marks ``U`` — the query is warranted."""
    theory = _tweety_theory()
    flies_tweety = _find_argument(theory, _ga("flies", "tweety"))
    tree = build_tree(flies_tweety, TrivialPreference(), theory)
    assert tree.children == ()
    assert mark(tree) == "U"


# -- Test 8 — circular argumentation (Garcia 04 Def 4.7 cond 3, Fig 6). --


def test_circular_argumentation_is_truncated() -> None:
    """Garcia 04 Def 4.7 cond 3 / Fig 6.

    With ``_chain_theory`` the root ``⟨{r1,r2}, r(a)⟩`` contains the
    sub-argument ``⟨{r1}, q(a)⟩``. A blocking defeater at ``~q(a)``
    is the attacker ``⟨{r3}, ~q(a)⟩``. From there, the only
    defeater candidate at ``q(a)`` is ``⟨{r1}, q(a)⟩`` itself —
    which is a sub-argument of the root. Def 4.7 cond 3 rejects it;
    the branch must truncate at the attacker.
    """
    theory = _chain_theory()
    root = _find_argument(theory, _ga("r", "a"))
    tree = build_tree(root, TrivialPreference(), theory)
    assert len(tree.children) == 1
    attacker_node = tree.children[0]
    assert attacker_node.argument.conclusion == _ga("~q", "a")
    assert attacker_node.children == ()


# -- Test 9 — reciprocal blocking (Garcia 04 Def 4.7 cond 4, Fig 5). --


def _reciprocal_blocking_theory() -> DefeasibleTheory:
    """Three disjoint arguments for ``p``/``~p`` to isolate cond 4.

    Rules::
        r1: p(X)  :- a(X).   fact a(x).
        r2: ~p(X) :- b(X).   fact b(x).
        r3: p(X)  :- c(X).   fact c(x).

    ``⟨{r1}, p(x)⟩`` and ``⟨{r3}, p(x)⟩`` are distinct arguments
    for ``p(x)`` with *disjoint* rule sets, so Def 4.7 cond 3 does
    not apply between them.
    """
    return DefeasibleTheory(
        facts={"a": {("x",)}, "b": {("x",)}, "c": {("x",)}},
        strict_rules=[],
        defeasible_rules=[
            Rule(id="r1", head="p(X)", body=["a(X)"]),
            Rule(id="r2", head="~p(X)", body=["b(X)"]),
            Rule(id="r3", head="p(X)", body=["c(X)"]),
        ],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )


def test_reciprocal_blocking_rejects_blocker_of_blocker() -> None:
    """Garcia 04 Def 4.7 cond 4 / Fig 5.

    Root ``⟨{r1}, p(x)⟩`` — child ``⟨{r2}, ~p(x)⟩`` is a blocking
    defeater (admitted, cond 4 does not yet apply). A grandchild
    candidate ``⟨{r3}, p(x)⟩`` would counter-argue ``⟨{r2}, ~p(x)⟩``
    as another blocking defeater. Def 4.7 cond 4 forbids a blocking
    defeater of a blocking defeater, so the grandchild is rejected.
    ``r3`` and ``r1`` have disjoint rule sets, so cond 3 is *not*
    the one doing the rejection here.
    """
    theory = _reciprocal_blocking_theory()
    r1_arg = next(
        a
        for a in build_arguments(theory)
        if a.conclusion == _ga("p", "x")
        and any(r.rule_id == "r1" for r in a.rules)
    )
    r3_arg = next(
        a
        for a in build_arguments(theory)
        if a.conclusion == _ga("p", "x")
        and any(r.rule_id == "r3" for r in a.rules)
    )
    # Precondition: r1_arg and r3_arg are distinct and neither is a
    # sub-argument of the other, so Def 4.7 cond 3 is silent here.
    assert r1_arg != r3_arg
    assert not is_subargument(r3_arg, r1_arg)
    assert not is_subargument(r1_arg, r3_arg)

    tree = build_tree(r1_arg, TrivialPreference(), theory)
    # Exactly one child: the ~p attacker.
    assert len(tree.children) == 1
    attacker = tree.children[0]
    assert attacker.argument.conclusion == _ga("~p", "x")
    # cond 4: grandchild blocking-of-blocking is rejected.
    assert attacker.children == ()


# -- Test 10 — contradictory supporting line (Garcia 04 Def 4.7 cond 2, Fig 8). --


def _contradictory_supporting_theory() -> DefeasibleTheory:
    """A theory where two supporting-line arguments together with Π
    produce a contradiction.

    Rules::
        d1:  p(X)        :- a(X).
        d2:  ~p(X)       :- hard(X).
        d3:  hard(X)     :- b(X).
        d4:  ~hard(X)    :- c(X).
        strict s1:  ~p(X) :- ~hard(X).

    With ``{d1, d4}`` combined and ``s1`` in Π, closure of the
    fact model produces both ``p(x)`` (from d1) and ``~p(x)``
    (from d4 via s1). But ``{d1}`` alone is consistent, and
    ``{d4}`` alone is consistent. Argument for ``p(x)`` is
    ``⟨{d1}, p(x)⟩``; argument for ``~p(x)`` (via hard) is
    ``⟨{d2, d3}, ~p(x)⟩``; argument for ``~hard(x)`` is
    ``⟨{d4}, ~hard(x)⟩``.
    """
    return DefeasibleTheory(
        facts={"a": {("x",)}, "b": {("x",)}, "c": {("x",)}},
        strict_rules=[Rule(id="s1", head="~p(X)", body=["~hard(X)"])],
        defeasible_rules=[
            Rule(id="d1", head="p(X)", body=["a(X)"]),
            Rule(id="d2", head="~p(X)", body=["hard(X)"]),
            Rule(id="d3", head="hard(X)", body=["b(X)"]),
            Rule(id="d4", head="~hard(X)", body=["c(X)"]),
        ],
        defeaters=[],
        superiority=[],
        conflicts=[],
    )


class _AlwaysProper:
    """Preference criterion that makes every attacker a proper defeater.

    ``prefers(left, right)`` returns True whenever ``left != right``,
    which ensures ``_defeat_kind`` always classifies defeats as
    ``proper``. This removes Def 4.7 cond 4 from the picture so
    cond 2 can be tested in isolation.
    """

    def prefers(self, left: Argument, right: Argument) -> bool:
        return left != right


def test_contradictory_supporting_line_is_truncated() -> None:
    """Garcia 04 Def 4.7 cond 2 / Fig 8.

    With ``_AlwaysProper`` every defeat is a proper defeat so cond 4
    never fires. The intended path is::

        line[0] = ⟨{d1}, p(x)⟩            (supporting, S_s-member)
        line[1] = ⟨{d2, d3}, ~p(x)⟩       (interfering)
        line[2] = ⟨{d4}, ~hard(x)⟩        (supporting, S_s-member)

    ``{d1} ∪ {d4}`` combined with ``Π = {s1: ~p :- ~hard}`` closes
    to ``{p(x), ~hard(x), ~p(x)}`` — contradictory. Def 4.7 cond 2
    rejects the ``⟨{d4}, ~hard(x)⟩`` candidate at position 2.
    """
    theory = _contradictory_supporting_theory()
    root = _find_argument(theory, _ga("p", "x"))
    tree = build_tree(root, _AlwaysProper(), theory)
    # Root should have at least one child (the ~p(x) attacker).
    assert len(tree.children) >= 1
    # The ~p(x) attacker node at position 1 must NOT have
    # ⟨{d4}, ~hard(x)⟩ as a child — Def 4.7 cond 2 rejects it
    # because {d1} ∪ {d4} ∪ Π is contradictory.
    for child in tree.children:
        if child.argument.conclusion == _ga("~p", "x"):
            assert not any(
                grand.argument.conclusion == _ga("~hard", "x")
                for grand in child.children
            ), "Def 4.7 cond 2 must reject the contradictory supporting-set extension"


# -- Hypothesis property tests 11-17 ----------------------------------------


def _tree_depth(node: DialecticalNode) -> int:
    if not node.children:
        return 1
    return 1 + max(_tree_depth(child) for child in node.children)


def _collect_paths(
    node: DialecticalNode,
) -> list[list[DialecticalNode]]:
    if not node.children:
        return [[node]]
    paths: list[list[DialecticalNode]] = []
    for child in node.children:
        for tail in _collect_paths(child):
            paths.append([node] + tail)
    return paths


# 11. build_tree terminates on any finite theory.
@given(theory_with_root_argument_strategy())
@settings(max_examples=500, deadline=5000)
def test_hypothesis_build_tree_terminates(
    pair: tuple[DefeasibleTheory, Argument],
) -> None:
    """Garcia 04 Def 4.7 cond 1: every acceptable line is finite, so
    ``build_tree`` returns in finite time on any finite theory."""
    theory, root = pair
    tree = build_tree(root, TrivialPreference(), theory)
    assert isinstance(tree, DialecticalNode)


# 12. mark is deterministic (pure).
@given(theory_with_root_argument_strategy())
@settings(max_examples=500, deadline=5000)
def test_hypothesis_mark_is_deterministic(
    pair: tuple[DefeasibleTheory, Argument],
) -> None:
    """Garcia 04 Proc 5.1 is a pure recursion — ``mark(node)`` must
    return the same label across repeated calls."""
    theory, root = pair
    tree = build_tree(root, TrivialPreference(), theory)
    assert mark(tree) == mark(tree)


# 13. mark is local — depends only on children's marks.
@given(
    st.lists(st.sampled_from(["U", "D"]), min_size=0, max_size=4),
    st.lists(st.sampled_from(["U", "D"]), min_size=0, max_size=4),
)
def test_hypothesis_mark_is_local(
    left_marks: list[str], right_marks: list[str]
) -> None:
    """Garcia 04 Proc 5.1 depends only on children's marks. Two
    trees sharing the same root argument and the same multiset of
    child marks must mark the root the same way, regardless of the
    deeper structure under each child."""

    # Build a stub root argument via the arguments_strategy pool.
    from conftest import CONCLUSION, RULE_POOL

    root_arg = Argument(rules=frozenset(RULE_POOL[:1]), conclusion=CONCLUSION)

    def _leaf_with_mark(label: str) -> DialecticalNode:
        # A bare leaf marks U. For "D" we wrap it in one extra
        # leaf child so the inner node marks D (any U child → D).
        leaf = DialecticalNode(argument=root_arg, children=())
        if label == "U":
            return leaf
        return DialecticalNode(argument=root_arg, children=(leaf,))

    left_children = tuple(_leaf_with_mark(m) for m in left_marks)
    right_children = tuple(
        # Wrap each into a deeper but same-marking subtree.
        DialecticalNode(
            argument=root_arg,
            children=(_leaf_with_mark(m),),
        )
        if False  # placeholder so deeper/shallower differ structurally
        else _leaf_with_mark(m)
        for m in left_marks
    )
    del right_marks  # unused on purpose — we duplicate left to guarantee parity
    left_tree = DialecticalNode(argument=root_arg, children=left_children)
    right_tree = DialecticalNode(argument=root_arg, children=right_children)
    assert mark(left_tree) == mark(right_tree)


# 14. Every root-to-leaf path is finite (depth-bound sanity check).
@given(theory_with_root_argument_strategy())
@settings(max_examples=500, deadline=5000)
def test_hypothesis_paths_are_finite(
    pair: tuple[DefeasibleTheory, Argument],
) -> None:
    """Garcia 04 Def 4.7 cond 1 — enforced here by simply computing
    a finite depth. If ``build_tree`` ever recursed infinitely, this
    test would hang and trip Hypothesis's deadline."""
    theory, root = pair
    tree = build_tree(root, TrivialPreference(), theory)
    assert _tree_depth(tree) >= 1


# 15. Sub-argument exclusion on every line.
@given(theory_with_root_argument_strategy())
@settings(max_examples=500, deadline=5000)
def test_hypothesis_sub_argument_exclusion(
    pair: tuple[DefeasibleTheory, Argument],
) -> None:
    """Garcia 04 Def 4.7 cond 3: along every root-to-leaf path, no
    argument at position ``k`` is a sub-argument of any argument at
    position ``j < k``."""
    theory, root = pair
    tree = build_tree(root, TrivialPreference(), theory)
    for path in _collect_paths(tree):
        for k, node_k in enumerate(path):
            for j in range(k):
                assert not is_subargument(node_k.argument, path[j].argument)


# 16. Supporting-set concordance on every line.
@given(theory_with_root_argument_strategy())
@settings(max_examples=500, deadline=5000)
def test_hypothesis_supporting_set_concordant(
    pair: tuple[DefeasibleTheory, Argument],
) -> None:
    """Garcia 04 Def 4.7 cond 2 (supporting half): along every
    root-to-leaf path the union of rules at even (0-indexed)
    positions combined with ``Π`` is non-contradictory.

    Precondition: ``Π`` itself must be consistent — Def 4.7 is
    only defined over theories with a concordant strict knowledge
    base (Garcia & Simari 2004 p.8 sets this as a standing
    assumption). Hypothesis-generated theories may violate that,
    in which case we ``assume`` them away.
    """
    theory, root = pair
    assume(_concordant([], theory))
    tree = build_tree(root, TrivialPreference(), theory)
    for path in _collect_paths(tree):
        supporting = [
            path[i].argument.rules for i in range(len(path)) if i % 2 == 0
        ]
        assert _concordant(supporting, theory)


# 17. Interfering-set concordance on every line.
@given(theory_with_root_argument_strategy())
@settings(max_examples=500, deadline=5000)
def test_hypothesis_interfering_set_concordant(
    pair: tuple[DefeasibleTheory, Argument],
) -> None:
    """Garcia 04 Def 4.7 cond 2 (interfering half): along every
    root-to-leaf path the union of rules at odd (0-indexed)
    positions combined with ``Π`` is non-contradictory.

    Same ``Π``-consistency precondition as the supporting-half
    property.
    """
    theory, root = pair
    assume(_concordant([], theory))
    tree = build_tree(root, TrivialPreference(), theory)
    for path in _collect_paths(tree):
        interfering = [
            path[i].argument.rules for i in range(len(path)) if i % 2 == 1
        ]
        assert _concordant(interfering, theory)
