"""Defeasible evaluator — paper-pipeline wiring.

Garcia & Simari 2004 §5: an argument-based defeasible evaluator
projecting the dialectical-tree machinery onto the four-key
``DefeasibleModel.sections`` contract that propstore and the
conformance suite consume.

Strict-only theories take a shortcut through ``SemiNaiveEvaluator``
(no defeasible rules, no defeaters, no superiority — nothing for the
dialectical tree to chew on). Every other theory routes through
``build_arguments`` (Garcia 04 Def 3.1) → ``build_tree`` (Def 5.1 +
Def 4.7) → ``mark`` (Proc 5.1) → section projection per the rules
documented on ``_sections_from_arguments`` below.
"""

from __future__ import annotations

from .evaluator import SemiNaiveEvaluator
from .schema import DefeasibleModel, FactTuple, ModelFacts, Policy
from .schema import DefeasibleTheory as SchemaDefeasibleTheory
from .schema import Program as SchemaProgram
from .trace import (
    ClassificationTrace,
    DatalogTrace,
    DefeasibleTrace,
    ProofAttemptTrace,
    TraceConfig,
)
from .types import GroundAtom


class DefeasibleEvaluator:
    """Evaluate defeasible theories under Gunray's supported semantics."""

    def evaluate(self, theory: SchemaDefeasibleTheory, policy: Policy) -> DefeasibleModel:
        model, _ = self.evaluate_with_trace(theory, policy)
        return model

    def evaluate_with_trace(
        self,
        theory: SchemaDefeasibleTheory,
        policy: Policy,
        trace_config: TraceConfig | None = None,
    ) -> tuple[DefeasibleModel, DefeasibleTrace]:
        del policy  # honored by the dialectical-tree path; unused for the strict-only shortcut
        actual_trace_config = trace_config or TraceConfig()
        if _is_strict_only_theory(theory):
            model, strict_trace = _evaluate_strict_only_theory_with_trace(
                theory,
                actual_trace_config,
            )
            trace = DefeasibleTrace(config=actual_trace_config)
            trace.strict_trace = strict_trace
            trace.definitely = tuple(
                sorted(
                    _section_to_atoms(model.sections.get("definitely", {})),
                    key=_atom_sort_key,
                )
            )
            trace.supported = trace.definitely
            return model, trace

        return _evaluate_via_argument_pipeline(theory, actual_trace_config)


