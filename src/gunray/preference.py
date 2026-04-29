"""Preference criterion: Garcia & Simari 2004 section 4.

The defeat relation (Garcia & Simari 2004 Def 4.1 / 4.2) is
parameterized over an abstract preference relation ``>`` on
arguments. This module exports the abstract ``PreferenceCriterion``
protocol, a trivial "prefer nothing" instance used to exercise the
dialectical tree in isolation, the real paper-grade
``GeneralizedSpecificity`` criterion based on Simari & Loui 1992
Lemma 2.4, the explicit-priority ``SuperiorityPreference`` from
Garcia & Simari 2004 §4.1, and a ``CompositePreference`` that
delegates to each criterion in priority order.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from ._internal import _force_strict_for_closure, _ground_theory
from .arguments import Argument
from .disagreement import strict_closure
from .schema import DefeasibleTheory
from .types import GroundAtom, GroundDefeasibleRule


@dataclass(frozen=True, slots=True)
class PreferenceComparison:
    """Public comparison report for a pair of arguments.

    Garcia & Simari 2004 p. 108 Example 3.5 makes the comparison
    direction user-visible: one argument is "more specific" than
    another, or the pair remains incomparable/equi-specific. This
    value type exposes that relation without forcing callers to run
    two separate boolean preference checks and reconstruct the reason.
    """

    relation: Literal["left", "right", "incomparable", "equi_specific"]
    left_prefers: bool
    right_prefers: bool
    reason: str
    citation: str


class PreferenceCriterion(Protocol):
    """Garcia & Simari 2004 section 4: abstract preference criterion ``>`` on arguments."""

    def prefers(self, left: Argument, right: Argument) -> bool:
        """Return True iff ``left`` is strictly preferred to ``right``."""
        ...

    def explain_preference(self, left: Argument, right: Argument) -> str | None:
        """Return a brief reason string iff ``prefers(left, right)`` is True.

        Used by :func:`gunray.dialectic.explain` to render why one
        argument defeats another. Implementations MUST return
        ``None`` whenever ``prefers(left, right)`` is False. The
        returned string should be a short clause (no trailing
        punctuation) suitable for embedding in a sentence such as
        "which is <reason>".
        """
        ...


class TrivialPreference:
    """A preference criterion that prefers nothing over nothing.

    Under ``TrivialPreference`` every counter-argument is a blocking
    defeater (Garcia & Simari 2004 Def 4.2) and none are proper
    defeaters (Garcia & Simari 2004 Def 4.1). Useful for testing the
    dialectical-tree machinery in isolation from any real specificity
    criterion.
    """

    def prefers(self, left: Argument, right: Argument) -> bool:
        return False

    def explain_preference(self, left: Argument, right: Argument) -> str | None:
        """``TrivialPreference`` never prefers anything; always ``None``."""
        return None


class GeneralizedSpecificity:
    """Simari & Loui 1992 Lemma 2.4 generalized specificity over a theory.

    Simari & Loui 1992 Definition 2.6 defines strict specificity
    ``⟨T₁, h₁⟩ ≻_spec ⟨T₂, h₂⟩`` semantically: every "activation"
    ``e`` of the weaker argument also activates the stronger one, and
    some activation of the stronger one fails to activate the weaker.
    Lemma 2.4 (p.14) reduces that semantic condition to an equivalent
    antecedent-only syntactic check:

        ``⟨T₁, h₁⟩ ≽ ⟨T₂, h₂⟩`` iff for every antecedent ``x ∈ An(T₂)``,
        ``K_N ∪ An(T₁) ∪ T₂ |~ x``.

    Strict specificity ``≻`` is the ``≽`` direction plus the converse
    failure: ``right`` does not cover ``left``.

    Garcia & Simari 2004 Definition 3.5 restates the same criterion as
    "generalized specificity" for DeLP, using the set ``H_1`` of
    literals with defeasible derivation and the "activating sets" of
    arguments. The two formulations are equivalent up to the DeLP
    renaming of ``K_N`` as ``Pi`` (strict rule context).

    Gunray specializes ``K_N`` to the strict rules of ``theory``
    (facts are deliberately excluded — if ``K_N`` included grounded
    facts then every antecedent literal corresponding to a fact would
    be trivially derivable and specificity would collapse). This
    matches the B2.2 dispatch contract and yields the expected
    results on the Opus, Nixon, and Royal-African-Elephant examples
    (Simari 92 §5).

    The criterion is instantiated once per theory; the constructor
    grounds the strict-rule base and caches it for reuse by every
    ``prefers`` call. ``prefers(a, a)`` is always ``False``
    (irreflexivity is a property of strict partial orders and is
    verified by the Hypothesis property suite).
    """

    def __init__(self, theory: DefeasibleTheory) -> None:
        grounded = _ground_theory(theory)
        # K_N is the set of strict rules. Facts are intentionally
        # excluded: seeding the strict_closure with facts would let
        # every fact-backed antecedent cover itself trivially and
        # destroy the antecedent-only distinction Lemma 2.4 relies on.
        self._strict_rules: tuple[GroundDefeasibleRule, ...] = grounded.grounded_strict_rules

    def prefers(self, left: Argument, right: Argument) -> bool:
        """Return ``True`` iff ``left`` is strictly more specific than ``right``.

        Implements Simari & Loui 1992 Lemma 2.4 / Garcia & Simari 2004
        Definition 3.5 as documented on the class docstring. The
        check is:

        1. Does ``left`` cover ``right``? (``right``'s antecedents
           are all derivable from ``K_N ∪ An(left) ∪ T_right``.)
        2. Does ``right`` cover ``left``?
        3. If only (1) holds, ``left`` is strictly more specific.
           If both hold, the arguments are equi-specific and no
           preference is returned. If neither (or only (2)) holds,
           ``left`` is not preferred.
        """

        if left == right:
            return False
        # Simari & Loui 1992 Lemma 2.4 compares non-empty defeasible
        # rule sets T. Empty-rule arguments are strict consequences of
        # K_N/Pi, so specificity does not make either side dominate.
        if not left.rules or not right.rules:
            return False

        left_ant = _antecedents_of(left)
        right_ant = _antecedents_of(right)

        if not self._covers(left_ant, right, right_ant):
            return False
        if self._covers(right_ant, left, left_ant):
            return False
        return True

    def explain_preference(self, left: Argument, right: Argument) -> str | None:
        """Return a brief reason iff ``left`` is strictly more specific.

        Garcia & Simari 2004 §6 (explanation of defeat): a proper
        defeater grounded in specificity is justified by noting that
        the attacker's antecedents strictly entail the target's, but
        not vice versa. This helper renders that reason.
        """

        if not self.prefers(left, right):
            return None
        left_ant = _antecedents_of(left)
        right_ant = _antecedents_of(right)
        if not left_ant and right_ant:
            # Empty-antecedent ("presumption-like") attacker case: the
            # attacker has no conditions to discharge, so it dominates
            # by vacuous cover while the target's antecedents block
            # the converse. The prefers guard above already excluded
            # empty-rule arguments.
            return "strictly more specific (no antecedents to discharge)"
        return "strictly more specific"

    def compare(self, left: Argument, right: Argument) -> PreferenceComparison:
        """Return the full generalized-specificity relation for ``left`` and ``right``.

        Garcia & Simari 2004 p. 108 Example 3.5 uses generalized
        specificity as an inspectable comparison: a chicken-based
        argument is more specific than a bird-based argument, and a
        scared-chicken argument is more specific than the chicken
        argument because it uses more information. The underlying
        strict preference is still ``prefers``; this method preserves
        both directions and a paper citation for explanation layers.
        """

        left_prefers = self.prefers(left, right)
        right_prefers = self.prefers(right, left)
        if left_prefers:
            relation: Literal["left", "right", "incomparable", "equi_specific"] = "left"
            reason = "left argument is strictly more specific"
        elif right_prefers:
            relation = "right"
            reason = "right argument is strictly more specific"
        elif left == right:
            relation = "equi_specific"
            reason = "arguments are identical"
        else:
            relation = "incomparable"
            reason = "neither argument strictly covers the other"
        return PreferenceComparison(
            relation=relation,
            left_prefers=left_prefers,
            right_prefers=right_prefers,
            reason=reason,
            citation="Garcia & Simari 2004, p. 108",
        )

    def _covers(
        self,
        covering_antecedents: frozenset[GroundAtom],
        covered_argument: Argument,
        covered_antecedents: frozenset[GroundAtom],
    ) -> bool:
        """Return True iff ``covering`` side covers ``covered_antecedents``.

        Evaluates the ``≽`` direction of Lemma 2.4:
        ``K_N ∪ covering_antecedents ∪ T_covered |~ x`` for every
        ``x`` in ``covered_antecedents``. Uses
        ``disagreement.strict_closure`` with ``covered_argument``'s
        rules shadowed by ``_force_strict_for_closure`` — the same
        pattern ``build_arguments`` uses to treat defeasible rules as
        closure-propagating for condition (1) of Garcia 04 Def 3.1.
        """

        if not covered_antecedents:
            # Vacuous coverage is valid only after the empty-rule
            # incomparability guard in ``prefers``.
            return True

        shadowed = tuple(_force_strict_for_closure(rule) for rule in covered_argument.rules)
        closure = strict_closure(
            covering_antecedents,
            self._strict_rules + shadowed,
        )
        return all(atom in closure for atom in covered_antecedents)


class SuperiorityPreference:
    """Garcia & Simari 2004 §4.1: rule priority criterion.

    The paper notes that comparison criteria are modular: the abstract
    preference relation can be instantiated by an explicit priority
    relation ``>`` over the defeasible rule set. Argument ``<A1, h1>``
    is preferred to ``<A2, h2>`` iff every rule in ``A1`` dominates
    every rule in ``A2`` under the *transitive closure* of the
    explicit priority relation supplied as
    ``DefeasibleTheory.superiority``. The pairs are written as
    ``(stronger_rule_id, weaker_rule_id)``.

    The criterion is constructed once per theory; the constructor
    computes the transitive closure of the priority relation as a
    ``frozenset[tuple[str, str]]`` keyed by ``rule_id`` and reuses it
    on every ``prefers`` call.

    Edge cases (per the B2.5 dispatch contract):

    * Reflexivity: ``prefers(a, a) is False`` — strict partial orders
      are irreflexive.
    * Strict-vs-defeasible: if either ``left.rules`` or ``right.rules``
      is empty (a strict-only argument), ``prefers`` returns ``False``.
      Strict and defeasible arguments are incomparable under the rule
      priority criterion; the strict-only shortcut in
      ``DefeasibleEvaluator`` handles strict arguments at the outer
      pipeline level.
    * Partial dominance fails: every rule in ``left.rules`` must
      dominate every rule in ``right.rules`` under the closed relation.
      A single missing pair is enough to return ``False``.
    """

    def __init__(self, theory: DefeasibleTheory) -> None:
        # Stash the raw pairs and precompute the transitive closure
        # over rule_ids. Floyd-Warshall over the active id set keeps
        # the closure cost to ``O(|ids|^3)``; in practice the rule set
        # per theory is tiny (single digits), so the cost is dominated
        # by the dictionary churn rather than the algorithm.
        pairs: tuple[tuple[str, str], ...] = tuple(theory.superiority)
        ids: set[str] = set()
        for higher, lower in pairs:
            ids.add(higher)
            ids.add(lower)
        # Build adjacency, then transitive closure via repeated
        # composition. Floyd-Warshall is overkill for the typical
        # theory size; the loop here is the same complexity but keeps
        # the data structure as a flat set of pairs.
        closure: set[tuple[str, str]] = set(pairs)
        changed = True
        while changed:
            changed = False
            new_pairs: set[tuple[str, str]] = set()
            for hi, mid_a in closure:
                for mid_b, lo in closure:
                    if mid_a == mid_b:
                        new_pairs.add((hi, lo))
            additions = new_pairs - closure
            if additions:
                closure |= additions
                changed = True
        self._closure: frozenset[tuple[str, str]] = frozenset(closure)

    def prefers(self, left: Argument, right: Argument) -> bool:
        """Return ``True`` iff every rule in ``left`` dominates every rule in ``right``.

        Implements Garcia & Simari 2004 §4.1's rule priority criterion
        as documented on the class docstring. The check is:

        1. Reject reflexive comparisons (``left == right``).
        2. Reject empty-rule (strict-only) arguments on either side —
           the rule priority criterion is undefined for them.
        3. For every ``(lr, rr)`` pair drawn from
           ``left.rules × right.rules``, require ``(lr.rule_id,
           rr.rule_id)`` to be in the precomputed transitive closure.
           Any single missing pair returns ``False``.
        """

        if left == right:
            return False
        if not left.rules or not right.rules:
            return False

        closure = self._closure
        for lr in left.rules:
            for rr in right.rules:
                if (lr.rule_id, rr.rule_id) not in closure:
                    return False
        return True

    def explain_preference(self, left: Argument, right: Argument) -> str | None:
        """Return a brief reason iff ``left`` dominates ``right`` by priority.

        Garcia & Simari 2004 §6 justifies a priority-based defeat by
        citing the explicit superiority pair(s) that decide it.
        """

        if not self.prefers(left, right):
            return None
        return "explicitly prioritised by the theory's superiority relation"


class CompositePreference:
    """First-criterion-to-fire composition of preference criteria.

    Garcia & Simari 2004 §4.1 notes that comparison criteria are
    modular and may be combined. ``CompositePreference`` implements
    *first-criterion-to-fire* composition: each child criterion is
    consulted in declaration order, and the first criterion to
    express an opinion for the pair (``left``, ``right``) — in
    *either* direction — monopolises the answer. Concretely, for
    each criterion ``c``:

    * if ``c.prefers(left, right)`` returns ``True``, the composite
      returns ``True`` immediately;
    * if ``c.prefers(right, left)`` returns ``True`` (i.e. ``c``
      prefers the *other* direction), the composite returns
      ``False`` immediately — subsequent criteria are not consulted;
    * otherwise ``c`` is silent on this pair and the composite
      falls through to the next criterion.

    If no criterion fires in either direction, the composite
    returns ``False``.

    **Why first-fire and not any-wins.** The ``any``-wins semantics
    used in earlier drafts broke asymmetry: if criterion 1 prefers
    ``(a, b)`` and criterion 2 prefers ``(b, a)``, ``any``-wins
    returned ``True`` for both ``prefers(a, b)`` and ``prefers(b, a)``,
    contradicting strict-partial-order axioms that Garcia & Simari
    2004 §4/§5's dialectical-tree theorems assume. First-fire
    restores asymmetry when each underlying criterion is itself a
    strict partial order: the first criterion to fire cannot prefer
    both directions, so by construction the composite cannot
    either.

    **Per-criterion transitivity.** Transitivity holds per
    criterion: if every pair (a, b), (b, c), (a, c) is decided by
    the *same* criterion ``c``, and ``c`` is transitive, the
    composite is transitive for that path. Cross-criterion
    transitivity (where (a, b) is decided by one criterion and
    (b, c) by another) is best-effort and not guaranteed by the
    abstract composition; it is a property of the specific
    criterion sequence and theory in use. The foreman's directive
    "superiority first, specificity fallback" embraces this: any
    pair where superiority has an opinion is handled by
    superiority, and only equi-priority pairs fall through to
    specificity.

    **Canonical use** under the B2.5 / B2.6 foreman decision:

    .. code-block:: python

        CompositePreference(
            SuperiorityPreference(theory),
            GeneralizedSpecificity(theory),
        )

    so that explicit user-supplied priority dominates the computed
    Lemma 2.4 specificity preference. Superiority is consulted
    first and monopolises every pair it has an opinion on;
    specificity only decides pairs on which superiority is silent.

    **Properties verified by Hypothesis** (``tests/test_superiority.py``):

    * ``test_hypothesis_composite_is_monotonic`` — if the composite
      prefers ``a`` over ``b``, at least one child criterion
      prefers ``a`` over ``b``.
    * ``test_hypothesis_composite_is_asymmetric`` — the composite
      never prefers both ``(a, b)`` and ``(b, a)`` simultaneously
      when each child is a strict partial order.
    """

    def __init__(self, *criteria: PreferenceCriterion) -> None:
        self._criteria: tuple[PreferenceCriterion, ...] = criteria

    def prefers(self, left: Argument, right: Argument) -> bool:
        for criterion in self._criteria:
            if criterion.prefers(left, right):
                return True
            if criterion.prefers(right, left):
                return False
        return False

    def explain_preference(self, left: Argument, right: Argument) -> str | None:
        """Return the reason from the first child criterion to fire.

        Matches the first-criterion-to-fire semantics of ``prefers``:
        the first child that expresses an opinion on ``(left, right)``
        monopolises the answer. If a child prefers the reverse
        direction first, the composite is silent on ``(left, right)``.
        """
        for criterion in self._criteria:
            reason = criterion.explain_preference(left, right)
            if reason is not None:
                return reason
            if criterion.prefers(right, left):
                return None
        return None


def _antecedents_of(argument: Argument) -> frozenset[GroundAtom]:
    """Return ``An(T)`` — the union of defeasible rule bodies in ``T``.

    Simari & Loui 1992 Implementation Details (p.10): ``An(T)`` is
    the set of antecedents of the rules in ``T``. For a gunray
    ``Argument`` that is the union of ``rule.body`` over every
    ``rule`` in ``argument.rules``.
    """

    return frozenset(atom for rule in argument.rules for atom in rule.body)
