# Gunray architecture

Contributor-facing map of the codebase. The [README](README.md) is the
user-facing introduction; this document is the internals reference.
Global principles live in [`CLAUDE.md`](CLAUDE.md); the full audit lives
in [`reviews/2026-04-16-full-review/`](reviews/2026-04-16-full-review/).

## Overview

`GunrayEvaluator` ([`adapter.py`](src/gunray/adapter.py)) dispatches on
input type over three engines:
`DefeasibleEvaluator` ([`defeasible.py`](src/gunray/defeasible.py))
for the García & Simari 2004 DeLP pipeline on `DefeasibleTheory`;
`SemiNaiveEvaluator` ([`evaluator.py`](src/gunray/evaluator.py)) for
stratified Datalog on `Program`; `ClosureEvaluator`
([`closure.py`](src/gunray/closure.py)) for KLM closure on the
propositional fragment. A strict-only fast path routes degenerate
defeasible theories into the Datalog engine — see below.

## The DeLP pipeline

The defeasible path is run verbatim from García & Simari 2004. Each
step lives in a named module:

- **Arguments** `⟨A, h⟩` — derivation, non-contradiction, minimality
  (García & Simari 2004 Def 3.1 p. 8). Enumerated by
  `build_arguments` in [`arguments.py`](src/gunray/arguments.py).
- **Dialectical trees** (García & Simari 2004 Def 5.1 p. 21) built
  under the Def 4.7 acceptable-argumentation-line conditions
  (García & Simari 2004 Def 4.7 p. 19) — concordance of supporting
  and interfering sets, sub-argument exclusion, block-on-block ban —
  enforced during construction in
  [`dialectic.py`](src/gunray/dialectic.py), not post-hoc.
- **Counter-arguments and defeaters.** `counter_argues`,
  `proper_defeater`, `blocking_defeater` in
  [`dialectic.py`](src/gunray/dialectic.py) — Def 4.1 / Def 4.2.
- **Disagreement.** `disagrees` in
  [`disagreement.py`](src/gunray/disagreement.py) — García & Simari
  2004 Def 3.3 p. 10: `h1` and `h2` disagree iff `Π ∪ {h1, h2}` is
  contradictory. `complement` and `strict_closure` support it.
- **Marking** is Procedure 5.1 post-order U/D in `mark`
  ([`dialectic.py`](src/gunray/dialectic.py)).
- **Answers** are the four-valued `Answer` of García & Simari 2004
  Def 5.3 p. 28 — `YES` / `NO` / `UNDECIDED` / `UNKNOWN` — exposed by
  `answer` in [`answer.py`](src/gunray/answer.py) and projected into
  the `yes` / `no` / `undecided` / `unknown` sections of
  `DefeasibleModel`. The pre-rewrite `definitely`, `defeasibly`, and
  `not_defeasibly` section names are not model fields.
- **Presumptions** (García & Simari 2004 §6.2 p. 32) are defeasible
  rules with an empty body, written `h -< true` in the DeLP surface
  syntax. `DefeasibleTheory.presumptions` carries them; they flow
  through the argument pipeline as ordinary defeasible rules.
- **Explanations** (García & Simari 2004 §6 p. 29). `explain` in
  [`dialectic.py`](src/gunray/dialectic.py) walks a marked
  dialectical tree and returns a prose transcript naming the
  supporting argument, each defeater considered, and the preference
  reason that decided every edge.

## Preference

Preference between arguments is
`CompositePreference(SuperiorityPreference, GeneralizedSpecificity)`
in [`preference.py`](src/gunray/preference.py).
`SuperiorityPreference` consults the user-supplied `superiority` pairs
on `DefeasibleTheory` (García & Simari 2004 §4.1 p. 17).
`GeneralizedSpecificity` is the fallback (Simari & Loui 1992 Lemma 2.4
p. 138). `CompositePreference` composes them with
first-criterion-to-fire semantics — the second criterion is consulted
only when the first is silent — which keeps the composite a strict
partial order. `TrivialPreference` (always False) is exported for
tests and for pure-dialectical-tree cases.

## Strict-only fast path

