"""Dialectical machinery: Garcia & Simari 2004 Defs 3.4, 4.1, 4.2, 4.7, 5.1; Proc 5.1.

This module implements the defeat relation and dialectical tree
construction from Garcia & Simari 2004. The public surface here is:

- ``counter_argues`` (Def 3.4) — one argument counter-argues another
  at a literal ``h`` iff ``h`` is (or can be built as) the conclusion
  of a *sub-argument* of the target and the attacker's conclusion
  disagrees with it. **Critical**: the attack must descend into
  sub-arguments, not merely inspect the target's root conclusion.
- ``proper_defeater`` (Def 4.1) / ``blocking_defeater`` (Def 4.2) —
  defeat relations parameterised by a ``PreferenceCriterion``.
- ``DialecticalNode`` (Def 5.1) — immutable tree node.
- ``build_tree`` (Def 5.1 + Def 4.7 acceptable-line conditions) —
  constructs the dialectical tree rooted at an argument, admitting
  children only if the extended line satisfies every Def 4.7
  condition.
- ``mark`` (Proc 5.1) — pure post-order marking on the immutable
  tree. Leaves ``→ U``; any ``U`` child ``→ D``; all ``D`` children
  ``→ U`` (reinstatement).
- ``render_tree`` — pure deterministic Unicode debugger for a
  ``DialecticalNode``. Not a paper definition; a deliberate
  engineering promotion per the B1.5 refactor plan so the renderer
  can visually diagnose Def 4.7 acceptable-line bugs during B1.6.

Explicitly **not** in this module: ``answer`` (coming later in the
B1.5 dispatch) and wiring to ``DefeasibleEvaluator`` (that lands in
B1.6). Caching, pruning, or any other optimisation is also out of
scope (Block 1 is correctness-first).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .arguments import (
    Argument,
    _fact_atoms,
    _force_strict_for_closure,
    build_arguments,
    is_subargument,
)
from .defeasible import _atom_sort_key
from .disagreement import complement, disagrees, strict_closure
from .parser import parse_defeasible_theory
from .preference import PreferenceCriterion
from .schema import DefeasibleTheory
from .types import GroundAtom, GroundDefeasibleRule


def _theory_strict_rules(
    theory: DefeasibleTheory,
) -> tuple[GroundDefeasibleRule, ...]:
    """Return the ground strict rules of ``theory`` for disagreement checks.

    Garcia & Simari 2004 Def 3.3 defines disagreement relative to the
    strict knowledge base ``Π``. We reach ``Π`` by re-running the
    argument builder's grounding pass over ``theory``.
    """
    # Reuse build_arguments' own machinery: it already grounds strict
    # rules via the same positive-closure pass. Instead of duplicating
    # that logic we import the helpers lazily from `arguments` — this
    # keeps the dialectic module small.
    from .arguments import _ground_rule_instances, _positive_closure_for_grounding

    _facts, defeasible_rules, _conflicts = parse_defeasible_theory(theory)
    strict_source = tuple(r for r in defeasible_rules if r.kind == "strict")
    positive_model = _positive_closure_for_grounding(_facts, defeasible_rules)
    grounded = tuple(
        instance
        for rule in strict_source
        for instance in _ground_rule_instances(rule, positive_model)
    )
    return grounded


def counter_argues(
    attacker: Argument, target: Argument, theory: DefeasibleTheory
) -> bool:
    """Garcia & Simari 2004 Definition 3.4.

    ``⟨A₁, h₁⟩`` counter-argues ``⟨A₂, h₂⟩`` at literal ``h`` iff
    there exists a sub-argument ``⟨A, h⟩`` of ``⟨A₂, h₂⟩`` such that
    ``h₁`` and ``h`` disagree.

    **Directional fix**: this implementation iterates *every*
    sub-argument of ``target`` (via ``is_subargument`` per
    ``arguments.py``) rather than comparing only root conclusions.
    The deleted ``_find_blocking_peer`` never descended; that is the
    whole point of this refactor.
    """
    for _sub in _disagreeing_subarguments(attacker, target, theory):
        return True
    return False


def _disagreeing_subarguments(
    attacker: Argument, target: Argument, theory: DefeasibleTheory
) -> list[Argument]:
    """Return every sub-argument ``⟨A, h⟩`` of ``target`` whose
    conclusion disagrees with ``attacker.conclusion``.

    Helper for ``counter_argues`` / ``proper_defeater`` /
    ``blocking_defeater``. Garcia & Simari 2004 Def 3.4 refers to
    the sub-argument at which the counter-attack lands; Defs 4.1 and
    4.2 condition on the preference between the attacker and *that*
    sub-argument, not the root of ``target``.
    """
    strict_rules = _theory_strict_rules(theory)
    hits: list[Argument] = []
    for sub in build_arguments(theory):
        if not is_subargument(sub, target):
            continue
        if disagrees(attacker.conclusion, sub.conclusion, strict_rules):
            hits.append(sub)
    return hits


def proper_defeater(
    attacker: Argument,
    target: Argument,
    criterion: PreferenceCriterion,
    theory: DefeasibleTheory,
) -> bool:
    """Garcia & Simari 2004 Definition 4.1.

    ``a1`` is a proper defeater for ``a2`` iff it counter-argues
    ``a2`` at some sub-argument ``⟨A, h⟩`` of ``a2`` AND
    ``criterion`` strictly prefers ``a1`` over ``⟨A, h⟩``.

    Under ``TrivialPreference`` nothing is strictly preferred so
    nothing is proper.
    """
    for sub in _disagreeing_subarguments(attacker, target, theory):
        if criterion.prefers(attacker, sub):
            return True
    return False


def blocking_defeater(
    attacker: Argument,
    target: Argument,
    criterion: PreferenceCriterion,
    theory: DefeasibleTheory,
) -> bool:
    """Garcia & Simari 2004 Definition 4.2.

    ``a1`` is a blocking defeater for ``a2`` iff it counter-argues
    ``a2`` at some sub-argument ``⟨A, h⟩`` of ``a2`` AND ``criterion``
    prefers neither direction (neither ``a1 > ⟨A, h⟩`` nor
    ``⟨A, h⟩ > a1``).
    """
    for sub in _disagreeing_subarguments(attacker, target, theory):
        if not criterion.prefers(attacker, sub) and not criterion.prefers(
            sub, attacker
        ):
            return True
    return False


@dataclass(frozen=True, slots=True)
class DialecticalNode:
    """Garcia & Simari 2004 Definition 5.1 — node of a dialectical tree.

    Immutable. No ``mark`` field — marking is a pure function over
    the tree (``mark``), per Procedure 5.1.
    """

    argument: Argument
    children: tuple["DialecticalNode", ...]


def _concordant(
    rule_sets: list[frozenset[GroundDefeasibleRule]],
    theory: DefeasibleTheory,
) -> bool:
    """Return True iff ``Π ∪ (union of rule_sets)`` is non-contradictory.

    Garcia & Simari 2004 Def 4.7 cond 2: the supporting and
    interfering sets must each be concordant. Concordance means
    that the union of an argument set's defeasible rules with the
    strict knowledge base ``Π`` produces no pair of complementary
    literals when closed under the rules.

    Implementation reuses ``arguments._force_strict_for_closure`` to
    wrap every defeasible rule as a strict-kind shadow for the
    closure pass, matching the Def 3.1 condition (2) treatment in
    ``build_arguments``.
    """
    facts, _defeasible, _ = parse_defeasible_theory(theory)
    seeds = _fact_atoms(facts)
    strict_rules = _theory_strict_rules(theory)
    combined: list[GroundDefeasibleRule] = list(strict_rules)
    for rule_set in rule_sets:
        for rule in rule_set:
            combined.append(_force_strict_for_closure(rule))
    closure = strict_closure(seeds, tuple(combined))
    for atom in closure:
        if complement(atom) in closure:
            return False
    return True


def _defeat_kind(
    attacker: Argument,
    target: Argument,
    criterion: PreferenceCriterion,
    theory: DefeasibleTheory,
) -> str | None:
    """Return ``"proper"``, ``"blocking"``, or ``None``.

    Helper used by ``build_tree`` to classify a candidate defeater.
    Proper takes precedence if some disagreeing sub-argument is
    strictly out-preferred by ``attacker``; blocking is returned if
    some disagreeing sub-argument is preference-neutral vs.
    ``attacker``; otherwise ``None``.
    """
    subs = _disagreeing_subarguments(attacker, target, theory)
    proper_hit = False
    blocking_hit = False
    for sub in subs:
        if criterion.prefers(attacker, sub):
            proper_hit = True
        elif not criterion.prefers(sub, attacker):
            blocking_hit = True
    if proper_hit:
        return "proper"
    if blocking_hit:
        return "blocking"
    return None


def build_tree(
    root: Argument,
    criterion: PreferenceCriterion,
    theory: DefeasibleTheory,
) -> DialecticalNode:
    """Garcia & Simari 2004 Def 5.1 + Def 4.7 acceptable argumentation line.

    Construct the dialectical tree rooted at ``root``. A child is
    admitted only if (a) it is a proper or blocking defeater of its
    parent, and (b) extending the current line with it still
    satisfies every Def 4.7 acceptable-line condition:

    1. The line is finite.
    2. The supporting set ``S_s = ⋃ A_{2i}`` (0-indexed: positions 0,
       2, 4, ...) and interfering set ``S_i = ⋃ A_{2i+1}`` (positions
       1, 3, 5, ...) are each concordant (union with ``Π``
       non-contradictory).
    3. No argument in the line is a sub-argument of an earlier one.
    4. If the parent edge was a blocking defeat, the child edge must
       be a proper defeat (otherwise the line terminates).

    Violating conditions 2, 3, or 4 truncates that branch by simply
    not adding the violator as a child. Condition 1 is structurally
    guaranteed: ``build_arguments`` returns a finite frozenset and
    cond 3 forbids re-entry along a line.
    """
    universe = build_arguments(theory)
    return _expand(root, [root], [None], universe, criterion, theory)


def _expand(
    current: Argument,
    line: list[Argument],
    edge_kinds: list[str | None],
    universe: "frozenset[Argument]",
    criterion: PreferenceCriterion,
    theory: DefeasibleTheory,
) -> DialecticalNode:
    """Recursive expansion of a single dialectical-tree node.

    ``line[i]`` is the argument at position ``i`` along the path
    from the root to ``current`` (so ``line[-1] == current``).
    ``edge_kinds[i]`` is the kind of defeat (``"proper"`` /
    ``"blocking"`` / ``None`` for the root) used to attach
    ``line[i]`` to its parent.
    """
    children_nodes: list[DialecticalNode] = []
    parent_edge_kind = edge_kinds[-1]

    for candidate in universe:
        kind = _defeat_kind(candidate, current, criterion, theory)
        if kind is None:
            continue

        # Def 4.7 cond 4: blocking-defeater-of-blocking-defeater
        # terminates the line.
        if parent_edge_kind == "blocking" and kind == "blocking":
            continue

        # Def 4.7 cond 3: no argument in the line is a sub-argument
        # of an earlier one. We only need to check `candidate`
        # against existing line members — earlier inclusions were
        # already checked when they were added.
        if any(is_subargument(candidate, earlier) for earlier in line):
            continue

        # Def 4.7 cond 2: the supporting set S_s (0-indexed even
        # positions) and interfering set S_i (0-indexed odd
        # positions) must each remain concordant with `candidate`
        # added to its appropriate set.
        new_index = len(line)  # position of `candidate` if admitted
        supporting = [
            line[i].rules for i in range(len(line)) if i % 2 == 0
        ]
        interfering = [
            line[i].rules for i in range(len(line)) if i % 2 == 1
        ]
        if new_index % 2 == 0:
            supporting.append(candidate.rules)
        else:
            interfering.append(candidate.rules)
        if not _concordant(supporting, theory):
            continue
        if not _concordant(interfering, theory):
            continue

        # All Def 4.7 conditions satisfied — recurse.
        new_line = line + [candidate]
        new_edges = edge_kinds + [kind]
        children_nodes.append(
            _expand(candidate, new_line, new_edges, universe, criterion, theory)
        )

    return DialecticalNode(argument=current, children=tuple(children_nodes))


def mark(node: DialecticalNode) -> Literal["U", "D"]:
    """Garcia & Simari 2004 Procedure 5.1 — pure marking.

    Post-order:

    - leaf ``→ U``
    - inner node with any ``U`` child ``→ D``
    - inner node whose every child marks ``D`` ``→ U`` (reinstatement)

    No mutation, no caching, no early exit. Block 1 is
    correctness-first.
    """
    if not node.children:
        return "U"
    if any(mark(child) == "U" for child in node.children):
        return "D"
    return "U"


def _format_atom(atom: GroundAtom) -> str:
    """Pretty-print a ground atom for the tree renderer.

    ``atom.predicate`` already carries the ``~`` prefix for strong
    negation (per ``disagreement.complement``). Zero-arity atoms
    render bare; others render as ``pred(a, b, c)``.
    """
    if not atom.arguments:
        return atom.predicate
    args = ", ".join(str(arg) for arg in atom.arguments)
    return f"{atom.predicate}({args})"


def _format_rule_ids(argument: Argument) -> str:
    """Return the sorted rule-id list for an argument's header line."""
    ids = sorted(rule.rule_id for rule in argument.rules)
    return "[" + ", ".join(ids) + "]"


