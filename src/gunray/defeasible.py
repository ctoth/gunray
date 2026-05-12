"""Defeasible evaluator — argument / dialectical-tree pipeline.

Implements the Garcia & Simari 2004 §5 pipeline verbatim:

- Argument structures ⟨A, h⟩ (Def 3.1) are enumerated by
  ``gunray.arguments.build_arguments``.
- Counter-argument at sub-argument (Def 3.4), proper defeater
  (Def 4.1), and blocking defeater (Def 4.2) are implemented in
  ``gunray.dialectic``.
- Dialectical trees (Def 5.1) are built with the Def 4.7
  acceptable-argumentation-line conditions (concordance,
  sub-argument exclusion, block-on-block ban) enforced during
  construction.
- U/D marking follows Procedure 5.1.
- The four-valued answer (Def 5.3, Garcia & Simari 2004 p. 120)
  projects into ``DefeasibleModel.sections`` with the four answer
  keys ``yes`` / ``no`` / ``undecided`` / ``unknown``.

The preference criterion is
``CompositePreference(SuperiorityPreference, GeneralizedSpecificity)``:
explicit user superiority (Garcia 04 §4.1) takes precedence over
generalized specificity (Simari 92 Lemma 2.4) via
first-criterion-to-fire composition.

Strict-only theories route around the argument pipeline via
``_is_strict_only_theory`` and ``SemiNaiveEvaluator`` for performance.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Literal

from ._internal import _atom_sort_key, _strict_rule_to_program_text
from .anytime import EnumerationExceeded
from .arguments import build_arguments
from .closure import ClosureEvaluator
from .disagreement import complement
from .errors import ContradictoryStrictTheoryError
from .evaluator import SemiNaiveEvaluator
from .grounding import inspect_grounding, simplified_ground_theory
from .schema import (
    ClosurePolicy,
    DefeasibleModel,
    FactTuple,
    GroundingMode,
    MarkingPolicy,
    ModelFacts,
    NegationSemantics,
    ProjectionSemantics,
)
from .schema import DefeasibleTheory as SchemaDefeasibleTheory
from .schema import Program as SchemaProgram
from .trace import (
    DatalogTrace,
    DefeasibleTrace,
    TraceConfig,
)
from .types import GroundAtom

if TYPE_CHECKING:  # pragma: no cover - import-time only
    from .arguments import Argument
    from .dialectic import DialecticalNode
    from .grounding_types import GroundingInspection
    from .preference import PreferenceCriterion
    from .types import GroundDefeasibleRule


class DefeasibleEvaluator:
    """Evaluate defeasible theories under Gunray's supported semantics."""

    def evaluate(
        self,
        theory: SchemaDefeasibleTheory,
        *,
        marking_policy: MarkingPolicy = MarkingPolicy.BLOCKING,
        closure_policy: ClosurePolicy | None = None,
        grounding_mode: GroundingMode = GroundingMode.DIRECT,
        negation_semantics: NegationSemantics = NegationSemantics.SAFE,
        projection_semantics: ProjectionSemantics = ProjectionSemantics.GARCIA,
        max_arguments: int | None = None,
    ) -> DefeasibleModel:
        try:
            model, _ = self.evaluate_with_trace(
                theory,
                marking_policy=marking_policy,
                closure_policy=closure_policy,
                grounding_mode=grounding_mode,
                negation_semantics=negation_semantics,
                projection_semantics=projection_semantics,
                max_arguments=max_arguments,
            )
        except EnumerationExceeded as exc:
            exc.partial_trace = None
            raise
        return model

    def evaluate_with_trace(
        self,
        theory: SchemaDefeasibleTheory,
        trace_config: TraceConfig | None = None,
        *,
        marking_policy: MarkingPolicy = MarkingPolicy.BLOCKING,
        closure_policy: ClosurePolicy | None = None,
        grounding_mode: GroundingMode = GroundingMode.DIRECT,
        negation_semantics: NegationSemantics = NegationSemantics.SAFE,
        projection_semantics: ProjectionSemantics = ProjectionSemantics.GARCIA,
        max_arguments: int | None = None,
    ) -> tuple[DefeasibleModel, DefeasibleTrace]:
        if closure_policy is not None:
            if grounding_mode is not GroundingMode.DIRECT:
                raise ValueError("grounding_mode applies only to dialectical-tree evaluation")
            if projection_semantics is not ProjectionSemantics.GARCIA:
                raise ValueError("projection_semantics applies only to defeasible projection")
            return ClosureEvaluator().evaluate_with_trace(
                theory,
                closure_policy,
                trace_config,
            )
        actual_trace_config = trace_config or TraceConfig()
        if marking_policy is MarkingPolicy.ANTONIOU_BLOCKING:
            return _evaluate_antoniou_policy(
                theory,
                actual_trace_config,
                propagate_ambiguity=False,
            )
        if marking_policy is MarkingPolicy.ANTONIOU_PROPAGATING:
            return _evaluate_antoniou_policy(
                theory,
                actual_trace_config,
                propagate_ambiguity=True,
            )
        if marking_policy is not MarkingPolicy.BLOCKING:
            raise ValueError(f"Unsupported marking policy: {marking_policy.value}")
        if projection_semantics is ProjectionSemantics.SPINDLE:
            if grounding_mode is not GroundingMode.DIRECT:
                raise ValueError("SPINdle projection requires direct grounding")
            return _evaluate_spindle_projection(
                theory,
                actual_trace_config,
                max_arguments=max_arguments,
            )
        if projection_semantics is not ProjectionSemantics.GARCIA:
            raise ValueError(f"Unsupported projection semantics: {projection_semantics.value}")

        # Post-Block-2, MarkingPolicy.BLOCKING is the only dialectical-tree
        # policy. Argument preference is resolved by
        # GeneralizedSpecificity (Simari 92 Lemma 2.4).
        if grounding_mode is GroundingMode.DILLER_SIMPLIFIED:
            grounding_inspection = inspect_grounding(theory)
            simplified_theory = simplified_ground_theory(theory, grounding_inspection)
            if _is_strict_only_theory(simplified_theory):
                model, strict_trace = _evaluate_strict_only_theory_with_trace(
                    simplified_theory,
                    actual_trace_config,
                    negation_semantics,
                )
                trace = DefeasibleTrace(config=actual_trace_config)
                trace.strict_trace = strict_trace
                trace.grounding_inspection = grounding_inspection
                trace.strict = tuple(
                    sorted(
                        _section_to_atoms(model.sections.get("yes", {})),
                        key=_atom_sort_key,
                    )
                )
                trace.yes = trace.strict
                _populate_strict_only_argument_view(simplified_theory, trace)
                return model, trace
            return _evaluate_via_argument_pipeline(
                simplified_theory,
                actual_trace_config,
                max_arguments=max_arguments,
                grounding_inspection=grounding_inspection,
                specificity_theory=theory,
            )

        if _is_strict_only_theory(theory):
            model, strict_trace = _evaluate_strict_only_theory_with_trace(
                theory,
                actual_trace_config,
                negation_semantics,
            )
            trace = DefeasibleTrace(config=actual_trace_config)
            trace.strict_trace = strict_trace
            trace.grounding_inspection = inspect_grounding(theory)
            trace.strict = tuple(
                sorted(
                    _section_to_atoms(model.sections.get("yes", {})),
                    key=_atom_sort_key,
                )
            )
            trace.yes = trace.strict
            _populate_strict_only_argument_view(theory, trace)
            return model, trace

        return _evaluate_via_argument_pipeline(
            theory,
            actual_trace_config,
            max_arguments=max_arguments,
        )