`DefeasibleEvaluator` recognises theories with no defeasible rules, no
defeaters, and no superiority as degenerate — they are classical
Datalog wearing a defeasible jacket. The fast path in
[`defeasible.py`](src/gunray/defeasible.py) routes them into
`SemiNaiveEvaluator` and mirrors every derived fact into the `yes`
section. It also populates the optional
argument view on `DefeasibleTrace`: every strict consequence is exposed
as a leaf `Argument(frozenset(), h)` with marking `U`.

The fast path runs **only after Π consistency is checked**. The strict
closure of Π is taken; if it contains any `h, ~h` pair — or any pair
listed in `DefeasibleTheory.conflicts` — the evaluator raises
`ContradictoryStrictTheoryError` rather than returning an inconsistent
model. This is load-bearing; see the pitfalls section below.

## Closure engine

[`closure.py`](src/gunray/closure.py) is a standalone KLM-style engine
covering rational, lexicographic, and relevant closure plus KLM `Or`
(Kraus-Lehmann-Magidor 1990). Zero-arity propositional fragment only —
no variables, no unification. Reachable as
`gunray.closure.ClosureEvaluator` and dispatched to by
`GunrayEvaluator` for `ClosurePolicy` inputs; scope is the
conformance-suite cases it was built for.

## Public policy and budget boundary

`schema.MarkingPolicy` and `schema.ClosurePolicy` are separate enums.
`MarkingPolicy.BLOCKING` selects the García/Simari dialectical-tree
marking path. `ClosurePolicy.RATIONAL_CLOSURE`,
`ClosurePolicy.LEXICOGRAPHIC_CLOSURE`, and
`ClosurePolicy.RELEVANT_CLOSURE` select the propositional KLM closure
engine. `DefeasibleEvaluator.evaluate(...)` and
`evaluate_with_trace(...)` therefore accept keyword-only
`marking_policy=...` and `closure_policy=...`; the old mixed `Policy`
surface is gone.

`evaluate_with_trace` is the canonical defeasible entry point. The
returned `DefeasibleTrace` carries the single grounding pass as
`trace.grounding_inspection`, plus `arguments`, `trees`, and `markings`
when the dialectical or strict-only paths construct them. `evaluate` is
only a convenience wrapper that discards the trace.

The dialectical path accepts `max_arguments: int | None`. If exact
argument enumeration would exceed that budget, Gunray raises
`EnumerationExceeded`. The exception carries `partial_arguments` and,
from `evaluate_with_trace`, a `partial_trace` containing those partial
arguments and the grounding inspection. Partial results are incomplete;
the only exact continuation is to rerun with a larger budget.

`DefeasibleTheory.superiority` is validated at construction time as an
irreflexive acyclic relation over declared rule ids. Self-pairs and
cycles are rejected before preference closure is computed.

Section projection and generalized specificity remain owned by the
García 2004 / Simari 1992 path. The section-projection contract is now
the Garcia Def 5.3 surface: `yes`, `no`, `undecided`, and `unknown`.
`DefeasibleTrace` carries strict consequences, dialectical trees,
markings, and `defeater_probed_atoms` for callers that need provenance
or inspection beyond those four answers.

## Out-of-contract