def _sorted_children(node: DialecticalNode) -> tuple[DialecticalNode, ...]:
    """Sort children by their argument's conclusion for stable rendering.

    Uses ``defeasible._atom_sort_key`` as the primary key (by
    ``(predicate, arguments)``) and the sorted rule-id tuple as a
    secondary key to distinguish distinct arguments that share a
    conclusion.
    """
    return tuple(
        sorted(
            node.children,
            key=lambda child: (
                _atom_sort_key(child.argument.conclusion),
                tuple(sorted(rule.rule_id for rule in child.argument.rules)),
            ),
        )
    )


def render_tree(node: DialecticalNode) -> str:
    """Render ``node`` as a deterministic Unicode tree.

    Format::

        conclusion  [rule_id, rule_id, ...]  (U|D)
        ├─ child_conclusion  [...]  (U|D)
        │  └─ ...
        └─ last_child  [...]  (U|D)

    The function is pure and deterministic: given the same input it
    always produces byte-identical output. Children are sorted via
    ``defeasible._atom_sort_key`` on their conclusion, with the
    sorted rule-id tuple as a tiebreaker for distinct arguments
    sharing a conclusion. ``mark`` is recomputed by calling the pure
    ``mark(node)`` recursively — repeated recursion is deliberate
    (Block 1 is correctness-first).
    """
    return "\n".join(_render_lines(node))


def _render_lines(node: DialecticalNode) -> list[str]:
    """Return the rendered lines for ``node`` and its descendants.

    The header line is rendered without any prefix; caller-supplied
    indentation is handled by ``_render_child_lines`` for nested
    subtrees.
    """
    head = f"{_format_atom(node.argument.conclusion)}  {_format_rule_ids(node.argument)}  ({mark(node)})"
    lines = [head]
    children = _sorted_children(node)
    for index, child in enumerate(children):
        is_last = index == len(children) - 1
        lines.extend(_render_child_lines(child, is_last))
    return lines


def _render_child_lines(child: DialecticalNode, is_last: bool) -> list[str]:
    """Render ``child``'s subtree with tree-drawing prefixes."""
    branch = "└─ " if is_last else "├─ "
    continuation = "   " if is_last else "│  "
    child_lines = _render_lines(child)
    rendered = [branch + child_lines[0]]
    for line in child_lines[1:]:
        rendered.append(continuation + line)
    return rendered


