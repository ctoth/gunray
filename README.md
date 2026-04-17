# Gunray

Gunray is a defeasible logic engine — one that can make sense of rules
that contradict each other. Tell it *birds fly*, tell it *penguins
don't fly*, hand it a bird that happens to also be a penguin, and it
does the right thing:

```python
from gunray import DefeasibleTheory, GunrayEvaluator, Policy, Rule

theory = DefeasibleTheory(
    facts={"bird": {("tweety",), ("opus",)}, "penguin": {("opus",)}},
    strict_rules=[Rule(id="s1", head="bird(X)", body=["penguin(X)"])],
    defeasible_rules=[
        Rule(id="r1", head="flies(X)",  body=["bird(X)"]),
        Rule(id="r2", head="~flies(X)", body=["penguin(X)"]),
    ],
)

model = GunrayEvaluator().evaluate(theory, Policy.BLOCKING)
# model.sections["defeasibly"] contains flies(tweety) and ~flies(opus).
```

`~flies(X) :- penguin(X)` is a *defeasible* rule, not a strict one.
It's weaker than anything classical logic would let you write — but
strong enough to win against `flies(X) :- bird(X)` on the penguin case
without contradicting the strict fact that penguins are still birds.
Gunray's job is to work out which defeasible conclusions survive, which
get blocked by opposing evidence, and — if you ask — exactly why.

## What Gunray implements

The defeasible pipeline is Garcia & Simari's 2004 DeLP, run verbatim:

- **Arguments** `⟨A, h⟩` — derivation, non-contradiction, minimality
  (Def 3.1). Enumerated by `gunray.arguments.build_arguments`.
- **Dialectical trees** (Def 5.1) built with the Def 4.7
  acceptable-argumentation-line conditions — concordance of supporting
  and interfering sets, sub-argument exclusion, block-on-block ban —
  enforced *during* construction rather than post-hoc.
- **Preference** is
  `CompositePreference(SuperiorityPreference, GeneralizedSpecificity)`:
  explicit user-supplied priority pairs (Garcia 04 §4.1) first, with
  generalized specificity (Simari 92 Lemma 2.4) as the fallback,
  composed under first-criterion-to-fire semantics so the composite is
  still a strict partial order.
- **Marking** is Procedure 5.1, post-order U/D.
- **Answers** are the four-valued `answer` of Def 5.3 —
  `YES` / `NO` / `UNDECIDED` / `UNKNOWN` — projected into the
  `definitely` / `defeasibly` / `not_defeasibly` / `undecided` sections
  of `DefeasibleModel`.

Strict-only theories (no defeasible rules, defeaters, or superiority)
take a shortcut around the argument pipeline and run through the
semi-naive Datalog engine — but *only after* Π consistency is checked.
If the strict closure derives any `h, ~h` pair (or a pair listed in
`conflicts`), `GunrayEvaluator` raises
`ContradictoryStrictTheoryError` rather than returning an inconsistent
model.

The legacy closure engine in `closure.py` — rational, lexicographic,
and relevant closure plus KLM `Or` — still covers the zero-arity
propositional fragment the conformance suite exercises. It's a
separate path for the cases it was built for.

## What Gunray does *not* implement

