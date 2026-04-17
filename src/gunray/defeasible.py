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
- The four-valued answer (Def 5.3) projects into the
  ``DefeasibleModel.sections`` dict with the four keys
  ``definitely`` / ``defeasibly`` / ``not_defeasibly`` /
  ``undecided`` for backwards compatibility with the propstore
  contract.

The preference criterion is
``CompositePreference(SuperiorityPreference, GeneralizedSpecificity)``:
explicit user superiority (Garcia 04 §4.1) takes precedence over
generalized specificity (Simari 92 Lemma 2.4) via
first-criterion-to-fire composition.

Strict-only theories route around the argument pipeline via
``_is_strict_only_theory`` and ``SemiNaiveEvaluator`` for performance.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from .errors import ContradictoryStrictTheoryError
from .evaluator import SemiNaiveEvaluator
from .schema import DefeasibleModel, FactTuple, ModelFacts, Policy
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
        # Post-Block-2, Policy.BLOCKING is the only supported value —
        # argument preference is resolved by GeneralizedSpecificity
        # (Simari 92 Lemma 2.4) regardless of the policy value. The
        # parameter is preserved for public-API stability; see
        # notes/policy_propagating_fate.md for the PROPAGATING
        # deprecation decision.
        del policy
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
    from .arguments import build_arguments
    from .dialectic import _theory_predicates, build_tree, mark
    from .disagreement import complement
    from .preference import (
        CompositePreference,
        GeneralizedSpecificity,
        SuperiorityPreference,
    )

    arguments = tuple(sorted(build_arguments(theory), key=_argument_sort_key))
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
        GeneralizedSpecificity(theory),
    )
    predicates = _theory_predicates(theory)

    # Defeater-kind arguments exist in the argument universe (so they
    # can attack in the dialectical tree) but do not warrant anything:
    # a defeater rule is a pure attacker in the Nute/Antoniou reading
    # (``notes/b2_defeater_participation.md``). We therefore exclude
    # them here when computing ``warranted`` and separately track the
    # atoms they probe so the section projection can classify those
    # atoms as ``not_defeasibly`` rather than leaving them unclassified.
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
        tree = build_tree(arg, criterion, theory)
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
    conclusions.update(complement(atom) for atom in strict_atoms)

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

    for atom in conclusions:
        # UNKNOWN gate: literals whose predicate isn't in the
        # language are omitted from every section per Garcia 04
        # Def 5.3 (and propstore's expectation per scout 2.2).
        if _strip_negation(atom.predicate) not in predicates:
            continue

        strict = atom in strict_atoms
        yes = atom in warranted
        no = complement(atom) in warranted or complement(atom) in strict_atoms
        # Nute/Antoniou defeater contribution: a defeater rule whose
        # head is ``atom`` or ``complement(atom)`` probes the literal
        # without ever warranting it, and routes both sides of the
        # probe into ``not_defeasibly``. See
        # ``notes/b2_defeater_participation.md``.
        defeater_touches = atom in defeater_probed or complement(atom) in defeater_probed

        if strict:
            definitely_atoms.add(atom)
        if yes or strict:
            defeasibly_atoms.add(atom)
            continue
        if no or defeater_touches:
            not_defeasibly_atoms.add(atom)
            continue
        # Neither yes, no, nor strict — but at least one argument
        # exists for ``atom`` (it is in ``conclusions``), so by Def 5.3
        # this is UNDECIDED.
        undecided_atoms.add(atom)

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
    trace.supported = tuple(sorted(definitely_atoms | defeasibly_atoms, key=_atom_sort_key))
    trace.arguments = arguments
    trace.trees = {
        atom: tree
        for atom, tree in sorted(trees.items(), key=lambda item: _atom_sort_key(item[0]))
    }
    trace.markings = {
        atom: label
        for atom, label in sorted(markings.items(), key=lambda item: _atom_sort_key(item[0]))
    }
    return model, trace


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
    return not theory.defeasible_rules and not theory.defeaters and not theory.superiority


def _evaluate_strict_only_theory_with_trace(
    theory: SchemaDefeasibleTheory,
    trace_config: TraceConfig,
) -> tuple[DefeasibleModel, DatalogTrace]:
    program = SchemaProgram(
        facts=theory.facts,
        rules=[_strict_rule_to_program_text(rule.head, rule.body) for rule in theory.strict_rules],
    )
    model, trace = SemiNaiveEvaluator().evaluate_with_trace(program, trace_config)
    _raise_if_strict_pi_contradictory(model.facts, theory.conflicts)
    sections = {
        "definitely": {predicate: set(rows) for predicate, rows in model.facts.items()},
        "defeasibly": {predicate: set(rows) for predicate, rows in model.facts.items()},
    }
    return DefeasibleModel(
        sections={name: facts_map for name, facts_map in sections.items() if facts_map}
    ), trace


def _raise_if_strict_pi_contradictory(
    facts: ModelFacts,
    conflicts: list[tuple[str, str]],
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