def _evaluate_via_argument_pipeline(
    theory: SchemaDefeasibleTheory,
    trace_config: TraceConfig,
    *,
    max_arguments: int | None = None,
    grounding_inspection: GroundingInspection | None = None,
    specificity_theory: SchemaDefeasibleTheory | None = None,
) -> tuple[DefeasibleModel, DefeasibleTrace]:
    """Garcia & Simari 2004 §5 pipeline: enumerate, mark, project.

    Lazy imports break the circular dependency between ``defeasible``
    and ``dialectic``: the dialectical module imports
    ``_atom_sort_key`` from this file at import time.
    """
    from .dialectic import _dialectical_context, _theory_predicates, build_tree, mark
    from .disagreement import complement
    from .preference import (
        CompositePreference,
        GeneralizedSpecificity,
        SuperiorityPreference,
    )

    if grounding_inspection is None:
        grounding_inspection = inspect_grounding(theory)
    try:
        arguments = tuple(
            sorted(
                build_arguments(theory, max_arguments=max_arguments),
                key=_argument_sort_key,
            )
        )
    except EnumerationExceeded as exc:
        trace = DefeasibleTrace(config=trace_config)
        trace.grounding_inspection = grounding_inspection
        trace.arguments = tuple(sorted(exc.partial_arguments, key=_argument_sort_key))
        exc.partial_trace = trace
        raise
    # Composed preference: Garcia & Simari 2004 §4.1 notes that the
    # rule priority criterion (explicit ``superiority`` pairs) and
    # generalized specificity (Lemma 2.4) are modular alternatives.
    # The B2.5 foreman decision is "explicit user-supplied priority
    # wins, otherwise fall through to specificity" — encoded as the
    # any-wins ``CompositePreference``. Both child criteria cache
    # their per-theory state at construction; the composite itself is
    # a thin delegator.
    criterion = CompositePreference(
        SuperiorityPreference(theory),
        GeneralizedSpecificity(specificity_theory or theory),
    )
    predicates = _theory_predicates(theory)
    dialectical_context = _dialectical_context(theory)
    concordance_cache: dict[frozenset["GroundDefeasibleRule"], bool] = {}

    # Defeater-kind arguments exist in the argument universe (so they
    # can attack in the dialectical tree) but do not warrant anything:
    # a defeater rule is a pure attacker in the Nute/Antoniou reading
    # (``notes/b2_defeater_participation.md``). We therefore exclude
    # them here when computing ``warranted`` and separately track the
    # atoms they probe so the section projection can classify those
    # atoms as Garcia ``NO`` rather than leaving them unclassified.
    def _is_defeater_argument(arg: "Argument") -> bool:
        return any(rule.kind == "defeater" for rule in arg.rules)

    warranted: set[GroundAtom] = set()
    trees: dict[GroundAtom, "DialecticalNode"] = {}
    markings: dict[GroundAtom, Literal["U", "D"]] = {}
    for arg in arguments:
        if _is_defeater_argument(arg):
            continue
        if arg.conclusion in warranted:
            continue
        tree = build_tree(
            arg,
            criterion,
            theory,
            universe=arguments,
            context=dialectical_context,
            concordance_cache=concordance_cache,
        )
        label = mark(tree)
        if arg.conclusion not in trees or label == "U":
            trees[arg.conclusion] = tree
            markings[arg.conclusion] = label
        if label == "U":
            warranted.add(arg.conclusion)

    defeater_probed: set[GroundAtom] = {
        arg.conclusion for arg in arguments if _is_defeater_argument(arg)
    }

    strict_atoms: set[GroundAtom] = {arg.conclusion for arg in arguments if not arg.rules}
    conclusions: set[GroundAtom] = {arg.conclusion for arg in arguments}
    conclusions.update(complement(atom) for atom in tuple(conclusions))

    # Garcia & Simari 2004 Def 5.3 (p. 120):
    #   YES       iff ``atom`` is warranted; strict Pi conclusions are
    #             represented as strict-only arguments and therefore
    #             count as warranted here.
    #   NO        iff the strong complement is warranted.
    #   UNDECIDED iff neither side is warranted but an argument exists
    #             on at least one side.
    #   UNKNOWN   iff the predicate is absent from the theory language.
    yes_atoms: set[GroundAtom] = set()
    no_atoms: set[GroundAtom] = set()
    undecided_atoms: set[GroundAtom] = set()
    unknown_atoms: set[GroundAtom] = set()

    for atom in conclusions:
        if _strip_negation(atom.predicate) not in predicates:
            unknown_atoms.add(atom)
            continue

        strict = atom in strict_atoms
        yes = atom in warranted
        no = complement(atom) in warranted or complement(atom) in strict_atoms
        # Nute/Antoniou defeater contribution: a defeater rule probes
        # the literal without ever warranting it. On the Garcia answer
        # surface, that probe makes the attacked literal a NO result.
        defeater_touches = atom in defeater_probed or complement(atom) in defeater_probed

        if yes or strict:
            yes_atoms.add(atom)
            continue
        if no or defeater_touches:
            no_atoms.add(atom)
            continue
        undecided_atoms.add(atom)

    sections = {
        "yes": _atoms_to_section(yes_atoms),
        "no": _atoms_to_section(no_atoms),
        "undecided": _atoms_to_section(undecided_atoms),
        "unknown": _atoms_to_section(unknown_atoms),
    }
    model = DefeasibleModel(
        sections=sections,
    )

    trace = DefeasibleTrace(config=trace_config)
    trace.grounding_inspection = grounding_inspection
    trace.strict = tuple(sorted(strict_atoms, key=_atom_sort_key))
    trace.yes = tuple(sorted(yes_atoms, key=_atom_sort_key))
    trace.arguments = arguments
    trace.trees = {
        atom: tree for atom, tree in sorted(trees.items(), key=lambda item: _atom_sort_key(item[0]))
    }
    trace.markings = {
        atom: label
        for atom, label in sorted(markings.items(), key=lambda item: _atom_sort_key(item[0]))
    }
    return model, trace


