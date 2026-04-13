"""Argument structures: Garcia & Simari 2004 Def 3.1, Simari & Loui 1992 Def 2.2.

An argument structure is a pair ``<A, h>`` where ``A`` is a subset of
the defeasible rule base and ``h`` is the conclusion. This module
defines the value type. Argument construction (enforcing minimality
and non-contradiction) lives in dispatch B1.3's ``build_arguments``.
"""

from __future__ import annotations

from dataclasses import dataclass

from .types import GroundAtom, GroundDefeasibleRule


@dataclass(frozen=True, slots=True)
class Argument:
    """A pair ``<A, h>``.

    Garcia & Simari 2004 Def 3.1: an argument structure for a literal
    ``h`` from a de.l.p. ``P = (Pi, Delta)`` is a pair ``<A, h>`` with
    ``A`` a subset of ``Delta`` such that (1) ``h`` has a defeasible
    derivation from ``Pi | A``, (2) ``Pi | A`` is non-contradictory,
    and (3) ``A`` is minimal. This dataclass carries the pair;
    conditions (1)-(3) are enforced by ``build_arguments`` (B1.3).
    """

    rules: frozenset[GroundDefeasibleRule]
    conclusion: GroundAtom


def is_subargument(a: Argument, b: Argument) -> bool:
    """Return True iff ``a``'s rule set is a subset of ``b``'s.

    Garcia & Simari 2004 Fig 1 (nested triangles) — a sub-argument of
    ``<A, h>`` is an argument ``<A', h'>`` with ``A'`` a subset of
    ``A``. This is a reflexive partial order on ``Argument`` values
    keyed by ``rules``.
    """

    return a.rules <= b.rules