The conformance harness at
[`ctoth/datalog-conformance-suite`](https://github.com/ctoth/datalog-conformance-suite)
contains fixtures Gunray deliberately does not support. They are
marked skip/deselect, not silently counted as passes:

- **Antoniou 2007 ambiguity propagation.** García 04's dialectical
  tree is blocking; the propagating reading comes from Antoniou's
  DR-Prolog meta-program and has no seam in this pipeline.
  `Policy.PROPAGATING` was deprecated — see
  [`notes/policy_propagating_fate.md`](notes/policy_propagating_fate.md).
- **Spindle implicit-`not_defeasibly` projection** for zero-arity head
  literals. This is a conformance-suite legacy expectation, not a
  Gunray model section.
- **Spindle partial-dominance superiority**, which relaxes García 04
  §4.1's all-rules-dominate requirement.

Re-introducing any of these requires an explicit semantic decision, a
new seam, and paper citations. Do not "fix" the fixtures in place.

## Module layout

Top-level surface under `src/gunray/`:

- [`adapter.py`](src/gunray/adapter.py) — `GunrayEvaluator`,
  dispatcher over `Program` / `DefeasibleTheory` / closure policies.
- [`defeasible.py`](src/gunray/defeasible.py) — the García/Simari
  argument-and-tree pipeline plus the strict-only fast path.
- [`evaluator.py`](src/gunray/evaluator.py) — semi-naive Datalog
  engine with stratified negation.
- [`closure.py`](src/gunray/closure.py) — KLM rational / lexicographic
  / relevant closure plus `Or` for the propositional fragment.
- [`conformance_adapter.py`](src/gunray/conformance_adapter.py) —
  bridge into `datalog-conformance-suite`.

Argument pipeline internals:

- [`arguments.py`](src/gunray/arguments.py) — `Argument`,
  `build_arguments`, sub-argument tests.
- [`dialectic.py`](src/gunray/dialectic.py) — counter-argument,
  defeater classification, tree construction, marking, render,
  explain.
- [`answer.py`](src/gunray/answer.py) — four-valued `Answer`
  (García & Simari 2004 Def 5.3 p. 28).
- [`disagreement.py`](src/gunray/disagreement.py) — `complement`,
  `disagrees`, `strict_closure`.
- [`preference.py`](src/gunray/preference.py) — `TrivialPreference`,
  `GeneralizedSpecificity`, `SuperiorityPreference`,
  `CompositePreference`.

Supporting infrastructure:

- [`schema.py`](src/gunray/schema.py) — `Rule`, `DefeasibleTheory`,
  `Program`, `Model`, `DefeasibleModel`, `MarkingPolicy`,
  `ClosurePolicy`, `NegationSemantics`. Frozen dataclasses with slots;
  construction validates.
- [`trace.py`](src/gunray/trace.py) — `TraceConfig`, `DatalogTrace`,
  `DefeasibleTrace`.
- [`types.py`](src/gunray/types.py) — frozen value types
  (`GroundAtom`, variables, terms).
- [`errors.py`](src/gunray/errors.py) — `GunrayError` hierarchy with
  conformance-compatible codes.
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
  helpers. See the pitfalls section: peer modules must not import
  private-underscore names from each other.

## Implementation notes (pitfalls)

Each of the following exists because it was broken once. They are
load-bearing, not ornamental.

- **Strict-only fast path must enforce Π consistency.**
  `_is_strict_only_theory` in
  [`defeasible.py`](src/gunray/defeasible.py) checks Π consistency
  before routing to the Datalog engine and raises
  `ContradictoryStrictTheoryError` on `{h, ~h}` derivation or any
  `DefeasibleTheory.conflicts` overlap. Without this, a theory with
  strict rule `~p(X) :- q(X).` plus facts `{p(a), q(a)}` would land
  `p(a)` and `~p(a)` both in `definitely`. Don't regress this.
- **`GeneralizedSpecificity` empty-rules edge.** Strict arguments
  have empty rule sets. The `_covers` helper in
  [`preference.py`](src/gunray/preference.py) must not let a
  defeasible argument out-specify a strict one by vacuity. The guard
  mirrors `SuperiorityPreference`'s explicit empty-rules check.
- **`disagrees` must see Π facts, not just Π rules.** García &
  Simari 2004 Def 3.3 p. 10 defines disagreement in terms of
  `Π ∪ {h1, h2}` where `Π` is strict rules **plus** facts. Callers
  in [`dialectic.py`](src/gunray/dialectic.py) must seed the closure
  with `DefeasibleTheory.facts` (or encode them as zero-body strict
  rules); passing only strict rules misses strict-rule firings that
  need facts as seeds.
- **No cross-module private imports.** Shared helpers live in
  [`_internal.py`](src/gunray/_internal.py). No
  `from gunray.evaluator import _helper`, no
  `from gunray.arguments import _force_strict_for_closure`. If two
  modules need the same helper, promote it to `_internal.py`. Public
  grounding value types live in
  [`grounding_types.py`](src/gunray/grounding_types.py); the grounding
  inspector reads the shared grounder result instead of re-parsing and
  re-grounding independently.