def _evaluate_spindle_projection(
    theory: SchemaDefeasibleTheory,
    trace_config: TraceConfig,
    *,
    max_arguments: int | None = None,
) -> tuple[DefeasibleModel, DefeasibleTrace]:
    """Lam/Governatori SPINdle projection over Maher's defeasible proof tags."""

    from ._internal import _ground_theory
    from .dialectic import _theory_predicates

    grounded = _ground_theory(theory)
    try:
        arguments = tuple(
            sorted(
                build_arguments(theory, max_arguments=max_arguments),
                key=_argument_sort_key,
            )
        )
    except EnumerationExceeded as exc:
        trace = DefeasibleTrace(config=trace_config)
        trace.grounding_inspection = grounded.inspection
        trace.arguments = tuple(sorted(exc.partial_arguments, key=_argument_sort_key))
        exc.partial_trace = trace
        raise

    strict_atoms: set[GroundAtom] = {arg.conclusion for arg in arguments if not arg.rules}
    accepted: set[GroundAtom] = set(strict_atoms)
    rules = tuple(grounded.grounded_defeasible_rules)
    superiority = _superiority_closure(theory.superiority)
    conflicts = grounded.conflicts

    changed = True
    while changed:
        changed = False
        for rule in rules:
            if rule.head in accepted:
                continue
            if not all(atom in accepted for atom in rule.body):
                continue
            if not all(atom not in accepted for atom in rule.default_negated_body):
                continue
            if _spindle_rule_is_overruled(rule, rules, accepted, superiority, conflicts):
                continue
            accepted.add(rule.head)
            changed = True

    defined_atoms: set[GroundAtom] = {rule.head for rule in rules}
    conclusions = set(defined_atoms | accepted)
    conclusions.update(complement(atom) for atom in tuple(conclusions))
    predicates = _theory_predicates(theory)

    yes_atoms: set[GroundAtom] = set()
    no_atoms: set[GroundAtom] = set()
    undecided_atoms: set[GroundAtom] = set()
    unknown_atoms: set[GroundAtom] = set()

    for atom in conclusions:
        if _strip_negation(atom.predicate) not in predicates:
            unknown_atoms.add(atom)
            continue
        if atom in accepted:
            yes_atoms.add(atom)
            continue
        if _has_accepted_conflict(atom, accepted, conflicts) or atom in defined_atoms:
            no_atoms.add(atom)
            continue
        undecided_atoms.add(atom)

    model = DefeasibleModel(
        sections={
            "yes": _atoms_to_section(yes_atoms),
            "no": _atoms_to_section(no_atoms),
            "undecided": _atoms_to_section(undecided_atoms),
            "unknown": _atoms_to_section(unknown_atoms),
        }
    )
    trace = DefeasibleTrace(config=trace_config)
    trace.grounding_inspection = grounded.inspection
    trace.strict = tuple(sorted(strict_atoms, key=_atom_sort_key))
    trace.yes = tuple(sorted(yes_atoms, key=_atom_sort_key))
    trace.arguments = arguments
    return model, trace


