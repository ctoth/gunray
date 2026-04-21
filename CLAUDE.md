# Gunray — project guidance for Claude

Global principles live in `~/.claude/CLAUDE.md.d/`. What follows is
*project-specific*: the things you need to know to work in this repo
without rediscovering them every session.

## What this repo is

A defeasible logic engine. The public story is in [`README.md`](README.md);
read it first. The short version:

- `DefeasibleEvaluator` runs the Garcia & Simari 2004 DeLP pipeline
  (arguments → dialectical trees → Procedure 5.1 marking → four-valued
  answer).
- `SemiNaiveEvaluator` runs plain stratified Datalog.
- `ClosureEvaluator` runs KLM rational/lexicographic/relevant closure
  on the propositional fragment.
- `GunrayEvaluator` dispatches between them on input type and policy.

## Where truth lives

- **The papers** (`papers/`) are the source of truth. When citing
  behavior in a commit, PR, or comment, name the definition and page
  number, not the paper title alone. Existing source citations follow
  that format; match it.
- **`reviews/2026-04-16-full-review/`** is the current authoritative
  audit of the codebase. `SUMMARY.md` is the executive view; the
  `surface-*` files are the per-module audits; `workstream/` is the
  (now-complete) remediation punch list. Read `SUMMARY.md` before
  planning non-trivial changes.
- **`notes/`** is the checkpoint log. Append — do not rewrite — when
  you're working on something that will outlive your session. Check
  existing notes on a topic before starting.

## Commands you will run often

Use `uv` — bare `python` is blocked by ward.

```powershell
uv run pytest tests -q
uv run pytest tests/test_conformance.py \
  --datalog-evaluator=gunray.conformance_adapter.GunrayConformanceEvaluator -q
uv run pyright
uv run ruff check
uv run ruff format --check
```

Exit criteria for any substantive change: unit suite green, conformance
suite green, pyright clean, ruff + format clean. No exceptions — this
was the workstream's bright line and it stays bright.

## Out-of-contract, on purpose

These conformance fixtures are *deliberately* not supported. Do not
"fix" them without an explicit semantic decision:

- Antoniou 2007 ambiguity-propagating fixtures. `Policy.PROPAGATING`
  was deprecated; re-introduction requires a new seam — see
  `notes/policy_propagating_fate.md`.
- Spindle implicit-`not_defeasibly` projection (zero-arity heads).
- Spindle partial-dominance superiority.

The harness marks them skip/deselect; that is the correct state.

## Negation semantics — two modes, by design

`NegationSemantics.SAFE` (default) enforces Apt-Blair-Walker safety and
raises `SafetyViolationError` on violations. `NegationSemantics.NEMO`
is the Nemo 2024 existential reading used by the conformance suite's
Nemo fixtures. They disagree on meaningful cases. Pick one consciously
per call; don't add a third.

## Things that bit prior agents

- **Strict-only fast path** (`defeasible.py:_is_strict_only_theory`)
  must enforce Π consistency before routing to the Datalog engine.
  `ContradictoryStrictTheoryError` is raised on `{h, ~h}` derivation
  or any `conflicts` overlap. Don't regress this — P1-T1 exists
  because it was broken once.
- **`GeneralizedSpecificity` empty-rules edge.** Strict arguments have
  empty rule sets. The preference check must not let a defeasible
  argument out-specify a strict one by vacuity. See `preference.py`
  and P1-T2.
- **`disagrees` must see Π facts, not just Π rules.** Garcia 04
  Def 3.3 is facts-plus-rules; passing only rules misses strict-rule
  firings that need facts as seeds. See P1-T3.
- **Cross-module private imports.** Shared helpers live in
  [`_internal.py`](src/gunray/_internal.py), not in peer modules'
  private-underscore names. No `from gunray.evaluator import _helper`.
- **Rule identity is theory-wide.** Rule IDs must be unique across strict
  and defeasible sections, and rule bodies are immutable tuples. Do not
  reintroduce list-backed rule bodies or per-section duplicate IDs.
- **Closure policies route through `ClosureEvaluator`.** `GunrayEvaluator`
  should dispatch closure-policy inputs to the closure engine, not delete
  the policy or fall through to defeasible evaluation.
- **Public conformance bridge only.** Adapter code must use public
  constructor surfaces. Do not reach into private `_core` attributes to
  satisfy tests or conformance harnesses.

## Style and tooling

- Pyright is strict, ruff is configured in `pyproject.toml`. Both
  stay clean at all times.
- Frozen dataclasses with slots throughout input types. Do not add
  mutable defaults; use factory functions (see `schema.py` for the
  pattern).
- Citation debt is real debt. Algorithms without source attribution
  (semi-naive evaluation, stratification, KLM `Or`, DeLP surface
  syntax) were the subject of P4-T4. New non-trivial algorithms need
  citations from day one — paper, section, page.

## When in doubt

Ask Q. Don't improvise semantics, don't silently relax safety, don't
delete skipped fixtures to claim a higher pass rate. The honesty of
the conformance harness is a feature of this codebase, not an
accident.
