"""Anytime result sentinels for bounded exact enumerators."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


VacuousRemainderProvenance = Literal["vacuous"]


@dataclass(frozen=True, slots=True)
class EnumerationExceeded:
    """Exact enumeration stopped at a caller-supplied candidate ceiling.

    Zilberstein 1996 frames anytime algorithms as returning the best
    available partial result when resource bounds interrupt exhaustive
    computation. Gunray uses this sentinel when a finite but adversarial
    enumerator has more candidates than the caller allowed.
    """

    partial_count: int
    max_candidates: int
    remainder_provenance: VacuousRemainderProvenance = "vacuous"