def _spindle_rule_is_overruled(
    rule: "GroundDefeasibleRule",
    rules: tuple["GroundDefeasibleRule", ...],
    accepted: set[GroundAtom],
    superiority: frozenset[tuple[str, str]],
    conflicts: frozenset[tuple[str, str]],
) -> bool:
    for opponent in rules:
        if not _atoms_conflict(rule.head, opponent.head, conflicts):
            continue
        if not all(atom in accepted for atom in opponent.body):
            continue
        if any(atom in accepted for atom in opponent.default_negated_body):
            continue
        if _spindle_opponent_is_defeated(
            opponent, rule.head, rules, accepted, superiority, conflicts
        ):
            continue
        return True
    return False


def _spindle_opponent_is_defeated(
    opponent: "GroundDefeasibleRule",
    target: GroundAtom,
    rules: tuple["GroundDefeasibleRule", ...],
    accepted: set[GroundAtom],
    superiority: frozenset[tuple[str, str]],
    conflicts: frozenset[tuple[str, str]],
) -> bool:
    for defender in rules:
        if not _atoms_conflict(defender.head, opponent.head, conflicts):
            continue
        if not _same_literal(defender.head, target):
            continue
        if (defender.rule_id, opponent.rule_id) not in superiority:
            continue
        if not all(atom in accepted for atom in defender.body):
            continue
        if any(atom in accepted for atom in defender.default_negated_body):
            continue
        return True
    return False


