"""Gunray error types with conformance-suite-compatible error codes."""

from __future__ import annotations


class GunrayError(Exception):
    """Base class for evaluator errors."""

    code = "gunray_error"


class ParseError(GunrayError):
    """Raised when a rule string cannot be parsed."""

    code = "parse_error"


class SafetyViolationError(GunrayError):
    """Raised when a rule violates Datalog safety conditions."""

    code = "safety_violations"


class UnboundVariableError(GunrayError):
    """Raised when a head variable is not range-restricted."""

    code = "unbound_variable"


class ArityMismatchError(GunrayError):
    """Raised when a predicate is used with inconsistent arities."""

    code = "arity_mismatch"


class CyclicNegationError(GunrayError):
    """Raised when a program contains recursive negation."""

    code = "cyclic_negation"
