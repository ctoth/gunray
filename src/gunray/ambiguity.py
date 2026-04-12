"""Ambiguity-policy helpers for defeasible evaluation."""

from __future__ import annotations

from dataclasses import dataclass

from .schema import Policy
from .types import GroundAtom


@dataclass(frozen=True, slots=True)
class AmbiguityPolicy:
    """Operational ambiguity-policy switches for the current evaluator."""

    name: Policy
    attacker_basis: str


def resolve_ambiguity_policy(policy: Policy) -> AmbiguityPolicy:
    """Map a Gunray policy to the evaluator's attacker basis."""

    if policy is Policy.BLOCKING:
        return AmbiguityPolicy(name=policy, attacker_basis="proved")
    if policy is Policy.PROPAGATING:
        return AmbiguityPolicy(name=policy, attacker_basis="supported")
    raise ValueError(f"Unsupported ambiguity policy: {policy.value}")


def attacker_basis_atoms(
    policy: AmbiguityPolicy,
    *,
    proven: set[GroundAtom],
    supported: set[GroundAtom],
) -> set[GroundAtom]:
    """Return the atoms that may activate attacking rules under the chosen policy."""

    if policy.attacker_basis == "proved":
        return proven
    return supported
