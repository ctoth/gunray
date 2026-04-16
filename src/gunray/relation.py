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

    def average_lookup_size(
        self,
        columns: tuple[int, ...],
    ) -> float:
        if not self._rows:
            return 0.0
        if not columns:
            return float(len(self._rows))
        index = self.ensure_index(columns)
        if not index:
            return 0.0
        return len(self._rows) / len(index)

    def estimated_lookup_size(
        self,
        columns: tuple[int, ...],
        *,
        sample_size: int = 256,
    ) -> float:
        if not self._rows:
            return 0.0
        if not columns:
            return float(len(self._rows))

        existing = self._indexes.get(columns)
        if existing is not None:
            if not existing:
                return 0.0
            return len(self._rows) / len(existing)

        sampled_keys: set[tuple[object, ...]] = set()
        sampled_count = 0
        for row in self._rows:
            sampled_keys.add(tuple(row[position] for position in columns))
            sampled_count += 1
            if sampled_count >= sample_size:
                break
        if not sampled_keys:
            return 0.0
        return sampled_count / len(sampled_keys)

    def as_set(self) -> set[tuple[object, ...]]:
        return set(self._rows)

    def difference(self, other: "IndexedRelation") -> "IndexedRelation":
        result = IndexedRelation()
        result._rows = self._rows - other._rows
        return result
