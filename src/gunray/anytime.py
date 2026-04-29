"""Anytime result sentinels for bounded exact enumerators."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Literal

if TYPE_CHECKING:
    from .arguments import Argument
    from .trace import DefeasibleTrace

VacuousRemainderProvenance = Literal["vacuous"]


class EnumerationExceeded(Exception):
    """Exact enumeration stopped at a caller-supplied candidate ceiling.

    Zilberstein 1996 frames anytime algorithms as returning the best
    available partial result when resource bounds interrupt exhaustive
    computation. Gunray uses this sentinel when a finite but adversarial
    enumerator has more candidates than the caller allowed.
    """

    def __init__(
        self,
        *,
        partial_arguments: tuple["Argument", ...],
        max_arguments: int,
        partial_trace: "DefeasibleTrace | None" = None,
        partial_count: int | None = None,
        reason: str | None = None,
    ) -> None:
        self.partial_arguments = partial_arguments
        self.max_arguments = max_arguments
        self.partial_trace = partial_trace
        self.reason = reason or (
            "argument enumeration budget exceeded: "
            f"{len(partial_arguments)} candidates produced of {max_arguments} allowed"
        )
        self.partial_count = partial_count if partial_count is not None else len(partial_arguments)
        self.max_candidates = max_arguments
        self.remainder_provenance: VacuousRemainderProvenance = "vacuous"
        super().__init__(self.reason)