def _has_accepted_conflict(
    atom: GroundAtom,
    accepted: set[GroundAtom],
    conflicts: frozenset[tuple[str, str]],
) -> bool:
    return any(_atoms_conflict(atom, other, conflicts) for other in accepted)


def _atoms_conflict(
    left: GroundAtom,
    right: GroundAtom,
    conflicts: frozenset[tuple[str, str]],
) -> bool:
    return left.arguments == right.arguments and (
        _same_literal(complement(left), right) or (left.predicate, right.predicate) in conflicts
    )


def _same_literal(left: GroundAtom, right: GroundAtom) -> bool:
    return left.predicate == right.predicate and left.arguments == right.arguments


def _superiority_closure(
    pairs: tuple[tuple[str, str], ...],
) -> frozenset[tuple[str, str]]:
    closure = set(pairs)
    changed = True
    while changed:
        changed = False
        for left, middle in tuple(closure):
            for candidate_middle, right in tuple(closure):
                if middle != candidate_middle or (left, right) in closure:
                    continue
                closure.add((left, right))
                changed = True
    return frozenset(closure)


def _evaluate_antoniou_policy(
    theory: SchemaDefeasibleTheory,
    trace_config: TraceConfig,
    *,
    propagate_ambiguity: bool,
) -> tuple[DefeasibleModel, DefeasibleTrace]:
    """Antoniou 2007 section 3.5 ambiguity-blocking/propagating projection."""

    from .dialectic import _theory_predicates
    from .preference import (
        CompositePreference,
        GeneralizedSpecificity,
        SuperiorityPreference,
    )

    arguments = tuple(sorted(build_arguments(theory), key=_argument_sort_key))
    criterion = CompositePreference(
        SuperiorityPreference(theory),
        GeneralizedSpecificity(theory),
    )
    strict_atoms = {argument.conclusion for argument in arguments if not argument.rules}
    supported_atoms = {argument.conclusion for argument in arguments}
    non_defeater_arguments = tuple(
        argument
        for argument in arguments
        if not any(rule.kind == "defeater" for rule in argument.rules)
    )

    accepted = set(strict_atoms)
    changed = True
    while changed:
        changed = False
        for argument in non_defeater_arguments:
            if argument.conclusion in accepted:
                continue
            if not _argument_bodies_satisfied(argument, accepted):
                continue
            if _propagating_opposition_blocks(
                argument,
                non_defeater_arguments,
                supported_atoms,
                accepted,
                strict_atoms,
                criterion,
                propagate_ambiguity=propagate_ambiguity,
            ):
                continue
            accepted.add(argument.conclusion)
            changed = True

    conclusions = set(supported_atoms)
    conclusions.update(complement(atom) for atom in tuple(conclusions))
    predicates = _theory_predicates(theory)
    yes_atoms: set[GroundAtom] = set()
    no_atoms: set[GroundAtom] = set()
    undecided_atoms: set[GroundAtom] = set()
    unknown_atoms: set[GroundAtom] = set()
    for atom in conclusions:
        if _strip_negation(atom.predicate) not in predicates:
            unknown_atoms.add(atom)
            continue
        if atom in accepted:
            yes_atoms.add(atom)
        elif atom in supported_atoms or complement(atom) in supported_atoms:
            undecided_atoms.add(atom)
        elif complement(atom) in accepted:
            no_atoms.add(atom)

    model = DefeasibleModel(
        sections={
            "yes": _atoms_to_section(yes_atoms),
            "no": _atoms_to_section(no_atoms),
            "undecided": _atoms_to_section(undecided_atoms),
            "unknown": _atoms_to_section(unknown_atoms),
        }
    )
    trace = DefeasibleTrace(config=trace_config)
    trace.grounding_inspection = inspect_grounding(theory)
    trace.strict = tuple(sorted(strict_atoms, key=_atom_sort_key))
    trace.yes = tuple(sorted(yes_atoms, key=_atom_sort_key))
    trace.arguments = arguments
    return model, trace


def _argument_bodies_satisfied(
    argument: "Argument",
    accepted: set[GroundAtom],
) -> bool:
    return all(atom in accepted for rule in argument.rules for atom in rule.body)


def _argument_bodies_supported(
    argument: "Argument",
    supported: set[GroundAtom],
) -> bool:
    return all(atom in supported for rule in argument.rules for atom in rule.body)


