# Full-scope gunray code review — 2026-04-16

**GOAL:** Q asked for full code review of gunray library, paper-referenced,
deliverables under `reviews/2026-04-16-full-review/`.

**DONE:**
- Created `reviews/2026-04-16-full-review/`.
- Read `notes/what_sucks_review.md`, `notes/refactor_complete.md`,
  `README.md`, `pyproject.toml`, `__init__.py`, `out` (= git log snapshot).
- Dispatched 6 parallel subagents. Five landed clean deliverables; one
  (Surface F adversary) returned an in-progress checkpoint but claims it
  will write the file. Need to verify.

**FILES (deliverables landed):**
- `reviews/2026-04-16-full-review/surface-a-core-semantics.md` ✓
- `reviews/2026-04-16-full-review/surface-b-datalog-engine.md` ✓
- `reviews/2026-04-16-full-review/surface-c-closure.md` ✓
- `reviews/2026-04-16-full-review/surface-d-io-and-api.md` ✓
- `reviews/2026-04-16-full-review/surface-e-tests.md` ✓
- `reviews/2026-04-16-full-review/surface-f-citations.md` — UNCONFIRMED

**KEY FINDINGS so far (from subagent summaries — verify when synthesizing):**

1. **refactor_complete.md is stale.** Per Surface E: actual unit 139/0, conformance
   282/0/10/3 (not 136/0/1 and 250/44/1). The 44-failure breakdown (28 nemo, 9 Def 3.1
   cond 2 etc.) no longer applies — nemo_negation fixed in `3ea1a00` by deleting the
   safety check (Nemo-style existential reading). Closure faithfulness test passes.
2. **Strict-only shortcut skips Π non-contradiction** (Surface A, A2; Surface D finding 5).
   `defeasible.py:294-313` — `~p :- q.` with facts `p.` `q.` puts both `p` and `~p`
   in `definitely`. Also ignores `theory.conflicts`.
3. **GeneralizedSpecificity missing empty-rules guard** (Surface A, A1). `preference.py:138-141`
   — defeasible arg can out-specify strict knowledge via vacuous coverage.
