"""Preference criterion: Garcia & Simari 2004 section 4.

The defeat relation (Garcia & Simari 2004 Def 4.1 / 4.2) is
parameterized over an abstract preference relation ``>`` on
arguments. This module exports the abstract ``PreferenceCriterion``
protocol, a trivial "prefer nothing" instance used to exercise the
dialectical tree in isolation, and the real paper-grade
``GeneralizedSpecificity`` criterion based on Simari & Loui 1992
Lemma 2.4.
"""

from __future__ import annotations

from typing import Protocol

from .arguments import Argument, _force_strict_for_closure, _ground_theory
from .disagreement import strict_closure
from .schema import DefeasibleTheory
from .types import GroundAtom, GroundDefeasibleRule


class PreferenceCriterion(Protocol):
    """Garcia & Simari 2004 section 4: abstract preference criterion ``>`` on arguments."""

    def prefers(self, left: Argument, right: Argument) -> bool:
        """Return True iff ``left`` is strictly preferred to ``right``."""
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
        self._strict_rules: tuple[GroundDefeasibleRule, ...] = (
            grounded.grounded_strict_rules
        )

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

        left_ant = _antecedents_of(left)
        right_ant = _antecedents_of(right)

        if not self._covers(left_ant, right, right_ant):
            return False
        if self._covers(right_ant, left, left_ant):
            return False
        return True

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
            # Vacuous coverage: empty antecedent set is trivially
            # entailed.
            return True

        shadowed = tuple(
            _force_strict_for_closure(rule) for rule in covered_argument.rules
        )
        closure = strict_closure(
            covering_antecedents,
            self._strict_rules + shadowed,
        )
        return all(atom in closure for atom in covered_antecedents)


def _antecedents_of(argument: Argument) -> frozenset[GroundAtom]:
    """Return ``An(T)`` — the union of defeasible rule bodies in ``T``.

    Simari & Loui 1992 Implementation Details (p.10): ``An(T)`` is
    the set of antecedents of the rules in ``T``. For a gunray
    ``Argument`` that is the union of ``rule.body`` over every
    ``rule`` in ``argument.rules``.
    """

    return frozenset(
        atom for rule in argument.rules for atom in rule.body
    )
