# Gunray

Gunray is a pure-Python evaluator for the current `datalog-conformance` Datalog and
defeasible-Datalog surface.

It targets the suite cloned at `../datalog-conformance-suite`.

## Scope

- Core Datalog evaluation from `datalog_conformance.schema.Program`
- Stratified negation with explicit rejection of cyclic negation
- Defeasible reasoning with:
  - blocking and propagating ambiguity policies
  - strict rules, defeasible rules, defeaters, conflicts, and superiority
- Reduced zero-arity closure support for the current conformance fragment:
  - rational closure
  - lexicographic closure
  - relevant closure
- KLM `Or` checks through the same reduced closure engine

The closure implementation is intentionally narrower than the general defeasible engine. It exists
to satisfy the current conformance-suite closure and KLM corpus, not as a full general closure
reasoner for arbitrary first-order theories.

## Value Semantics

Gunray routes equality, ordering, and arithmetic through [semantics.py](src/gunray/semantics.py)
instead of scattering raw Python operators across the evaluator.

Current policy:

- Equality and inequality use normalized Python scalar equality.
- Ordering uses Python ordering when the operand pair is comparable.
- `+` means numeric addition for numeric operands and concatenation otherwise.
- `-` means numeric subtraction only.

## Layout

- [adapter.py](src/gunray/adapter.py): conformance-suite entrypoint
- [evaluator.py](src/gunray/evaluator.py): semi-naive core Datalog engine
- [defeasible.py](src/gunray/defeasible.py): defeasible evaluator for the main theory surface
- [ambiguity.py](src/gunray/ambiguity.py): explicit ambiguity-policy handling
- [closure.py](src/gunray/closure.py): reduced closure and KLM support for the current suite
- [trace.py](src/gunray/trace.py): execution-trace structures and helpers

## Verification

```powershell
uv sync --extra dev
uv run pytest tests -q
uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.adapter.GunrayEvaluator -q
```
