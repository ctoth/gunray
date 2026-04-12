# Gunray

Pure-Python evaluator for the `datalog-conformance` test suite. If you landed
here cold, this is the engine that the cases in
[`ctoth/datalog-conformance-suite`](https://github.com/ctoth/datalog-conformance-suite)
run against.

Gunray covers stratified Datalog with negation, defeasible reasoning under
blocking and propagating ambiguity, and the reduced closure fragment the suite
currently exercises: rational, lexicographic, and relevant closure, plus KLM
`Or` checks through the same path.

The closure engine is intentionally narrow. It only handles the zero-arity
propositional fragment and rejects defeaters, superiority, and explicit
conflict sets. Everything else — strict rules, defeasible rules, defeaters,
superiority, conflicts — goes through the main defeasible evaluator, not the
closure path.

## Setup

Python 3.11+ and `uv`. The conformance suite is declared as a git dependency
in `pyproject.toml`, so a sibling checkout isn't required:

```powershell
uv sync --extra dev
```

## Usage

`GunrayEvaluator` is the suite-facing entry point and dispatches on whether
you hand it a `Program` or a `DefeasibleTheory`:

```python
from datalog_conformance.schema import DefeasibleTheory, Policy, Program, Rule

from gunray import GunrayEvaluator

evaluator = GunrayEvaluator()

program = Program(
    facts={"edge": {("a", "b"), ("b", "c")}},
    rules=[
        "path(X, Y) :- edge(X, Y).",
        "path(X, Z) :- edge(X, Y), path(Y, Z).",
    ],
)
model = evaluator.evaluate(program)

theory = DefeasibleTheory(
    facts={"bird": {("tweety",)}, "penguin": {("tweety",)}},
    strict_rules=[Rule(id="s1", head="bird(X)", body=["penguin(X)"])],
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

`SemiNaiveEvaluator` and `DefeasibleEvaluator` are also exported from
`gunray` if you want to skip dispatch and drive one engine directly.

## Traces

Both engines can return structured traces through `evaluate_with_trace`:

```python
from gunray import GunrayEvaluator, TraceConfig

model, trace = GunrayEvaluator().evaluate_with_trace(
    program,
    trace_config=TraceConfig(
        capture_derived_rows=True,
        max_derived_rows_per_rule_fire=2,
    ),
)
fires = trace.find_rule_fires(head_predicate="path", derived_count_at_least=1)
```

Defeasible traces carry proof attempts, final classifications, supporting and
attacking rule ids, and the atoms in conflict. When a theory has no
defeasible content, the strict-only Datalog trace is returned directly.

## Value semantics

Equality, ordering, and arithmetic go through
[`semantics.py`](src/gunray/semantics.py) rather than being scattered across
the evaluator. Equality normalizes Python scalars, ordering defers to Python
when the operand pair is comparable, `+` is numeric addition for numeric
operands and concatenation otherwise, and `-` is numeric subtraction only.

## Layout

- [`adapter.py`](src/gunray/adapter.py) — `GunrayEvaluator`, suite-facing dispatcher
- [`evaluator.py`](src/gunray/evaluator.py) — semi-naive Datalog engine
- [`defeasible.py`](src/gunray/defeasible.py) — defeasible evaluator
- [`closure.py`](src/gunray/closure.py) — reduced closure and KLM `Or`
- [`trace.py`](src/gunray/trace.py) — trace types and helpers
- [`tests/test_conformance.py`](tests/test_conformance.py) — conformance harness

## Running tests

Local suite:

```powershell
uv run pytest tests -q
```

Full conformance corpus against Gunray:

```powershell
uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.adapter.GunrayEvaluator -q
```

For poking at individual defeasible cases by hand:

```powershell
uv run python scripts/show_defeasible_case.py --help
```