def _propagating_opposition_blocks(
    argument: "Argument",
    arguments: tuple["Argument", ...],
    supported_atoms: set[GroundAtom],
    accepted_atoms: set[GroundAtom],
    strict_atoms: set[GroundAtom],
    criterion: "PreferenceCriterion",
    *,
    propagate_ambiguity: bool,
) -> bool:
    if argument.conclusion in strict_atoms:
        return False
    opposite = complement(argument.conclusion)
    for opponent in arguments:
        if opponent.conclusion != opposite:
            continue
        if propagate_ambiguity:
            opponent_body_available = _argument_bodies_supported(opponent, supported_atoms)
        else:
            opponent_body_available = _argument_bodies_satisfied(opponent, accepted_atoms)
        if not opponent_body_available:
            continue
        if criterion.prefers(argument, opponent):
            continue
        return True
    return False


def _populate_strict_only_argument_view(
    theory: SchemaDefeasibleTheory,
    trace: DefeasibleTrace,
) -> None:
    """Populate the optional argument view for the strict-only fast path.

    Strict-only enumeration is bounded by the strict closure size: there
    are no defeasible rule subsets to enumerate, only ``<empty, h>`` leaf
    arguments for strict consequences.
    """

    from .dialectic import DialecticalNode

    arguments = tuple(sorted(build_arguments(theory), key=_argument_sort_key))
    trace.arguments = arguments
    trace.trees = {
        argument.conclusion: DialecticalNode(argument=argument, children=())
        for argument in arguments
    }
    trace.markings = {argument.conclusion: "U" for argument in arguments}


def _argument_sort_key(
    arg: "Argument",
) -> tuple[tuple[str, FactTuple], tuple[tuple[str, str], ...]]:
    return (
        _atom_sort_key(arg.conclusion),
        tuple(sorted((rule.kind, rule.rule_id) for rule in arg.rules)),
    )


def _strip_negation(predicate: str) -> str:
    """Return ``predicate`` with its strong-negation ``~`` prefix removed."""
    if predicate.startswith("~"):
        return predicate[1:]
    return predicate


def _is_strict_only_theory(theory: SchemaDefeasibleTheory) -> bool:
    return (
        not theory.defeasible_rules
        and not theory.defeaters
        and not theory.presumptions
        and not theory.superiority
    )


def _evaluate_strict_only_theory_with_trace(
    theory: SchemaDefeasibleTheory,
    trace_config: TraceConfig,
    negation_semantics: NegationSemantics,
) -> tuple[DefeasibleModel, DatalogTrace]:
    program = SchemaProgram(
        facts=theory.facts,
        rules=[_strict_rule_to_program_text(rule.head, rule.body) for rule in theory.strict_rules],
    )
    model, trace = SemiNaiveEvaluator().evaluate_with_trace(
        program,
        trace_config,
        negation_semantics=negation_semantics,
    )
    _raise_if_strict_pi_contradictory(model.facts, theory.conflicts)
    sections = {
        "yes": {predicate: set(rows) for predicate, rows in model.facts.items()},
        "no": {},
        "undecided": {},
        "unknown": {},
    }
    return DefeasibleModel(
        sections=sections,
    ), trace


def _raise_if_strict_pi_contradictory(
    facts: ModelFacts,
    conflicts: Sequence[tuple[str, str]],
) -> None:
    for predicate, rows in facts.items():
        if predicate.startswith("~"):
            continue
        complement_predicate = f"~{predicate}"
        overlap = rows & facts.get(complement_predicate, set())
        if overlap:
            row = next(iter(overlap))
            raise ContradictoryStrictTheoryError(
                f"Pi derives both {predicate}{row!r} and {complement_predicate}{row!r}"
            )

    for left, right in conflicts:
        overlap = facts.get(left, set()) & facts.get(right, set())
        if overlap:
            row = next(iter(overlap))
            raise ContradictoryStrictTheoryError(
                f"Pi derives conflicting atoms {left}{row!r} and {right}{row!r}"
            )


def _atoms_to_section(atoms: set[GroundAtom]) -> dict[str, set[FactTuple]]:
    section: dict[str, set[FactTuple]] = {}
    for atom in atoms:
        section.setdefault(atom.predicate, set()).add(atom.arguments)
    return section


def _section_to_atoms(section: ModelFacts) -> set[GroundAtom]:
    return {
        GroundAtom(predicate=predicate, arguments=arguments)
        for predicate, rows in section.items()
        for arguments in rows
    }
