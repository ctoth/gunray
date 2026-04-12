# Gunray

Gunray is a defeasible logic engine — one that can make sense of rules that
contradict each other. Tell it *birds fly*, tell it *penguins don't fly*,
hand it a bird that happens to also be a penguin, and it does the right
thing:

```python
from datalog_conformance.schema import DefeasibleTheory, Policy, Rule
from gunray import GunrayEvaluator

theory = DefeasibleTheory(
    facts={"bird": {("tweety",), ("opus",)}, "penguin": {("opus",)}},
    strict_rules=[Rule(id="s1", head="bird(X)", body=["penguin(X)"])],
    defeasible_rules=[
        Rule(id="r1", head="flies(X)",  body=["bird(X)"]),
        Rule(id="r2", head="~flies(X)", body=["penguin(X)"]),
    ],
    defeaters=[], superiority=[], conflicts=[],
)

model = GunrayEvaluator().evaluate(theory, Policy.BLOCKING)
# model.sections["defeasibly"] contains flies(tweety) and ~flies(opus).
```

The reason that works is that `~flies(X) :- penguin(X)` is a *defeasible*
rule rather than a strict one. It is weaker than anything classical logic
would let you write — but strong enough to win against the competing
`flies(X) :- bird(X)` for the penguin case without contradicting the strict
fact that penguins are still birds. Gunray's job is to work out which
defeasible conclusions survive, which get blocked by opposing evidence, and
— if you ask — why.

## The conformance suite

Gunray is the Python evaluator behind
[`ctoth/datalog-conformance-suite`](https://github.com/ctoth/datalog-conformance-suite),
a fixed corpus of cases that pins down how a conforming defeasible evaluator
is supposed to behave. The suite is the spec; Gunray is a readable
implementation you can run against it. If a case and the engine disagree,
one of them is wrong and the test run says which.

Under the hood, Gunray is a semi-naive Datalog core with stratified negation,
a defeasible layer implementing both ambiguity-blocking and
ambiguity-propagating semantics, and a closure engine covering rational,
lexicographic, and relevant closure (plus KLM `Or`) for the fragment the
suite exercises. The closure engine is intentionally narrow: it handles only
the zero-arity propositional fragment and rejects defeaters, superiority,
and explicit conflict sets at that path. Everything non-trivial — defeaters,
superiority, conflict sets, higher-arity literals — goes through the full
defeasible evaluator instead.

## Install

Python 3.11+ and [`uv`](https://docs.astral.sh/uv/). The conformance suite
is a git-pinned dependency in `pyproject.toml`, so you don't need a sibling
checkout:

```powershell
uv sync --extra dev
```

## Plain Datalog works too

`GunrayEvaluator.evaluate` dispatches on the input type, so the same object
handles strict programs:

```python
from datalog_conformance.schema import Program
from gunray import GunrayEvaluator

model = GunrayEvaluator().evaluate(Program(
    facts={"edge": {("a", "b"), ("b", "c")}},
    rules=[
        "path(X, Y) :- edge(X, Y).",
        "path(X, Z) :- edge(X, Y), path(Y, Z).",
    ],
))
# model.facts["path"] == {("a", "b"), ("b", "c"), ("a", "c")}
```

If you'd rather skip the dispatcher, `SemiNaiveEvaluator` and
`DefeasibleEvaluator` are exported from `gunray` directly.

## Traces: why did it decide that?

Defeasible reasoning is exactly the kind of thing where *what* was concluded
is less useful than *why*. Both engines can return a structured trace
alongside the model:

```python
from gunray import GunrayEvaluator, TraceConfig

model, trace = GunrayEvaluator().evaluate_with_trace(
    program, trace_config=TraceConfig(capture_derived_rows=True),
)
fires = trace.find_rule_fires(head_predicate="path")
```

Defeasible traces carry each proof attempt, its final classification
(`defeasibly`, `not_defeasibly`, `definitely`), the rule ids that supported
and attacked it, and the atoms in conflict. For theories with no defeasible
content, you get the strict Datalog trace in its place.

## Running the tests

Local unit suite:

```powershell
uv run pytest tests -q
```

Full conformance corpus against Gunray:

```powershell
uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.adapter.GunrayEvaluator -q
```

To pick apart a single defeasible case by hand:

```powershell
uv run python scripts/show_defeasible_case.py --help
```

## Where things live

- [`adapter.py`](src/gunray/adapter.py) — `GunrayEvaluator`, the suite-facing dispatcher
- [`evaluator.py`](src/gunray/evaluator.py) — semi-naive Datalog engine
- [`defeasible.py`](src/gunray/defeasible.py) — defeasible evaluator
- [`closure.py`](src/gunray/closure.py) — reduced closure and KLM `Or`
- [`trace.py`](src/gunray/trace.py) — trace types and helpers
- [`semantics.py`](src/gunray/semantics.py) — equality, ordering, and arithmetic routed through one place
- [`tests/test_conformance.py`](tests/test_conformance.py) — conformance harness
