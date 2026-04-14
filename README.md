# Gunray

Gunray is a defeasible logic engine — one that can make sense of rules that
contradict each other. Tell it *birds fly*, tell it *penguins don't fly*,
hand it a bird that happens to also be a penguin, and it does the right
thing:

```python
from gunray import DefeasibleTheory, GunrayEvaluator, Policy, Rule

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

Under the hood, `DefeasibleEvaluator` runs the Garcia & Simari 2004 §5
pipeline verbatim. `build_arguments` enumerates first-class `Argument`
structures `⟨A, h⟩` per Def 3.1 (derivation, non-contradiction, minimality).
For each argument, `build_tree` constructs the dialectical tree of Def 5.1
while enforcing the Def 4.7 acceptable-argumentation-line conditions
(concordance of the supporting and interfering sets, sub-argument
exclusion, and the block-on-block ban) during construction. `mark`
post-orders the tree under Procedure 5.1, and a literal is classified by
the four-valued `answer` of Def 5.3 — `YES` / `NO` / `UNDECIDED` /
`UNKNOWN` — projected into the `definitely` / `defeasibly` /
`not_defeasibly` / `undecided` sections that `DefeasibleModel` exposes.
Preference between conflicting arguments is
`CompositePreference(SuperiorityPreference, GeneralizedSpecificity)`:
explicit user-supplied priority pairs (Garcia 04 §4.1) are consulted
first, with generalized specificity (Simari 92 Lemma 2.4) as the
fallback, composed under first-criterion-to-fire semantics so the
composite is still a strict partial order. `render_tree` is a Unicode
debugger you can point at any dialectical tree when you want to see
exactly why a literal was warranted, blocked, or left undecided.

Strict-only theories (no defeasible rules, no defeaters, no superiority)
take a shortcut around the argument pipeline and run through the
semi-naive Datalog engine instead, because there is nothing for a
dialectical tree to chew on. The legacy closure engine in `closure.py`
— rational, lexicographic, and relevant closure plus KLM `Or` — still
covers the zero-arity propositional fragment the conformance suite
exercises, and is kept exactly as it was: a separate path for the
propositional cases it was built for.

## Install

Python 3.11+ and [`uv`](https://docs.astral.sh/uv/). The conformance suite
is not part of Gunray's base runtime install:

```powershell
uv sync
```

For development, tests, and suite-driven verification:

```powershell
uv sync --extra dev
```

## Plain Datalog works too

`GunrayEvaluator.evaluate` dispatches on the input type, so the same object
handles strict programs:

```python
from gunray import GunrayEvaluator, Program

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
uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.conformance_adapter.GunrayConformanceEvaluator -q
```

To pick apart a single defeasible case by hand:

```powershell
uv run python scripts/show_defeasible_case.py --help
```

## Where things live

- [`adapter.py`](src/gunray/adapter.py) — `GunrayEvaluator`, the Gunray-owned dispatcher
- [`conformance_adapter.py`](src/gunray/conformance_adapter.py) — optional suite bridge
- [`evaluator.py`](src/gunray/evaluator.py) — semi-naive Datalog engine
- [`defeasible.py`](src/gunray/defeasible.py) — defeasible evaluator
- [`closure.py`](src/gunray/closure.py) — reduced closure and KLM `Or`
- [`trace.py`](src/gunray/trace.py) — trace types and helpers
- [`semantics.py`](src/gunray/semantics.py) — equality, ordering, and arithmetic routed through one place
- [`tests/test_conformance.py`](tests/test_conformance.py) — conformance harness
