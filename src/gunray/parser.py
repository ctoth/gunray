"""Parser for the current Gunray Datalog and defeasible rule surface."""

from __future__ import annotations

from ast import literal_eval
from collections.abc import Mapping
from typing import cast

from .errors import ParseError
from .schema import DefeasibleTheory as SchemaDefeasibleTheory
from .schema import PredicateFacts
from .schema import Program as SchemaProgram
from .schema import Rule as SchemaRule
from .semantics import add_values, subtract_values
from .types import (
    AddExpression,
    Atom,
    AtomTerm,
    Comparison,
    Constant,
    DefeasibleRule,
    GroundAtom,
    Rule,
    Scalar,
    SubtractExpression,
    Variable,
    Wildcard,
)


def normalize_facts(
    raw_facts: PredicateFacts,
) -> dict[str, set[tuple[Scalar, ...]]]:
    """Normalize YAML fact rows to a set-based model representation."""

    return {
        predicate: {tuple(_normalize_scalar_value(value) for value in row) for row in rows}
        for predicate, rows in raw_facts.items()
    }


def parse_program(program: SchemaProgram) -> tuple[dict[str, set[tuple[Scalar, ...]]], list[Rule]]:
    """Parse a Gunray program into normalized facts and rules."""

    facts = normalize_facts(program.facts)
    rules = [parse_rule_text(rule_text) for rule_text in program.rules]
    return facts, rules


def parse_defeasible_theory(
    theory: SchemaDefeasibleTheory,
) -> tuple[dict[str, set[tuple[Scalar, ...]]], list[DefeasibleRule], set[tuple[str, str]]]:
    """Parse a Gunray defeasible theory."""

    facts = normalize_facts(theory.facts)
    rules: list[DefeasibleRule] = []

    for item in theory.strict_rules:
        rules.append(parse_defeasible_rule(item, kind="strict"))
    for item in theory.defeasible_rules:
        rules.append(parse_defeasible_rule(item, kind="defeasible"))
    for item in theory.defeaters:
        rules.append(parse_defeasible_rule(item, kind="defeater"))

    conflicts = _collect_conflicts(theory)
    return facts, rules, conflicts


def parse_defeasible_rule(rule: SchemaRule, *, kind: str) -> DefeasibleRule:
    """Parse a structured defeasible rule entry."""

    return DefeasibleRule(
        rule_id=rule.id,
        kind=kind,
        head=parse_atom_text(rule.head),
        body=tuple(parse_atom_text(item) for item in rule.body),
    )


def parse_rule_text(text: str) -> Rule:
    """Parse a standard Datalog rule string."""

    stripped = text.strip()
    if not stripped:
        raise ParseError("Empty rule")

    body_text = ""
    head_text = stripped.removesuffix(".")
    separator_index = _find_top_level_operator(head_text, ":-")
    if separator_index != -1:
        body_text = head_text[separator_index + 2 :]
        head_text = head_text[:separator_index]

    heads = tuple(parse_atom_text(chunk) for chunk in split_top_level(head_text))
    positive_body: list[Atom] = []
    negative_body: list[Atom] = []
    constraints: list[Comparison] = []

    if body_text.strip():
        for item in split_top_level(body_text):
            candidate = item.strip()
            if candidate.startswith("not "):
                negative_body.append(parse_atom_text(candidate[4:].strip()))
            elif _is_constraint(candidate):
                constraints.append(parse_constraint_text(candidate))
            else:
                positive_body.append(parse_atom_text(candidate))

    return Rule(
        heads=heads,
        positive_body=tuple(positive_body),
        negative_body=tuple(negative_body),
        constraints=tuple(constraints),
        source_text=stripped,
    )


