"""Defeasible evaluator — paper-pipeline skeleton.

The atom-level classifier that used to live here has been removed
(commit B1.2 scorched earth). The public `DefeasibleEvaluator` still
routes strict-only theories through the semi-naive engine; the
defeasible path currently raises NotImplementedError and will be
rewired in dispatch B1.6 onto the argument / dialectical-tree
pipeline specified by Garcia & Simari 2004 §5.
"""

from __future__ import annotations

from .evaluator import SemiNaiveEvaluator
from .schema import DefeasibleModel, FactTuple, ModelFacts, Policy
from .schema import DefeasibleTheory as SchemaDefeasibleTheory
from .schema import Program as SchemaProgram
from .trace import DatalogTrace, DefeasibleTrace, TraceConfig
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
        raise NotImplementedError(
            "DefeasibleEvaluator.evaluate_with_trace: defeasible path rewired in B1.6"
        )


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
