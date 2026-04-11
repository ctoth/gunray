"""Compiled slot-based matching for simple positive rule bodies."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from .relation import IndexedRelation
from .semantics import values_equal
from .types import Atom, Constant, Variable, Wildcard


_UNBOUND = object()


@dataclass(frozen=True, slots=True)
class CompiledSimpleAtom:
    source_index: int
    predicate: str
    lookup_columns: tuple[int, ...]
    constant_values: tuple[object, ...]
    lookup_slots: tuple[int, ...]
    assigned_columns: tuple[int, ...]
    assigned_slots: tuple[int, ...]
    equality_columns: tuple[int, ...]
    equality_slots: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class CompiledSimpleMatcher:
    slot_names: tuple[str, ...]
    atoms: tuple[CompiledSimpleAtom, ...]


@dataclass(frozen=True, slots=True)
class CompiledSimpleRule:
    head_predicate: str
    head_slots: tuple[int | None, ...]
    head_constants: tuple[object | None, ...]
    matcher: CompiledSimpleMatcher


def compile_simple_matcher(
    ordered_atoms: list[tuple[int, Atom]],
) -> CompiledSimpleMatcher | None:
    slot_indexes: dict[str, int] = {}
    slot_names: list[str] = []
    compiled_atoms: list[CompiledSimpleAtom] = []

    for source_index, atom in ordered_atoms:
        constant_columns: list[int] = []
        constant_values: list[object] = []
        lookup_columns: list[int] = []
        lookup_slots: list[int] = []
        assigned_columns: list[int] = []
        assigned_slots: list[int] = []
        equality_columns: list[int] = []
        equality_slots: list[int] = []
        assigned_this_atom: set[int] = set()

        for column, term in enumerate(atom.terms):
            if isinstance(term, Constant):
                constant_columns.append(column)
                constant_values.append(term.value)
                continue
            if isinstance(term, Wildcard):
                continue
            if not isinstance(term, Variable):
                return None

            slot = slot_indexes.get(term.name)
            if slot is None:
                slot = len(slot_names)
                slot_indexes[term.name] = slot
                slot_names.append(term.name)
                assigned_this_atom.add(slot)
                assigned_columns.append(column)
                assigned_slots.append(slot)
                continue
            if slot in assigned_this_atom:
                equality_columns.append(column)
                equality_slots.append(slot)
                continue
            lookup_columns.append(column)
            lookup_slots.append(slot)

        compiled_atoms.append(
            CompiledSimpleAtom(
                source_index=source_index,
                predicate=atom.predicate,
                lookup_columns=tuple(constant_columns + lookup_columns),
                constant_values=tuple(constant_values),
                lookup_slots=tuple(lookup_slots),
                assigned_columns=tuple(assigned_columns),
                assigned_slots=tuple(assigned_slots),
                equality_columns=tuple(equality_columns),
                equality_slots=tuple(equality_slots),
            )
        )

    return CompiledSimpleMatcher(
        slot_names=tuple(slot_names),
        atoms=tuple(compiled_atoms),
    )


def compile_simple_rule(
    rule: Atom,
    ordered_atoms: list[tuple[int, Atom]],
) -> CompiledSimpleRule | None:
    matcher = compile_simple_matcher(ordered_atoms)
    if matcher is None:
        return None

    head_slots: list[int | None] = []
    head_constants: list[object | None] = []
    slot_indexes = {
        name: index
        for index, name in enumerate(matcher.slot_names)
    }
    for term in rule.terms:
        if isinstance(term, Constant):
            head_slots.append(None)
            head_constants.append(term.value)
            continue
        if not isinstance(term, Variable):
            return None
        slot = slot_indexes.get(term.name)
        if slot is None:
            return None
        head_slots.append(slot)
        head_constants.append(None)

    return CompiledSimpleRule(
        head_predicate=rule.predicate,
        head_slots=tuple(head_slots),
        head_constants=tuple(head_constants),
        matcher=matcher,
    )


def iter_compiled_bindings(
    compiled: CompiledSimpleMatcher,
    model: dict[str, IndexedRelation],
    overrides: dict[int, IndexedRelation],
) -> Iterator[dict[str, object]]:
    slots: list[object] = [_UNBOUND] * len(compiled.slot_names)
    yield from _iter_compiled_matches(compiled, 0, slots, model, overrides)


def _iter_compiled_matches(
    compiled: CompiledSimpleMatcher,
    offset: int,
    slots: list[object],
    model: dict[str, IndexedRelation],
    overrides: dict[int, IndexedRelation],
) -> Iterator[dict[str, object]]:
    if offset >= len(compiled.atoms):
        yield {
            name: slots[index]
            for index, name in enumerate(compiled.slot_names)
        }
        return

    atom = compiled.atoms[offset]
    rows = overrides.get(atom.source_index, model.get(atom.predicate, IndexedRelation()))
    if not rows:
        return

    candidates = rows
    if atom.lookup_columns:
        lookup_values = list(atom.constant_values)
        lookup_values.extend(slots[slot] for slot in atom.lookup_slots)
        candidates = rows.lookup(atom.lookup_columns, tuple(lookup_values))
        if not candidates:
            return

    for row in candidates:
        if not _row_equalities_hold(atom, row, slots):
            continue
        for column, slot in zip(atom.assigned_columns, atom.assigned_slots, strict=True):
            slots[slot] = row[column]
        yield from _iter_compiled_matches(compiled, offset + 1, slots, model, overrides)
        for slot in reversed(atom.assigned_slots):
            slots[slot] = _UNBOUND


def iter_compiled_head_rows(
    compiled: CompiledSimpleRule,
    model: dict[str, IndexedRelation],
    overrides: dict[int, IndexedRelation],
) -> Iterator[tuple[object, ...]]:
    slots: list[object] = [_UNBOUND] * len(compiled.matcher.slot_names)
    yield from _iter_compiled_head_matches(compiled, 0, slots, model, overrides)


def _iter_compiled_head_matches(
    compiled: CompiledSimpleRule,
    offset: int,
    slots: list[object],
    model: dict[str, IndexedRelation],
    overrides: dict[int, IndexedRelation],
) -> Iterator[tuple[object, ...]]:
    if offset >= len(compiled.matcher.atoms):
        yield tuple(
            slots[slot] if slot is not None else constant
            for slot, constant in zip(compiled.head_slots, compiled.head_constants, strict=True)
        )
        return

    atom = compiled.matcher.atoms[offset]
    rows = overrides.get(atom.source_index, model.get(atom.predicate, IndexedRelation()))
    if not rows:
        return

    candidates = rows
    if atom.lookup_columns:
        lookup_values = list(atom.constant_values)
        lookup_values.extend(slots[slot] for slot in atom.lookup_slots)
        candidates = rows.lookup(atom.lookup_columns, tuple(lookup_values))
        if not candidates:
            return

    for row in candidates:
        if not _row_equalities_hold(atom, row, slots):
            continue
        for column, slot in zip(atom.assigned_columns, atom.assigned_slots, strict=True):
            slots[slot] = row[column]
        yield from _iter_compiled_head_matches(compiled, offset + 1, slots, model, overrides)
        for slot in reversed(atom.assigned_slots):
            slots[slot] = _UNBOUND


def _row_equalities_hold(
    atom: CompiledSimpleAtom,
    row: tuple[object, ...],
    slots: list[object],
) -> bool:
    for column, slot in zip(atom.equality_columns, atom.equality_slots, strict=True):
        if not values_equal(row[column], slots[slot]):
            return False
    return True