def parse_atom_text(text: str) -> Atom:
    """Parse an atom like `p(X, Y)` or `~q`."""

    stripped = text.strip()
    if not stripped:
        raise ParseError("Empty atom")

    bounds = _find_atom_argument_bounds(stripped)
    if bounds is None:
        return Atom(predicate=stripped, terms=())

    open_index, close_index = bounds
    if open_index <= 0 or close_index < open_index:
        raise ParseError(f"Unsupported atom syntax: {text}")

    predicate = stripped[:open_index].strip()
    inner = stripped[open_index + 1 : close_index].strip()
    if not predicate:
        raise ParseError(f"Missing predicate name: {text}")
    if not inner:
        return Atom(predicate=predicate, terms=())

    return Atom(
        predicate=predicate,
        terms=tuple(parse_term_text(item) for item in split_top_level(inner)),
    )


def parse_term_text(text: str) -> AtomTerm:
    """Parse a rule term, including simple addition expressions."""

    stripped = text.strip()
    if not stripped:
        raise ParseError("Empty term")

    if stripped == "_" or stripped.startswith("_"):
        return Wildcard(token=stripped)

    plus_index = _find_top_level_binary(stripped, "+")
    if plus_index != -1:
        left = stripped[:plus_index]
        right = stripped[plus_index + 1 :]
        return AddExpression(left=parse_value_term(left), right=parse_value_term(right))

    return parse_value_term(stripped)


def parse_value_term(text: str) -> Variable | Constant | AddExpression | SubtractExpression:
    """Parse a term that can appear in a value-producing position."""

    stripped = text.strip()
    operator_index, operator = _find_rightmost_top_level_binary(stripped, "+-")
    if operator_index != -1 and operator == "+":
        return AddExpression(
            left=parse_value_term(stripped[:operator_index]),
            right=parse_value_term(stripped[operator_index + 1 :]),
        )
    if operator_index != -1 and operator == "-":
        return SubtractExpression(
            left=parse_value_term(stripped[:operator_index]),
            right=parse_value_term(stripped[operator_index + 1 :]),
        )

    scalar = _parse_scalar(stripped)
    if scalar is not None:
        return Constant(value=scalar)
    return Variable(name=stripped)


def parse_constraint_text(text: str) -> Comparison:
    """Parse a comparison literal like `(n <= 25)`."""

    stripped = text.strip()
    if stripped.startswith("(") and stripped.endswith(")"):
        stripped = stripped[1:-1].strip()

    for operator in ("<=", ">=", "==", "!=", "<", ">"):
        index = _find_top_level_operator(stripped, operator)
        if index != -1:
            left = stripped[:index]
            right = stripped[index + len(operator) :]
            return Comparison(
                left=parse_value_term(left),
                operator=operator,
                right=parse_value_term(right),
            )
    raise ParseError(f"Unsupported comparison literal: {text}")


def split_top_level(text: str) -> list[str]:
    """Split a comma-separated sequence while respecting nesting and quotes."""

    top_level_mask = _scan_top_level_mask(text)
    items: list[str] = []
    current: list[str] = []

    for index, character in enumerate(text):
        if character == "," and top_level_mask[index]:
            item = "".join(current).strip()
            if item:
                items.append(item)
            current = []
            continue
        current.append(character)

    tail = "".join(current).strip()
    if tail:
        items.append(tail)
    return items


def ground_atom(atom: Atom, binding: Mapping[str, object]) -> GroundAtom:
    """Instantiate a parsed atom under a binding."""

    return GroundAtom(
        predicate=atom.predicate,
        arguments=tuple(evaluate_term(term, binding) for term in atom.terms),
    )


def evaluate_term(term: AtomTerm, binding: Mapping[str, object]) -> Scalar:
    """Evaluate a head/body term under a concrete variable binding."""

    if isinstance(term, Constant):
        return term.value
    if isinstance(term, Variable):
        return cast(Scalar, binding[term.name])
    if isinstance(term, Wildcard):
        raise KeyError(f"Wildcard term {term.token!r} cannot be evaluated as a value")

    left = evaluate_term(term.left, binding)
    right = evaluate_term(term.right, binding)
    if isinstance(term, SubtractExpression):
        return subtract_values(left, right)
    return add_values(left, right)