Scope is honest. The conformance suite at
[`ctoth/datalog-conformance-suite`](https://github.com/ctoth/datalog-conformance-suite)
contains fixtures Gunray explicitly does not support:

- **Antoniou 2007 ambiguity propagation.** Garcia 04's dialectical tree
  is blocking; the propagating reading comes from Antoniou's DR-Prolog
  meta-program and has no seam in this pipeline. `Policy.PROPAGATING`
  was deprecated — see `notes/policy_propagating_fate.md`.
- **Spindle implicit-`not_defeasibly` projection** for zero-arity
  head literals.
- **Spindle partial-dominance superiority**, which relaxes Garcia 04
  §4.1's all-rules-dominate requirement.

These fixtures are marked out-of-contract in the test harness, not
silently counted as passes.

## Install

Python 3.11+ and [`uv`](https://docs.astral.sh/uv/). The base runtime
has zero dependencies:

```powershell
uv sync
```

For development, tests, and the conformance suite:

```powershell
uv sync --extra dev
```

## One dispatcher, two engines

`GunrayEvaluator.evaluate` dispatches on the input type, so the same
object handles plain Datalog:

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
`DefeasibleEvaluator` are exported from `gunray` directly. The closure
engine is reachable as `gunray.closure.ClosureEvaluator`.

### Input types are frozen and validated

`Rule`, `DefeasibleTheory`, `Program`, `Model`, and `DefeasibleModel`
are all `frozen=True, slots=True`. Construction is not a free action —
it validates. `Rule(id="", head="...")` raises; a
`DefeasibleTheory.superiority` pair naming a rule id that doesn't exist
in `strict_rules`, `defeasible_rules`, or `defeaters` raises.
Schema violations never become silent evaluator mysteries.

## Negation semantics: `SAFE` vs `NEMO`

Rules with variables in negated body literals have two competing
readings in the literature. Gunray ships both:

```python
from gunray import GunrayEvaluator, NegationSemantics, Program

model = GunrayEvaluator().evaluate(
    program,
    negation_semantics=NegationSemantics.NEMO,
)
```

- `NegationSemantics.SAFE` — the default. Apt-Blair-Walker 1988
  stratified-Datalog safety: every variable in a negated body literal
  must be bound by a positive body literal. Unsafe programs raise
  `SafetyViolationError`.
- `NegationSemantics.NEMO` — the Nemo 2024 reading (Ivliev, Gerlach,
  Meusel, Steinberg, and Kroetzsch, KR 2024,
  [doi:10.24963/kr.2024/70](https://doi.org/10.24963/kr.2024/70)):
  variables in negated literals are interpreted existentially over the
  active Herbrand universe. Used by the conformance suite for the
  Nemo-style fixtures.

Choose deliberately. The two semantics disagree on meaningful cases.

## Traces: why did the engine decide that?

Defeasible reasoning is exactly the kind of thing where *what* was
concluded is less useful than *why*. Both engines return a structured
trace alongside the model:

```python
from gunray import GunrayEvaluator, TraceConfig

model, trace = GunrayEvaluator().evaluate_with_trace(
    theory, trace_config=TraceConfig(capture_derived_rows=True),
)

# Defeasible traces carry the full argument pipeline output.
for argument in trace.arguments:
    ...

# For any atom in the model, the dialectical tree retained for it:
tree    = trace.tree_for(flies_tweety)
marking = trace.marking_for(flies_tweety)  # "U" or "D"
args    = trace.arguments_for_conclusion(flies_tweety)
```

For plain Datalog programs, the trace is a stratum-by-stratum
rule-fire log with `find_rule_fires` helpers. For theories with no
defeasible content, you get the strict Datalog trace in its place.

## Query a single literal

When you want one literal classified rather than the whole model, go
straight to the four-valued `answer` and, if you want to see the shape
of the dialectical tree behind the verdict, `render_tree`:

```python
from gunray import (
    Answer, DefeasibleTheory, Policy, Rule,
    GunrayEvaluator, GeneralizedSpecificity,
    answer, build_arguments, build_tree, mark, render_tree,
)
from gunray.types import GroundAtom

theory = DefeasibleTheory(
    facts={"bird": {("tweety",), ("opus",)}, "penguin": {("opus",)}},
    strict_rules=[Rule(id="r0", head="bird(X)", body=["penguin(X)"])],
    defeasible_rules=[
        Rule(id="r1", head="flies(X)",  body=["bird(X)"]),
        Rule(id="r2", head="~flies(X)", body=["penguin(X)"]),
    ],
)

model = GunrayEvaluator().evaluate(theory, Policy.BLOCKING)
assert ("tweety",) in model.sections["defeasibly"]["flies"]
assert ("opus",)   in model.sections["defeasibly"]["~flies"]

criterion    = GeneralizedSpecificity(theory)
flies_tweety = GroundAtom(predicate="flies", arguments=("tweety",))
flies_opus   = GroundAtom(predicate="flies", arguments=("opus",))

assert answer(theory, flies_tweety, criterion) is Answer.YES
assert answer(theory, flies_opus,   criterion) is Answer.NO

for arg in build_arguments(theory):
    if arg.conclusion == flies_tweety:
        tree = build_tree(arg, criterion, theory)
        print(render_tree(tree))
        assert mark(tree) == "U"  # warranted
        break
```

`Answer.YES` means the literal is warranted (tree marks `U`),
`Answer.NO` means the complement is warranted, `Answer.UNDECIDED`
means arguments exist on both sides and neither wins, `Answer.UNKNOWN`
means the predicate is not in the language of the theory.

`render_tree` returns a Unicode string suitable for pasting into logs
or test failure messages. It is how the defeasible evaluator's
internals become legible when a case disagrees with your intuition.

## Running the tests

Local unit suite:

```powershell
uv run pytest tests -q
```

Supported conformance corpus:

```powershell
uv run pytest tests/test_conformance.py \
  --datalog-evaluator=gunray.conformance_adapter.GunrayConformanceEvaluator -q
```

The harness skips documented out-of-contract fixtures (see the "What
Gunray does not implement" section above) rather than silently counting
them as passes.

To pick apart a single defeasible case by hand:

```powershell
uv run python scripts/show_defeasible_case.py --help
```

Static analysis (pyright strict, ruff, format check) must stay clean:

```powershell
uv run pyright
uv run ruff check
uv run ruff format --check
```

## Where things live

Top-level surface under `src/gunray/`:

- [`adapter.py`](src/gunray/adapter.py) — `GunrayEvaluator`, the
  dispatcher over `Program` / `DefeasibleTheory` / closure policies.
- [`defeasible.py`](src/gunray/defeasible.py) — the Garcia/Simari
  argument-and-tree pipeline.
- [`evaluator.py`](src/gunray/evaluator.py) — semi-naive Datalog
  engine with stratified negation.
- [`closure.py`](src/gunray/closure.py) — KLM rational / lexicographic
  / relevant closure plus the `Or` rule for the propositional
  fragment.
- [`conformance_adapter.py`](src/gunray/conformance_adapter.py) —
  optional bridge into `datalog-conformance-suite`.

Argument pipeline internals:

- [`arguments.py`](src/gunray/arguments.py) — `Argument`,
  `build_arguments`, sub-argument tests.
- [`dialectic.py`](src/gunray/dialectic.py) — counter-argument,
  defeater classification, tree construction, marking, render.
- [`answer.py`](src/gunray/answer.py) — four-valued `Answer` (Def 5.3).
- [`disagreement.py`](src/gunray/disagreement.py) — `complement`,
  `disagrees`, `strict_closure`.
- [`preference.py`](src/gunray/preference.py) — `TrivialPreference`,
  `GeneralizedSpecificity`, `SuperiorityPreference`,
  `CompositePreference`.

Supporting infrastructure:

- [`schema.py`](src/gunray/schema.py) — `Rule`, `DefeasibleTheory`,
  `Program`, `Model`, `DefeasibleModel`, `Policy`,
  `NegationSemantics`.
- [`trace.py`](src/gunray/trace.py) — `TraceConfig`, `DatalogTrace`,
  `DefeasibleTrace`.
- [`types.py`](src/gunray/types.py) — frozen value types
  (`GroundAtom`, variables, terms).
- [`errors.py`](src/gunray/errors.py) — `GunrayError` hierarchy
  with conformance-compatible codes.
- [`parser.py`](src/gunray/parser.py) — DeLP surface-syntax parser.
- [`stratify.py`](src/gunray/stratify.py) — Apt-Blair-Walker
  stratification via Tarjan + Kahn.
- [`relation.py`](src/gunray/relation.py) — indexed relations for the
  semi-naive engine.
- [`compiled.py`](src/gunray/compiled.py) — compiled matcher fast
  path, cross-checked against the generic matcher in tests.
- [`semantics.py`](src/gunray/semantics.py) — equality, ordering, and
  arithmetic routed through one place.
- [`_internal.py`](src/gunray/_internal.py) — shared cross-module
  helpers (intentionally named; no private-attribute imports across
  module boundaries).

## Citations

The engine is anchored in a small, deliberate paper set under
[`papers/`](papers/):

- **Garcia & Simari 2004**, *Defeasible Logic Programming* — the
  DeLP pipeline this engine implements.
- **Simari & Loui 1992**, *A Mathematical Treatment of Defeasible
  Reasoning* — generalized specificity.
- **Morris, Ross & Meyer 2020**, *Defeasible Disjunctive Datalog* —
  rational closure construction.
- **Antoniou 2007**, *Defeasible Reasoning on the Semantic Web* —
  ambiguity-propagating reference (not implemented; explicitly
  out-of-contract).
- **Ivliev et al. 2024**, *Nemo: Your Friendly and Versatile Rule
  Reasoning Toolkit* (KR 2024) — Nemo-style negation semantics.

Citations in source point to definition numbers and page references,
not just paper titles; grep for `Def 3.1`, `Def 4.7`, `Procedure 5.1`,
`Lemma 2.4`.