def _evaluate_via_argument_pipeline(
    theory: SchemaDefeasibleTheory,
    trace_config: TraceConfig,
) -> tuple[DefeasibleModel, DefeasibleTrace]:
    """Garcia & Simari 2004 §5 pipeline: enumerate, mark, project.

    Lazy imports break the circular dependency between ``defeasible``
    and ``dialectic``: the dialectical module imports
    ``_atom_sort_key`` from this file at import time.
    """
    from .arguments import Argument, build_arguments
    from .dialectic import _theory_predicates, build_tree, mark
    from .disagreement import complement
    from .preference import TrivialPreference

    arguments = build_arguments(theory)
    criterion = TrivialPreference()
    predicates = _theory_predicates(theory)

    # Group every distinct ground conclusion by literal so each atom
    # is classified exactly once. The prompt explicitly forbids
    # looping ``answer`` per literal — we already have every argument
    # and we mark each tree at most once via ``warranted_literals``.
    conclusions: set[GroundAtom] = {arg.conclusion for arg in arguments}

    warranted: set[GroundAtom] = set()
    for arg in arguments:
        if arg.conclusion in warranted:
            continue
        if mark(build_tree(arg, criterion, theory)) == "U":
            warranted.add(arg.conclusion)

    strict_atoms: set[GroundAtom] = {
        arg.conclusion for arg in arguments if not arg.rules
    }

    # Section projection rules (per the B1.6 prompt verbatim):
    #   strict   = ∃⟨∅, h⟩
    #   yes      = ∃⟨A, h⟩ marked U
    #   no       = ∃⟨A, complement(h)⟩ marked U
    #   definitely    iff strict
    #   defeasibly    iff yes OR strict
    #   not_defeasibly iff no AND NOT strict
    #   undecided     iff (NOT yes AND NOT no AND NOT strict)
    #                    AND (some argument for h or complement(h) exists)
    #   UNKNOWN (predicate not in language) → omitted from every section
    definitely_atoms: set[GroundAtom] = set()
    defeasibly_atoms: set[GroundAtom] = set()
    not_defeasibly_atoms: set[GroundAtom] = set()
    undecided_atoms: set[GroundAtom] = set()

    classifications: list[ClassificationTrace] = []
    proof_attempts: list[ProofAttemptTrace] = []

    for atom in conclusions:
        # UNKNOWN gate: literals whose predicate isn't in the
        # language are omitted from every section per Garcia 04
        # Def 5.3 (and propstore's expectation per scout 2.2).
        if _strip_negation(atom.predicate) not in predicates:
            continue

        strict = atom in strict_atoms
        yes = atom in warranted
        no = complement(atom) in warranted

        if strict:
            definitely_atoms.add(atom)
        if yes or strict:
            defeasibly_atoms.add(atom)
            classifications.append(
                ClassificationTrace(
                    atom=atom,
                    result="defeasibly" if not strict else "definitely",
                    reason="strict_derivation" if strict else "warranted",
                    supporter_rule_ids=_supporter_rule_ids(atom, arguments),
                )
            )
            continue
        if no:
            not_defeasibly_atoms.add(atom)
            classifications.append(
                ClassificationTrace(
                    atom=atom,
                    result="not_defeasibly",
                    reason="complement_warranted",
                    attacker_rule_ids=_supporter_rule_ids(complement(atom), arguments),
                    opposing_atoms=(complement(atom),),
                )
            )
            continue
        # Neither yes, no, nor strict — but at least one argument
        # exists for ``atom`` (it is in ``conclusions``), so by Def 5.3
        # this is UNDECIDED.
        undecided_atoms.add(atom)
        classifications.append(
            ClassificationTrace(
                atom=atom,
                result="undecided",
                reason="equal_strength_peer_conflict",
                supporter_rule_ids=_supporter_rule_ids(atom, arguments),
                attacker_rule_ids=_supporter_rule_ids(complement(atom), arguments),
                opposing_atoms=(complement(atom),),
            )
        )
        proof_attempts.append(
            ProofAttemptTrace(
                atom=atom,
                result="blocked",
                reason="equal_strength_peer_conflict",
                supporter_rule_ids=_supporter_rule_ids(atom, arguments),
                attacker_rule_ids=_supporter_rule_ids(complement(atom), arguments),
                opposing_atoms=(complement(atom),),
            )
        )

    sections = {
        "definitely": _atoms_to_section(definitely_atoms),
        "defeasibly": _atoms_to_section(defeasibly_atoms),
        "not_defeasibly": _atoms_to_section(not_defeasibly_atoms),
        "undecided": _atoms_to_section(undecided_atoms),
    }
    model = DefeasibleModel(
        sections={name: facts_map for name, facts_map in sections.items() if facts_map}
    )

    trace = DefeasibleTrace(config=trace_config)
    trace.definitely = tuple(sorted(definitely_atoms, key=_atom_sort_key))
    trace.supported = tuple(
        sorted(definitely_atoms | defeasibly_atoms, key=_atom_sort_key)
    )
    trace.classifications = classifications
    trace.proof_attempts = proof_attempts
    return model, trace


def _supporter_rule_ids(
    atom: GroundAtom,
    arguments: "frozenset[object]",
) -> tuple[str, ...]:
    """Collect sorted rule-ids of every argument whose conclusion is ``atom``.

    Used to populate ``ClassificationTrace.supporter_rule_ids`` /
    ``attacker_rule_ids`` so re-landed trace tests can introspect why
    a literal landed in ``undecided`` / ``not_defeasibly``.
    """
    ids: set[str] = set()
    for arg in arguments:
        if getattr(arg, "conclusion", None) != atom:
            continue
        for rule in getattr(arg, "rules", frozenset()):
            ids.add(rule.rule_id)
    return tuple(sorted(ids))


def _strip_negation(predicate: str) -> str:
    """Return ``predicate`` with its strong-negation ``~`` prefix removed."""
    if predicate.startswith("~"):
        return predicate[1:]
    return predicate


def _is_strict_only_theory(theory: SchemaDefeasibleTheory) -> bool:
    return not theory.defeasible_rules and not theory.defeaters and not theory.superiority


def _evaluate_strict_only_theory(theory: SchemaDefeasibleTheory) -> DefeasibleModel:
    model, _ = _evaluate_strict_only_theory_with_trace(theory, TraceConfig())
    return model


def _evaluate_strict_only_theory_with_trace(
    theory: SchemaDefeasibleTheory,
    trace_config: TraceConfig,
) -> tuple[DefeasibleModel, DatalogTrace]:
    program = SchemaProgram(
        facts=theory.facts,
        rules=[_strict_rule_to_program_text(rule.head, rule.body) for rule in theory.strict_rules],
    )
    model, trace = SemiNaiveEvaluator().evaluate_with_trace(program, trace_config)
    sections = {
        "definitely": {predicate: set(rows) for predicate, rows in model.facts.items()},
        "defeasibly": {predicate: set(rows) for predicate, rows in model.facts.items()},
    }
    return DefeasibleModel(
        sections={name: facts_map for name, facts_map in sections.items() if facts_map}
    ), trace


def _strict_rule_to_program_text(head: str, body: list[str]) -> str:
    if not body:
        return f"{head}."
    return f"{head} :- {', '.join(body)}."


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


def _atom_sort_key(atom: GroundAtom) -> tuple[str, FactTuple]:
    return atom.predicate, atom.arguments
