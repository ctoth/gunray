# Gunray

Gunray is a pure-Python evaluator for the current `datalog-conformance` Datalog and
defeasible-Datalog surface.

It is built to run against the conformance suite in the sibling repository
`../datalog-conformance-suite`, and it exposes the same schema objects the suite uses.

## What It Supports

- Bottom-up Datalog evaluation through `datalog_conformance.schema.Program`
- Stratified negation, with explicit rejection of cyclic negation
- Defeasible reasoning through `datalog_conformance.schema.DefeasibleTheory`
- Blocking and propagating ambiguity policies
- Strict rules, defeasible rules, defeaters, conflicts, and superiority
- Execution traces for both Datalog and defeasible runs
- Reduced closure support for the current conformance fragment:
  - rational closure
  - lexicographic closure
  - relevant closure
- KLM `Or` checks through the same reduced closure engine

## Current Boundaries

Gunray is deliberately narrower than a general-purpose defeasible logic platform.

- The closure engine only supports the current zero-arity closure fragment used by the
  conformance suite.
- Closure evaluation rejects defeaters, superiority, explicit conflict sets, and non-zero-arity
  literals.
- The project is optimized around the current suite surface, not arbitrary first-order theories.

## Setup

Prerequisites:

- Python 3.11+
- `uv`
- A checkout of `datalog-conformance-suite` at `../datalog-conformance-suite`

Install the environment with:

```powershell
uv sync --extra dev
```

`pyproject.toml` wires `datalog-conformance` from that sibling checkout:

```toml
[tool.uv.sources]
datalog-conformance = { path = "../datalog-conformance-suite" }
```

## Quick Start

For suite-style dispatch, use `GunrayEvaluator`:

```python
from datalog_conformance.schema import Policy, Program, Rule, DefeasibleTheory

from gunray import GunrayEvaluator

evaluator = GunrayEvaluator()

program = Program(
    facts={"edge": {("a", "b"), ("b", "c")}},
    rules=[
        "path(X, Y) :- edge(X, Y).",
        "path(X, Z) :- edge(X, Y), path(Y, Z).",
    ],
)

program_model = evaluator.evaluate(program)

theory = DefeasibleTheory(
    facts={"bird": {("tweety",)}, "penguin": {("tweety",)}},
    strict_rules=[
        Rule(id="s1", head="bird(X)", body=["penguin(X)"]),
    ],
    defeasible_rules=[
        Rule(id="r1", head="flies(X)", body=["bird(X)"]),
        Rule(id="r2", head="~flies(X)", body=["penguin(X)"]),
    ],
    defeaters=[],
    superiority=[],
    conflicts=[],
)

theory_model = evaluator.evaluate(theory, Policy.BLOCKING)
```

The package also exposes the lower-level evaluators directly:

- `SemiNaiveEvaluator` for stratified Datalog
- `DefeasibleEvaluator` for the main defeasible engine

## Trace Support

Both Datalog and defeasible evaluation can return structured traces:

```python
from datalog_conformance.schema import Program

from gunray import GunrayEvaluator, TraceConfig

program = Program(
    facts={"edge": {("a", "b"), ("b", "c")}},
    rules=[
        "path(X, Y) :- edge(X, Y).",
        "path(X, Z) :- edge(X, Y), path(Y, Z).",
    ],
)

model, trace = GunrayEvaluator().evaluate_with_trace(
    program,
    trace_config=TraceConfig(
        capture_derived_rows=True,
        max_derived_rows_per_rule_fire=2,
    ),
)

rule_fires = trace.find_rule_fires(head_predicate="path", derived_count_at_least=1)
```

For defeasible theories, the trace records:

- proof attempts
- final classifications
- supporting and attacking rule ids
- conflicting atoms
- the strict-only Datalog trace when a theory has no defeasible content

## Value Semantics

Gunray routes equality, ordering, and arithmetic through
[semantics.py](src/gunray/semantics.py) instead of scattering raw Python operators across the
evaluator.

Current policy:

- Equality and inequality use normalized Python scalar equality.
- Ordering uses Python ordering when the operand pair is comparable.
- `+` means numeric addition for numeric operands and concatenation otherwise.
- `-` means numeric subtraction only.

## Repository Layout

- [src/gunray/adapter.py](src/gunray/adapter.py): suite-facing dispatcher
- [src/gunray/evaluator.py](src/gunray/evaluator.py): semi-naive Datalog engine
- [src/gunray/defeasible.py](src/gunray/defeasible.py): defeasible evaluator
- [src/gunray/closure.py](src/gunray/closure.py): reduced closure and KLM support
- [src/gunray/trace.py](src/gunray/trace.py): structured trace types and helpers
- [tests/test_conformance.py](tests/test_conformance.py): suite harness

## Verification

Run the local test suite:

```powershell
uv run pytest tests -q
```

Run the conformance corpus against Gunray:

```powershell
uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.adapter.GunrayEvaluator -q
```

For manual inspection of defeasible suite cases, the repo also includes:

```powershell
uv run python scripts/show_defeasible_case.py --help
```
