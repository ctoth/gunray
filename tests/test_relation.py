from __future__ import annotations

import pytest

from gunray.relation import IndexedRelation


def test_difference_bulk_constructs_rows_without_per_row_add(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Large semi-naive deltas need set difference without per-row reindexing."""
    left = IndexedRelation({("a",), ("b",), ("c",)})
    right = IndexedRelation({("b",)})

    def fail_add(_self: IndexedRelation, _row: tuple[object, ...]) -> bool:
        raise AssertionError("difference should not rebuild by per-row add")

    monkeypatch.setattr(IndexedRelation, "add", fail_add)

    result = left.difference(right)

    assert result.as_set() == {("a",), ("c",)}
