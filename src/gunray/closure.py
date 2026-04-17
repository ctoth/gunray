"""Reduced symbolic closure operators for Gunray's zero-arity fragment.

The implementation follows the ranking / exceptionality structure of Morris,
Ross, and Meyer 2020 (Algorithms 3-5, pp. 150-153) but specializes it to the
current zero-arity Horn-like literal surface used by Gunray. This removes the
old `2^n` world enumeration path while keeping the existing Formula/test API.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from itertools import combinations
from typing import TypeVar

from .schema import DefeasibleModel, DefeasibleTheory, Policy, Rule
from .trace import DefeasibleTrace, TraceConfig
from .types import GroundAtom

World = frozenset[str]
RankScore = int | tuple[int, ...]
RankScoreT = TypeVar("RankScoreT", int, tuple[int, ...])


@dataclass(frozen=True, slots=True)
class RankedDefaults:
    """Ranked propositional default theory."""

    atoms: tuple[str, ...]
    finite_ranks: tuple[tuple[Rule, ...], ...]
    infinite_rank: tuple[Rule, ...]


ScoreFunction = Callable[[RankedDefaults, World], RankScoreT]


@dataclass(frozen=True, slots=True)
class Formula:
    """Reduced zero-arity formula language for current closure tests."""

    kind: str
    literal: str | None = None
    left: "Formula | None" = None
    right: "Formula | None" = None


class ClosureEvaluator:
    """Evaluate the current reduced closure fragment."""

    def evaluate(self, theory: DefeasibleTheory, policy: Policy) -> DefeasibleModel:
        model, _ = self.evaluate_with_trace(theory, policy)
        return model

    def evaluate_with_trace(
        self,
        theory: DefeasibleTheory,
        policy: Policy,
        trace_config: TraceConfig | None = None,
    ) -> tuple[DefeasibleModel, DefeasibleTrace]:
        if policy not in {
            Policy.RATIONAL_CLOSURE,
            Policy.LEXICOGRAPHIC_CLOSURE,
            Policy.RELEVANT_CLOSURE,
        }:
            raise ValueError(f"Unsupported closure policy: {policy.value}")

        _ensure_propositional(theory)
        ranked = _ranked_defaults(theory)
        facts = _fact_literals(theory)
        definite = _strict_closure(facts, theory.strict_rules)
        literals = _literal_universe(theory)

        defeasible = {
            literal
            for literal in literals
            if _closure_entails(ranked, theory, facts, literal, policy)
        }
        defeasible.update(definite)
        not_defeasible = literals - defeasible

        sections: dict[str, dict[str, set[tuple[()]]]] = {}
        if definite:
            sections["definitely"] = _atoms_to_section(definite)
        if defeasible:
            sections["defeasibly"] = _atoms_to_section(defeasible)
        if not_defeasible:
            sections["not_defeasibly"] = _atoms_to_section(not_defeasible)

        trace = DefeasibleTrace(config=trace_config or TraceConfig())
        trace.definitely = tuple(_ground_atoms_from_literals(definite))
        trace.supported = tuple(_ground_atoms_from_literals(defeasible))
        return DefeasibleModel(sections=sections), trace

    def satisfies_klm_property(
        self,
        theory: DefeasibleTheory,
        property_name: str,
        policy: Policy,
    ) -> bool:
        if property_name != "Or":
            raise ValueError(f"Unsupported KLM property: {property_name}")
        if policy not in {
            Policy.RATIONAL_CLOSURE,
            Policy.LEXICOGRAPHIC_CLOSURE,
            Policy.RELEVANT_CLOSURE,
        }:
            raise ValueError(f"Unsupported closure policy: {policy.value}")

        _ensure_propositional(theory)
        ranked = _ranked_defaults(theory)
        literals = sorted(_literal_universe(theory))

        for left_literal in literals:
            left = _literal_formula(left_literal)
            for right_literal in literals:
                right = _literal_formula(right_literal)
                disjunction = _or_formula(left, right)
                for consequent_literal in literals:
                    consequent = _literal_formula(consequent_literal)
                    if not _formula_entails(ranked, theory, left, consequent, policy):
                        continue
                    if not _formula_entails(ranked, theory, right, consequent, policy):
                        continue
                    if not _formula_entails(ranked, theory, disjunction, consequent, policy):
                        return False
        return True


def _ensure_propositional(theory: DefeasibleTheory) -> None:
    if theory.defeaters:
        raise ValueError("Closure evaluator does not support defeaters")
    if theory.superiority:
        raise ValueError("Closure evaluator does not support superiority")
    if theory.conflicts:
        raise ValueError("Closure evaluator does not support explicit conflict sets")

    for predicate, rows in theory.facts.items():
        for row in rows:
            if tuple(row) != ():
                raise ValueError(
                    f"Closure evaluator expects zero-arity facts, got {predicate}{tuple(row)!r}"
                )
    for collection in (theory.strict_rules, theory.defeasible_rules):
        for rule in collection:
            _ensure_zero_arity_literal(rule.head)
            for item in rule.body:
                _ensure_zero_arity_literal(item)


def _ensure_zero_arity_literal(text: str) -> None:
    if "(" in text or ")" in text:
        raise ValueError(f"Closure evaluator expects zero-arity literals, got {text!r}")


def _ranked_defaults(theory: DefeasibleTheory) -> RankedDefaults:
    """Partition defaults by exceptionality without enumerating worlds.

    Morris, Ross, and Meyer 2020 Algorithm 3 (p. 150 / local
    ``page-009.png``): BaseRankDatalog repeatedly removes the defeasible
    rules whose antecedents are still satisfiable against the current
    classical-plus-defeasible theory, leaving the permanently exceptional
    defaults at infinite rank.
    """

    atoms = tuple(sorted(_positive_atoms(theory)))
    remaining: list[Rule] = list(theory.defeasible_rules)
    finite_ranks: list[tuple[Rule, ...]] = []
    while remaining:
        active_rules: list[Rule] = [*theory.strict_rules, *remaining]
        current_rank_items = [
            rule for rule in remaining if _branch_satisfiable(frozenset(rule.body), active_rules)
        ]
        current_rank = tuple(current_rank_items)
        if not current_rank:
            break
        current_ids = {rule.id for rule in current_rank}
        finite_ranks.append(current_rank)
        remaining = [rule for rule in remaining if rule.id not in current_ids]

    return RankedDefaults(
        atoms=atoms,
        finite_ranks=tuple(finite_ranks),
        infinite_rank=tuple(remaining),
    )


def _positive_atoms(theory: DefeasibleTheory) -> set[str]:
    atoms = {_positive_atom(predicate) for predicate, rows in theory.facts.items() if rows}
    for collection in (theory.strict_rules, theory.defeasible_rules):
        for rule in collection:
            atoms.add(_positive_atom(rule.head))
            atoms.update(_positive_atom(item) for item in rule.body)
    return atoms


def _literal_universe(theory: DefeasibleTheory) -> set[str]:
    atoms = _positive_atoms(theory)
    return {literal for atom in atoms for literal in (atom, _complement(atom))}


def _fact_literals(theory: DefeasibleTheory) -> set[str]:
    return {predicate for predicate, rows in theory.facts.items() if rows}


def _strict_closure(facts: set[str], strict_rules: list[Rule]) -> set[str]:
    closure = set(facts)
    changed = True
    while changed:
        changed = False
        for rule in strict_rules:
            if rule.head in closure:
                continue
            if set(rule.body) <= closure:
                closure.add(rule.head)
                changed = True
    return closure


def _closure_entails(
    ranked: RankedDefaults,
    theory: DefeasibleTheory,
    facts: set[str],
    query: str,
    policy: Policy,
) -> bool:
    antecedent = _conjunction_formula(sorted(facts))
    consequent = _literal_formula(query)
    return _formula_entails(ranked, theory, antecedent, consequent, policy)


def _formula_entails(
    ranked: RankedDefaults,
    theory: DefeasibleTheory,
    antecedent: Formula,
    consequent: Formula,
    policy: Policy,
) -> bool:
    if policy is Policy.RATIONAL_CLOSURE:
        return _rational_formula_entails(ranked, theory, antecedent, consequent)
    if policy is Policy.LEXICOGRAPHIC_CLOSURE:
        return _lexicographic_formula_entails(ranked, theory, antecedent, consequent)
    if policy is Policy.RELEVANT_CLOSURE:
        return _relevant_formula_entails(ranked, theory, antecedent, consequent)
    raise ValueError(f"Unsupported closure policy: {policy.value}")


def _rational_formula_entails(
    ranked: RankedDefaults,
    theory: DefeasibleTheory,
    antecedent: Formula,
    consequent: Formula,
) -> bool:
    """Morris, Ross, and Meyer 2020 Algorithm 4 (p. 151 / ``page-010.png``)."""

    return _ranked_formula_entails(
        ranked,
        theory,
        antecedent,
        consequent,
        score=_rational_score,
    )


def _lexicographic_formula_entails(
    ranked: RankedDefaults,
    theory: DefeasibleTheory,
    antecedent: Formula,
    consequent: Formula,
) -> bool:
    """Morris, Ross, and Meyer 2020 subset-ranking semantics (pp.156-158)."""

    return _ranked_formula_entails(
        ranked,
        theory,
        antecedent,
        consequent,
        score=_lexicographic_score,
    )


def _ranked_formula_entails(
    ranked: RankedDefaults,
    theory: DefeasibleTheory,
    antecedent: Formula,
    consequent: Formula,
    *,
    score: ScoreFunction[RankScoreT],
) -> bool:
    atoms = _atoms_for_rules_and_formulas(
        [*theory.strict_rules, *theory.defeasible_rules],
        antecedent,
        consequent,
    )
    strict_rules = list(theory.strict_rules)
    any_context = False
    best_score: RankScoreT | None = None
    countermodel_at_best = False

    def visit(assignment: dict[str, bool]) -> None:
        nonlocal any_context
        nonlocal best_score
        nonlocal countermodel_at_best

        propagated = _propagate_assignment(strict_rules, assignment)
        if propagated is None:
            return

        antecedent_status = _formula_status(antecedent, propagated)
        if antecedent_status is False:
            return

        unassigned = next((atom for atom in atoms if atom not in propagated), None)
        if unassigned is not None:
            for value in (False, True):
                next_assignment = dict(propagated)
                next_assignment[unassigned] = value
                visit(next_assignment)
            return

        if antecedent_status is not True:
            return

        any_context = True
        world: World = frozenset(atom for atom, value in propagated.items() if value)
        world_score = score(ranked, world)
        consequent_holds = _formula_holds(world, consequent)
        if best_score is None or world_score < best_score:
            best_score = world_score
            countermodel_at_best = not consequent_holds
            return
        if world_score == best_score and not consequent_holds:
            countermodel_at_best = True

    visit({})
    if not any_context:
        return _classically_entails(
            theory.strict_rules,
            list(theory.defeasible_rules),
            antecedent,
            consequent,
        )
    return not countermodel_at_best


def _relevant_formula_entails(
    ranked: RankedDefaults,
    theory: DefeasibleTheory,
    antecedent: Formula,
    consequent: Formula,
) -> bool:
    relevant_ids = _minimal_relevant_rule_ids(ranked, theory, antecedent)
    active_defaults = list(theory.defeasible_rules)

    for level in ranked.finite_ranks:
        if not _is_exceptional(theory.strict_rules, active_defaults, antecedent):
            break
        active_defaults = [
            rule for rule in active_defaults if rule.id not in relevant_ids or rule not in level
        ]

    return _classically_entails(theory.strict_rules, active_defaults, antecedent, consequent)


def _lexicographic_preferred_default_sets(
    ranked: RankedDefaults,
    theory: DefeasibleTheory,
    antecedent: Formula,
) -> list[list[Rule]]:
    """Return the lexicographically preferred default sets for ``antecedent``.

    Each iteration keeps only the largest subsets of the current rank that
    remain satisfiable together with the already retained more-exceptional
    defaults. This matches the subset-ranking intent of Morris et al. 2020
    without enumerating truth-table worlds.
    """

    selected_sets: list[tuple[Rule, ...]] = [tuple(ranked.infinite_rank)]
    for level in reversed(ranked.finite_ranks):
        next_sets: list[tuple[Rule, ...]] = []
        best_size = -1
        seen: set[tuple[str, ...]] = set()
        level_items = tuple(level)

        for selected in selected_sets:
            satisfiable_subsets: list[tuple[Rule, ...]] = []
            chosen_size = -1
            for size in range(len(level_items), -1, -1):
                current = [
                    subset
                    for subset in combinations(level_items, size)
                    if _is_formula_possible(
                        theory.strict_rules,
                        list(selected) + list(subset),
                        antecedent,
                    )
                ]
                if current:
                    satisfiable_subsets = current
                    chosen_size = size
                    break

            if chosen_size < best_size:
                continue
            if chosen_size > best_size:
                best_size = chosen_size
                next_sets = []
                seen.clear()

            for subset in satisfiable_subsets:
                combined = tuple(sorted((*selected, *subset), key=lambda rule: rule.id))
                key = tuple(rule.id for rule in combined)
                if key in seen:
                    continue
                seen.add(key)
                next_sets.append(combined)

        if next_sets:
            selected_sets = next_sets

    return [list(selected) for selected in selected_sets]


def _minimal_relevant_rule_ids(
    ranked: RankedDefaults,
    theory: DefeasibleTheory,
    antecedent: Formula,
) -> set[str]:
    defaults = list(theory.defeasible_rules)
    justifications: list[tuple[Rule, ...]] = []

    for size in range(1, len(defaults) + 1):
        for subset in combinations(defaults, size):
            subset_ids = {rule.id for rule in subset}
            if any(
                {rule.id for rule in existing}.issubset(subset_ids) for existing in justifications
            ):
                continue
            if not _is_exceptional(theory.strict_rules, list(subset), antecedent):
                continue
            justifications.append(subset)

    relevant_ids: set[str] = set()
    for justification in justifications:
        min_rank = min(_rule_rank(ranked, rule) for rule in justification)
        relevant_ids.update(
            rule.id for rule in justification if _rule_rank(ranked, rule) == min_rank
        )
    return relevant_ids


def _rule_rank(ranked: RankedDefaults, target: Rule) -> int:
    for index, level in enumerate(ranked.finite_ranks):
        if any(rule.id == target.id for rule in level):
            return index
    return len(ranked.finite_ranks)


def _is_exceptional(
    strict_rules: list[Rule],
    defaults: list[Rule],
    antecedent: Formula,
) -> bool:
    return not _is_formula_possible(strict_rules, defaults, antecedent)


def _is_formula_possible(
    strict_rules: list[Rule],
    defaults: list[Rule],
    antecedent: Formula,
) -> bool:
    rules = [*strict_rules, *defaults]
    atoms = _atoms_for_rules_and_formulas(rules, antecedent)
    return _model_exists(atoms, rules, antecedent, forbidden_consequent=None)


def _classically_entails(
    strict_rules: list[Rule],
    defaults: list[Rule],
    antecedent: Formula,
    consequent: Formula,
) -> bool:
    rules = [*strict_rules, *defaults]
    atoms = _atoms_for_rules_and_formulas(rules, antecedent, consequent)
    return not _model_exists(atoms, rules, antecedent, forbidden_consequent=consequent)


def _atoms_for_rules_and_formulas(
    rules: list[Rule],
    *formulae: Formula,
) -> tuple[str, ...]:
    atoms: set[str] = set()
    for rule in rules:
        atoms.add(_positive_atom(rule.head))
        atoms.update(_positive_atom(item) for item in rule.body)
    for formula in formulae:
        atoms.update(_formula_atoms(formula))
    return tuple(sorted(atoms))


def _formula_atoms(formula: Formula) -> set[str]:
    if formula.kind == "true":
        return set()
    if formula.kind == "literal":
        assert formula.literal is not None
        return {_positive_atom(formula.literal)}
    if formula.kind in {"and", "or"}:
        assert formula.left is not None
        assert formula.right is not None
        return _formula_atoms(formula.left) | _formula_atoms(formula.right)
    raise ValueError(f"Unsupported formula kind: {formula.kind}")


def _model_exists(
    atoms: tuple[str, ...],
    rules: list[Rule],
    antecedent: Formula,
    *,
    forbidden_consequent: Formula | None,
) -> bool:
    return _search_model(
        atoms,
        rules,
        antecedent,
        forbidden_consequent,
        assignment={},
    )


def _search_model(
    atoms: tuple[str, ...],
    rules: list[Rule],
    antecedent: Formula,
    forbidden_consequent: Formula | None,
    *,
    assignment: dict[str, bool],
) -> bool:
    propagated = _propagate_assignment(rules, assignment)
    if propagated is None:
        return False

    antecedent_status = _formula_status(antecedent, propagated)
    if antecedent_status is False:
        return False

    if forbidden_consequent is not None:
        consequent_status = _formula_status(forbidden_consequent, propagated)
        if antecedent_status is True and consequent_status is True:
            return False

    unassigned = next((atom for atom in atoms if atom not in propagated), None)
    if unassigned is None:
        if antecedent_status is not True:
            return False
        if forbidden_consequent is None:
            return True
        return _formula_status(forbidden_consequent, propagated) is False

    for value in (False, True):
        next_assignment = dict(propagated)
        next_assignment[unassigned] = value
        if _search_model(
            atoms,
            rules,
            antecedent,
            forbidden_consequent,
            assignment=next_assignment,
        ):
            return True
    return False


def _propagate_assignment(
    rules: list[Rule],
    assignment: dict[str, bool],
) -> dict[str, bool] | None:
    current = dict(assignment)
    changed = True
    while changed:
        changed = False
        for rule in rules:
            body_statuses = [_literal_status(item, current) for item in rule.body]
            if any(status is False for status in body_statuses):
                continue
            if any(status is None for status in body_statuses):
                continue
            forced = _force_literal(rule.head, current)
            if forced is None:
                return None
            changed = changed or forced
    return current


def _force_literal(literal: str, assignment: dict[str, bool]) -> bool | None:
    atom = _positive_atom(literal)
    value = not literal.startswith("~")
    existing = assignment.get(atom)
    if existing is not None:
        if existing is not value:
            return None
        return False
    assignment[atom] = value
    return True


def _literal_status(literal: str, assignment: dict[str, bool]) -> bool | None:
    atom = _positive_atom(literal)
    value = assignment.get(atom)
    if value is None:
        return None
    return not value if literal.startswith("~") else value


def _formula_status(formula: Formula, assignment: dict[str, bool]) -> bool | None:
    if formula.kind == "true":
        return True
    if formula.kind == "literal":
        assert formula.literal is not None
        return _literal_status(formula.literal, assignment)
    if formula.kind == "and":
        assert formula.left is not None
        assert formula.right is not None
        left = _formula_status(formula.left, assignment)
        right = _formula_status(formula.right, assignment)
        if left is False or right is False:
            return False
        if left is True and right is True:
            return True
        return None
    if formula.kind == "or":
        assert formula.left is not None
        assert formula.right is not None
        left = _formula_status(formula.left, assignment)
        right = _formula_status(formula.right, assignment)
        if left is True or right is True:
            return True
        if left is False and right is False:
            return False
        return None
    raise ValueError(f"Unsupported formula kind: {formula.kind}")


def _branch_satisfiable(
    branch: frozenset[str],
    rules: list[Rule],
) -> bool:
    return _is_formula_possible([], rules, _conjunction_formula(sorted(branch)))


def _branch_closure(
    branch: frozenset[str],
    rules: list[Rule],
) -> set[str]:
    closure = set(branch)
    changed = True
    while changed:
        changed = False
        for rule in rules:
            if rule.head in closure:
                continue
            if set(rule.body) <= closure:
                closure.add(rule.head)
                changed = True
    return closure


def _is_consistent(literals: set[str]) -> bool:
    return all(_complement(literal) not in literals for literal in literals)


def _formula_branches(formula: Formula) -> tuple[frozenset[str], ...]:
    """Convert Formula to a deduplicated DNF branch list.

    Gunray's closure tests only use literals, conjunctions, disjunctions, and
    `true`, so a direct branch expansion is simpler than general SAT encoding.
    """

    if formula.kind == "true":
        return (frozenset(),)
    if formula.kind == "literal":
        assert formula.literal is not None
        return (frozenset({formula.literal}),)
    if formula.kind == "and":
        assert formula.left is not None
        assert formula.right is not None
        branches: set[frozenset[str]] = set()
        for left in _formula_branches(formula.left):
            for right in _formula_branches(formula.right):
                branches.add(left | right)
        return tuple(sorted(branches, key=lambda branch: tuple(sorted(branch))))
    if formula.kind == "or":
        assert formula.left is not None
        assert formula.right is not None
        branches = set(_formula_branches(formula.left))
        branches.update(_formula_branches(formula.right))
        return tuple(sorted(branches, key=lambda branch: tuple(sorted(branch))))
    raise ValueError(f"Unsupported formula kind: {formula.kind}")


def _formula_holds(world: World, formula: Formula) -> bool:
    if formula.kind == "true":
        return True
    if formula.kind == "literal":
        assert formula.literal is not None
        return _literal_holds(world, formula.literal)
    if formula.kind == "and":
        assert formula.left is not None
        assert formula.right is not None
        return _formula_holds(world, formula.left) and _formula_holds(world, formula.right)
    if formula.kind == "or":
        assert formula.left is not None
        assert formula.right is not None
        return _formula_holds(world, formula.left) or _formula_holds(world, formula.right)
    raise ValueError(f"Unsupported formula kind: {formula.kind}")


def _formula_true_in_closure(formula: Formula, closure: set[str]) -> bool:
    if formula.kind == "true":
        return True
    if formula.kind == "literal":
        assert formula.literal is not None
        if formula.literal.startswith("~"):
            # The reduced closure fragment still uses the paper's two-valued
            # world semantics: a negative literal holds exactly when its
            # positive atom is absent from the current world/closure state.
            return formula.literal[1:] not in closure
        return formula.literal in closure
    if formula.kind == "and":
        assert formula.left is not None
        assert formula.right is not None
        return _formula_true_in_closure(formula.left, closure) and _formula_true_in_closure(
            formula.right, closure
        )
    if formula.kind == "or":
        assert formula.left is not None
        assert formula.right is not None
        return _formula_true_in_closure(formula.left, closure) or _formula_true_in_closure(
            formula.right, closure
        )
    raise ValueError(f"Unsupported formula kind: {formula.kind}")


def _literal_formula(literal: str) -> Formula:
    return Formula(kind="literal", literal=literal)


def _conjunction_formula(literals: list[str]) -> Formula:
    if not literals:
        return Formula(kind="true")
    formula = _literal_formula(literals[0])
    for literal in literals[1:]:
        formula = Formula(kind="and", left=formula, right=_literal_formula(literal))
    return formula


def _or_formula(left: Formula, right: Formula) -> Formula:
    return Formula(kind="or", left=left, right=right)


def _rational_score(ranked: RankedDefaults, world: World) -> int:
    if any(_violates(world, rule) for rule in ranked.infinite_rank):
        return len(ranked.finite_ranks) + 1

    worst_rank = -1
    for index, level in enumerate(ranked.finite_ranks):
        if any(_violates(world, rule) for rule in level):
            worst_rank = index
    return worst_rank + 1


def _lexicographic_score(ranked: RankedDefaults, world: World) -> tuple[int, ...]:
    if any(_violates(world, rule) for rule in ranked.infinite_rank):
        width = max(len(ranked.finite_ranks), 1)
        worst = len(ranked.infinite_rank) + sum(len(level) for level in ranked.finite_ranks) + 1
        return tuple(worst for _ in range(width))

    return tuple(
        sum(1 for rule in level if _violates(world, rule))
        for level in reversed(ranked.finite_ranks)
    )


def _world_satisfies_rules(world: World, rules: list[Rule]) -> bool:
    return all(
        not _world_satisfies_literals(world, set(rule.body)) or _literal_holds(world, rule.head)
        for rule in rules
    )


def _world_satisfies_literals(world: World, literals: set[str]) -> bool:
    return all(_literal_holds(world, literal) for literal in literals)


def _literal_holds(world: World, literal: str) -> bool:
    positive = _positive_atom(literal)
    if literal.startswith("~"):
        return positive not in world
    return positive in world


def _violates(world: World, rule: Rule) -> bool:
    return _world_satisfies_literals(world, set(rule.body)) and not _literal_holds(world, rule.head)


def _atoms_to_section(atoms: set[str]) -> dict[str, set[tuple[()]]]:
    return {atom: {()} for atom in sorted(atoms)}


def _ground_atoms_from_literals(literals: set[str]) -> list[GroundAtom]:
    return [GroundAtom(predicate=literal, arguments=()) for literal in sorted(literals)]


def _positive_atom(literal: str) -> str:
    return literal[1:] if literal.startswith("~") else literal


def _complement(literal: str) -> str:
    if literal.startswith("~"):
        return literal[1:]
    return f"~{literal}"
