from __future__ import annotations

import pytest

from gunray.semantics import SemanticError, add_values


def test_add_values_accepts_numeric_pair() -> None:
    assert add_values(1, 2) == 3
    assert add_values(1.5, 2.5) == 4.0


def test_add_values_rejects_mixed_types() -> None:
    with pytest.raises(SemanticError):
        add_values(1, "a")
    with pytest.raises(SemanticError):
        add_values("a", 1)


def test_add_values_rejects_string_string() -> None:
    with pytest.raises(SemanticError):
        add_values("a", "b")


def test_add_values_rejects_bool_operands() -> None:
    with pytest.raises(SemanticError):
        add_values(True, 1)
    with pytest.raises(SemanticError):
        add_values(1, False)