def _collect_conflicts(theory: SchemaDefeasibleTheory) -> set[tuple[str, str]]:
    conflicts: set[tuple[str, str]] = set()
    for left, right in theory.conflicts:
        conflicts.add((left, right))
        conflicts.add((right, left))

    predicates = set(theory.facts)
    for rule in theory.strict_rules:
        predicates.add(parse_atom_text(rule.head).predicate)
    for rule in theory.defeasible_rules:
        predicates.add(parse_atom_text(rule.head).predicate)
    for rule in theory.defeaters:
        predicates.add(parse_atom_text(rule.head).predicate)

    for predicate in predicates:
        complement = _complement(predicate)
        if complement is not None:
            conflicts.add((predicate, complement))
            conflicts.add((complement, predicate))

    return conflicts


def _complement(predicate: str) -> str | None:
    if predicate.startswith("~"):
        return predicate[1:]
    if predicate:
        return f"~{predicate}"
    return None


def _find_top_level_binary(text: str, operator: str) -> int:
    index, _ = _find_top_level_token(
        text,
        (operator,),
        require_left_operand=True,
    )
    return index


def _find_rightmost_top_level_binary(text: str, operators: str) -> tuple[int, str | None]:
    return _find_top_level_token(
        text,
        tuple(operators),
        from_right=True,
        require_left_operand=True,
    )


def _find_top_level_operator(text: str, operator: str) -> int:
    index, _ = _find_top_level_token(text, (operator,))
    return index


def _is_constraint(text: str) -> bool:
    stripped = text.strip()
    if stripped.startswith("(") and stripped.endswith(")"):
        stripped = stripped[1:-1].strip()
    operators = ("<=", ">=", "==", "!=", "<", ">")
    return any(_find_top_level_operator(stripped, operator) != -1 for operator in operators)


def _find_atom_argument_bounds(text: str) -> tuple[int, int] | None:
    _scan_top_level_mask(text)
    open_index = text.find("(")
    if open_index == -1:
        return None

    close_index = text.rfind(")")
    if close_index != len(text) - 1:
        raise ParseError(f"Unsupported atom syntax: {text}")
    return open_index, close_index


def _find_top_level_token(
    text: str,
    tokens: tuple[str, ...],
    *,
    from_right: bool = False,
    require_left_operand: bool = False,
) -> tuple[int, str | None]:
    top_level_mask = _scan_top_level_mask(text)
    ordered_tokens = tuple(sorted(tokens, key=len, reverse=True))
    indexes = range(len(text) - 1, -1, -1) if from_right else range(len(text))

    for index in indexes:
        if not top_level_mask[index]:
            continue
        if require_left_operand and index == 0:
            continue
        for token in ordered_tokens:
            if text.startswith(token, index):
                return index, token
    return -1, None


def _scan_top_level_mask(text: str) -> tuple[bool, ...]:
    top_level: list[bool] = []
    depth = 0
    in_string = False
    escaped = False

    for character in text:
        top_level.append(not in_string and depth == 0)
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
            continue
        if character == "(":
            depth += 1
            continue
        if character == ")":
            depth -= 1
            if depth < 0:
                raise ParseError(f"Unbalanced parentheses: {text}")

    if in_string:
        raise ParseError(f"Unterminated string literal: {text}")
    if depth != 0:
        raise ParseError(f"Unbalanced parentheses: {text}")
    return tuple(top_level)


def _parse_scalar(text: str) -> Scalar | None:
    if not text:
        return None
    if text.startswith('"') and text.endswith('"'):
        parsed = literal_eval(text)
        if not isinstance(parsed, str):
            raise ParseError(f"Expected quoted string literal, got {text}")
        return parsed
    return _parse_unquoted_scalar(text)


def _normalize_scalar_value(value: Scalar) -> Scalar:
    return value


def _parse_unquoted_scalar(text: str) -> Scalar | None:
    if text == "true":
        return True
    if text == "false":
        return False
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        return None
