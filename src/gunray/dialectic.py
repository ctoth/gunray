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

Explicitly **not** in this module: ``render_tree``, ``answer``, and
wiring to ``DefeasibleEvaluator`` — those land in B1.5 and B1.6.
Caching, pruning, or any other optimisation is also out of scope
(Block 1 is correctness-first).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .arguments import Argument, build_arguments, is_subargument
from .disagreement import complement, disagrees, strict_closure
from .parser import parse_defeasible_theory
from .preference import PreferenceCriterion
from .schema import DefeasibleTheory
from .types import GroundDefeasibleRule


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
    # that logic we import the helper lazily from `arguments` — this
    # keeps the dialectic module small.
    from .arguments import _force_strict_for_closure  # noqa: F401  (used indirectly)
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
    strict_rules = _theory_strict_rules(theory)
    for sub in build_arguments(theory):
        if not is_subargument(sub, target):
            continue
        if disagrees(attacker.conclusion, sub.conclusion, strict_rules):
            return True
    return False


def proper_defeater(
    attacker: Argument,
    target: Argument,
    criterion: PreferenceCriterion,
    theory: DefeasibleTheory,
) -> bool:
    """Garcia & Simari 2004 Definition 4.1.

    ``a1`` is a proper defeater for ``a2`` iff ``a1`` counter-argues
    ``a2`` at some sub-argument ``⟨A, h⟩`` of ``a2`` and ``criterion``
    strictly prefers ``a1`` over ``⟨A, h⟩``.
    """
    raise NotImplementedError


def blocking_defeater(
    attacker: Argument,
    target: Argument,
    criterion: PreferenceCriterion,
    theory: DefeasibleTheory,
) -> bool:
    """Garcia & Simari 2004 Definition 4.2.

    ``a1`` is a blocking defeater for ``a2`` iff ``a1`` counter-argues
    ``a2`` at some sub-argument ``⟨A, h⟩`` of ``a2`` and ``criterion``
    prefers neither direction (neither ``a1 > ⟨A, h⟩`` nor
    ``⟨A, h⟩ > a1``).
    """
    raise NotImplementedError


@dataclass(frozen=True, slots=True)
class DialecticalNode:
    """Garcia & Simari 2004 Definition 5.1 — node of a dialectical tree.

    Immutable. No ``mark`` field — marking is a pure function over
    the tree (``mark``), per Procedure 5.1.
    """

    argument: Argument
    children: tuple["DialecticalNode", ...]


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
    2. The supporting set ``S_s = ⋃ A_{2i}`` and interfering set
       ``S_i = ⋃ A_{2i+1}`` are each concordant (union with ``Π``
       non-contradictory).
    3. No argument in the line is a sub-argument of an earlier one.
    4. If the parent edge is a blocking defeat, the child edge must
       be a proper defeat (otherwise the line terminates).

    Violating conditions 2, 3, or 4 truncates that branch by simply
    not adding the violator as a child.
    """
    raise NotImplementedError


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
