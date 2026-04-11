# Gunray

Gunray is a pure-Python evaluator for the current `datalog-conformance` Datalog and
defeasible-Datalog test surface.

## Scope

- Core Datalog evaluation from `datalog_conformance.schema.Program`
- Stratified negation with explicit rejection of cyclic negation
- Blocking-style defeasible reasoning with strict rules, defeasible rules, defeaters,
  conflicts, and superiority

The package currently targets the conformance suite that is cloned at
`../datalog-conformance-suite`.

## Explicit Value Semantics

Gunray now routes equality, ordering, and arithmetic through
`gunray.semantics` instead of relying on ad hoc inline Python operators.

The current policy is:

- Equality and inequality use exact normalized Python scalar equality.
- Ordering operators use Python ordering when the operand pair is comparable.
- `+` means numeric addition for numeric operands and concatenation otherwise.
- `-` means numeric subtraction only.

If that policy changes, `src/gunray/semantics.py` is the single place to change
and review it.

## Verification

```powershell
uv sync --extra dev
uv run pytest
uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.evaluator.SemiNaiveEvaluator
uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.defeasible.DefeasibleEvaluator
```
