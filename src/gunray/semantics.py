"""Explicit value semantics for Gunray term evaluation and constraints.

Gunray currently adopts a small, concrete value domain policy:

- Equality and inequality are exact Python value comparisons on normalized scalars.
- Ordering is delegated to Python ordering, but only when the operands are mutually
  comparable under that ordering.
- `+` is numeric addition for numeric operands and string-style concatenation otherwise.
- `-` is numeric subtraction only.

This module exists so those choices are explicit and centrally reviewable rather than
implicitly spread across the evaluator.
"""

from __future__ import annotations


class SemanticError(ValueError):
    """Raised when an operation is outside Gunray's explicit value semantics."""


def values_equal(left: object, right: object) -> bool:
    """Return whether two values are equal under Gunray semantics."""

    return left == right


def values_not_equal(left: object, right: object) -> bool:
    """Return whether two values are unequal under Gunray semantics."""

    return not values_equal(left, right)


def add_values(left: object, right: object) -> object:
    """Evaluate `left + right` under Gunray semantics."""

    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left + right
    return f"{left}{right}"


def subtract_values(left: object, right: object) -> object:
    """Evaluate `left - right` under Gunray semantics."""

    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left - right
    raise SemanticError("Subtraction requires numeric operands")


def compare_values(left: object, operator: str, right: object) -> bool:
    """Evaluate an ordering or equality comparison under Gunray semantics."""

    if operator == "==":
        return values_equal(left, right)
    if operator == "!=":
        return values_not_equal(left, right)

    try:
        if operator == "<=":
            return left <= right
        if operator == "<":
            return left < right
        if operator == ">=":
            return left >= right
        if operator == ">":
            return left > right
    except TypeError as exc:
        raise SemanticError(
            f"Operator {operator!r} is undefined for {type(left).__name__} and {type(right).__name__}"
        ) from exc

    raise SemanticError(f"Unknown comparison operator: {operator}")