4. **Trace upgrade never shipped** (Surface A A5, Surface D #3). `DialecticalNode` built
   and marked in `defeasible.py:143`, then discarded. `DefeasibleTrace` is still flat
   rule-fire records. `notes/what_sucks_review.md` point 4 remains unresolved.
5. **Public-surface export gap confirmed.** `GeneralizedSpecificity`, `SuperiorityPreference`,
   `CompositePreference` not in `__init__.__all__` though README imports them.
6. **`Policy.PROPAGATING` fully removed** from enum, not deprecated. Callers get raw
   `AttributeError`, not GunrayError. No test for the message.
7. **~110 LOC dead code in closure.py** (Surface C): `_lexicographic_preferred_default_sets`
   (57), `_formula_branches` (27), `_formula_true_in_closure` (24), `_world_satisfies_rules` (5).
   Two propositional engines coexist. File is 821 LOC, not 699 — baseline figure stale.
8. **`src/gunray.tar`** is stale pre-refactor snapshot, 300KB. Delete.
9. **`out` file** in repo root is captured git log. Probably delete / gitignore.
10. **Several vacuous property tests** (Surface E): `test_hypothesis_mark_is_local` is
    `mark(x) == mark(x)`; `test_hypothesis_build_arguments_is_monotonic_in_facts` adds
    a fact no rule references; `test_render.py:127-142` would pass on `return ""`.
11. **Performance bomb** (Surface E): `dialectic._disagreeing_subarguments` calls
    `build_arguments(theory)` per counter-argument check. Root of the deselected
    `spindle_racket_query_long_chain` timeout. No test bounds call count.
12. **`_unify` uses `is None` instead of `_UNBOUND` sentinel** (Surface B B2). Conflates
    missing key with Python None.
13. **`add_values` silent string coercion** on mixed types (Surface B B4; `semantics.py:38-43`).
14. **Private `_match_positive_body`** imported across modules (Surface B B5). Architecture leak.
15. **`nemo_negation` "fix" was silent deletion of safety check** (Surface B B1). Policy
    concern — engine silently adopted Nemo-style existential reading, only documented
    in `tests/conftest.py:92-96`.

**STUCK:** Surface F adversary may not have finished. Need to check the file exists
and has content.

**NEXT:**
1. Check surface-f-citations.md exists / was written.
2. If missing, either let it finish (agent id `aaf21556e785f54b3`) or synthesize
   without citation audit.
3. Read all 6 surface reports directly to verify subagent summaries.
4. Write `reviews/2026-04-16-full-review/SUMMARY.md` with prioritized top-level list.
5. Deliver to Q in HK-47 voice with pointers into the review folder.

## 2026-04-16 — Delivery checkpoint

**DONE:**
- Surface F was missing — the first adversary was spooked by a "don't write markdown"
  hook. Re-dispatched as scout with explicit "write the file" instruction; landed clean.
- Verified top-3 severity claims by direct source read before writing the summary:
  - A2 strict-only Π cond 2 skip: CONFIRMED at `defeasible.py:294-313` — no
    contradiction check, `theory.conflicts` also ignored.
  - A1 GenSpec empty-rules missing guard: CONFIRMED at `preference.py:138-141` —
    vacuous `True` in one direction + `False` in reverse → strictly prefers
    defeasible over strict with empty rules. SuperiorityPreference has the guard
    (line 232); GenSpec doesn't.
  - F `disagrees` drops facts: CONFIRMED at `disagreement.py:68-87` —
    `strict_context` is rules only, no facts parameter. Def 3.3 says `Π ∪ {h1,h2}`.
- Wrote `reviews/2026-04-16-full-review/SUMMARY.md` — 7 critical/high, 9 medium,
  6 low/hygiene, open-decisions list for Q, suggested priority order.
- All 7 tasks closed.

**FILES:**
- `reviews/2026-04-16-full-review/` — 7 files total (6 surfaces + SUMMARY)

**WHAT WORKED:**
- Parallel dispatch of 6 specialized subagents across coherent code surfaces.
  Each agent stayed in its lane and produced actionable file:line findings.
- Re-dispatching the spooked adversary as a scout with a harvest-and-continue
  prompt (carried the first agent's verified observations forward) saved the
  audit without re-doing work.
- Verifying the top-severity claims myself before amplifying them. The three
  flagship bugs in SUMMARY are eyeball-confirmed, not hearsay.

**WHAT DIDN'T:**
- First Surface F adversary agent interpreted a generic system prompt rule
  ("NEVER create documentation files unless explicitly requested") as overriding
  the explicit "write this deliverable file" prompt. The rule should have been
  satisfied by Q's explicit `./reviews` request; agent was over-conservative.
  Re-dispatch with harder language resolved it.
- The refactor's own completion notes (`notes/refactor_complete.md`) drifted
  behind reality in 2 days — cited stale conformance numbers and a pre-existing
  failing test that has since been fixed. Flagged in SUMMARY §8.

**NEXT:**
- Wait for Q's decisions on the 5 open questions in SUMMARY.
- Fix order if Q greenlights: (1) strict-only Π check, (2) GenSpec empty-rules
  guard, (3) disagrees Π facts, (4) Nemo semantics policy call, (5) export gap,
  (6) perf hoist, (7) everything else.

## 2026-04-16 — Workstream authoring

**Q's decisions received:**
- #9 closure: YAGNI, delete dead code. Defer z3 closure as separate work.
- #12 add_values: raise, not warn.
- Trace upgrade: Option B (RESTRUCTURE, break propstore, migrate propstore
  at `C:\Users\Q\code\propstore\`).
- Nemo mode: Option B (orthogonal kwarg + new `NegationSemantics` enum,
  default `SAFE`).

**DONE (workstream authoring):**
- Created `reviews/2026-04-16-full-review/workstream/` directory.
- Verified `trace.py` current shape (flat proof_attempts/classifications
  lists with ProofAttemptTrace/ClassificationTrace dataclasses).
- Pulled `git show 3ea1a00` — confirmed the safety check deletion is 2
  lines in `_validate_program` gated on `_variables_in_atom`. Restoration
  is trivial; enum gate is small.
- Wrote 10 of 18 workstream files:
  - README.md, GROUND_RULES.md, EXIT_CRITERIA.md
  - P0-T1-hygiene.md (tarball/out/gitignore)
  - P1-T1-strict-only-pi.md (ContradictoryStrictTheoryError)
  - P1-T2-genspec-empty-rules.md (mirror SuperiorityPreference guard)
  - P1-T3-disagrees-pi-facts.md (plumb facts through, Option A)
  - P2-T1-preference-exports.md (5-line __all__ fix)
  - P2-T2-trace-upgrade.md (restructure + propstore migration)
  - P2-T3-nemo-mode.md (NegationSemantics enum + gated safety)

**REMAINING (to write, 8 files):**
- P3-T1-unify-sentinel.md
- P3-T2-add-values-raise.md
- P3-T3-freeze-dataclasses.md
- P3-T4-vacuous-tests.md
- P4-T1-closure-dead-code.md
- P4-T2-perf-hoist.md
- P4-T3-private-imports.md
- P4-T4-citations.md

**FORMAT established:** each task file has Context, Files, Red (failing
test with concrete assertions and Hypothesis properties), Green
(concrete code direction), Acceptance (uv run commands with expected
results), Commits (message templates), Anchors (back-links to
SUMMARY/surface reports/papers).

**STUCK:** Nothing. Proceeding with remaining 8 task files.

**NEXT:**
- Write the 8 remaining task files.
- Report back to Q with file list + any design gaps surfaced during
  authoring.

## Post-workstream delta

- P4-T1 closure cull: `src/gunray/closure.py` was 671 LOC immediately before
  the deletion slice and 549 LOC after removing the dead helpers. The earlier
  review note's 821 LOC observation was stale by the time this slice ran.
- P4-T4 final hygiene: standard algorithm citation gaps are closed in
  `evaluator.py`, `stratify.py`, `closure.py`, `parser.py`, and `schema.py`.
  `_variables_in_atom` is live in `_internal._validate_program`; parser
  identifiers now reject malformed predicates/terms while preserving suite
  namespace-prefixed predicates; conformance rule translation now rejects
  unknown suite rule fields instead of silently dropping them.
