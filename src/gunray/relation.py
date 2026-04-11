"""Indexed relation storage for accelerating repeated joins."""

from __future__ import annotations

from collections.abc import Iterable, Iterator


class IndexedRelation:
    """Store relation rows with lazily built hash indexes over column subsets."""

    def __init__(self, rows: Iterable[tuple[object, ...]] = ()) -> None:
        self._rows: set[tuple[object, ...]] = set()
        self._indexes: dict[
            tuple[int, ...],
            dict[tuple[object, ...], set[tuple[object, ...]]],
        ] = {}
        for row in rows:
            self.add(row)

    def __iter__(self) -> Iterator[tuple[object, ...]]:
        return iter(self._rows)

    def __len__(self) -> int:
        return len(self._rows)

    def __contains__(self, row: object) -> bool:
        return row in self._rows

    def add(self, row: tuple[object, ...]) -> bool:
        if row in self._rows:
            return False
        self._rows.add(row)
        for columns, index in self._indexes.items():
            key = tuple(row[position] for position in columns)
            bucket = index.setdefault(key, set())
            bucket.add(row)
        return True

    def lookup(
        self,
        columns: tuple[int, ...],
        values: tuple[object, ...],
    ) -> set[tuple[object, ...]]:
        index = self.ensure_index(columns)
        return index.get(values, set())

    def ensure_index(
        self,
        columns: tuple[int, ...],
    ) -> dict[tuple[object, ...], set[tuple[object, ...]]]:
        existing = self._indexes.get(columns)
        if existing is not None:
            return existing

        built: dict[tuple[object, ...], set[tuple[object, ...]]] = {}
        for row in self._rows:
            key = tuple(row[position] for position in columns)
            bucket = built.setdefault(key, set())
            bucket.add(row)
        self._indexes[columns] = built
        return built

    def as_set(self) -> set[tuple[object, ...]]:
        return set(self._rows)

    def difference(self, other: "IndexedRelation") -> "IndexedRelation":
        return IndexedRelation(self._rows - other._rows)
