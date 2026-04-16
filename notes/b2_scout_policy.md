# B2.1 — Policy usage scout progress

## 2026-04-13

### GOAL
Find every call site of `Policy.BLOCKING` / `Policy.PROPAGATING` /
`AmbiguityPolicy` / `attacker_basis` across gunray + propstore +
conformance fixtures. Decide verdict matrix for deprecate / map /
something-else. Produce `reports/b2-scout-policy.md`.

### DONE (observed)
- Gunray `src/gunray/schema.py:36-40` defines Policy enum with
  BLOCKING, PROPAGATING, RATIONAL_CLOSURE, LEXICOGRAPHIC_CLOSURE,
  RELEVANT_CLOSURE.
- Gunray `src/gunray/defeasible.py:51` — `del policy` IMMEDIATELY on
  entry to `evaluate_with_trace`. The parameter has ZERO runtime
  effect in the B1 dialectical-tree path. Comment claims it is
  "honored by the dialectical-tree path" — FALSE; it is deleted.
- Gunray `src/gunray/dialectic.py` — `build_tree`, `mark`, `answer`
  take NO policy parameter. The dialectical-tree machinery is
  policy-agnostic.
- Gunray `src/gunray/adapter.py:34,53` — routes closure policies to
  ClosureEvaluator, else calls `_defeasible.evaluate(theory, policy)`
  which ignores it.
- Gunray `src/gunray/closure.py` — uses policy ONLY to distinguish
  RATIONAL / LEXICOGRAPHIC / RELEVANT closure. Does not touch
  BLOCKING / PROPAGATING.
- Gunray tests `tests/test_trace.py`, `tests/test_defeasible_evaluator.py`,
  `scripts/show_defeasible_case.py` — every gunray caller passes
  `Policy.BLOCKING`. Zero passes of PROPAGATING anywhere in gunray.
- Propstore `propstore/grounding/grounder.py:79` — `ground()` accepts
  `policy: Policy = Policy.BLOCKING` and forwards to
  `GunrayEvaluator().evaluate(theory, policy)`. Docstring explicitly
  says "Phase 1 theories cannot diverge between BLOCKING and
  PROPAGATING".
- Propstore `tests/test_grounding_grounder.py:640-680` — the ONLY
  real PROPAGATING call site in the entire codebase. Smoke test
  that passes `Policy.PROPAGATING` and asserts the call returns a
  valid bundle. Test docstring admits this does NOT differentially
  test behavior.
- Propstore `tests/test_defeasible_conformance_tranche.py:37,43` —
  includes the fixture id
  `antoniou_ambiguous_attacker_blocks_only_in_propagating` in both
  the gunray-direct and propstore-translation tranches. The
  translation tranche branch handles `expect_per_policy` and iterates
  policies, calling
  `GunrayEvaluator().evaluate(translated, Policy(policy_name))`.
- Conformance fixture
  `datalog-conformance-suite/src/datalog_conformance/_tests/defeasible/ambiguity/antoniou_basic_ambiguity.yaml`
  — contains TWO fixtures with `expect_per_policy: {blocking, propagating}`.
  The two policies have DIFFERENT expected sections. Under blocking,
  `p` is `defeasibly` provable; under propagating, `p` is `undecided`.
  Source: Antoniou 2007 §3.5 p.10.
- Propstore other `policy=` occurrences (`propstore/world/*`, `cli/*`,
  `worldline/*`, `praf/*`) are propstore's OWN `RenderPolicy` / world
  resolution policy, NOT gunray `Policy`. False positives.

### STUCK / NOT YET OBSERVED
- Have not yet read paper notes for Garcia 04 and Simari 92 to verify
  whether PROPAGATING is actually in those papers.
- Have not yet read `notes/defeasible_conformance.md` /
  `notes/refactor_progress.md` Deviations section.
- Have not yet read `notes/what_sucks_review.md` line 93 context.
- Have not yet determined if the B2 conformance-pass tranche is
  currently passing or skipping the propagating branch. The test
  is listed in the tranche, which suggests it either currently
  passes (meaning `del policy` happens to produce the blocking
  output and the test is run with `policy_name=None`) or fails.
- Haven't read the b1-scout report's full discussion of the old
  `ambiguity.py` module to understand what was deleted.

### NEXT
1. Read Garcia 04 and Simari 92 paper notes for propagating/blocking.
2. Read `notes/defeasible_conformance.md`, `refactor_progress.md`
   Deviations, `what_sucks_review.md:93`.
3. Confirm whether the `antoniou_ambiguous_attacker_blocks_only_in_propagating`
   case currently runs for both policies and what the B1-post state
   of that test is.
4. Write `reports/b2-scout-policy.md` with verdict matrix.

### KEY FINDING SO FAR
The policy parameter is vestigial in gunray's CURRENT post-B1
code — `del policy` in defeasible.py line 51 proves it. BUT a
real conformance fixture with genuine per-policy expected outputs
exists AND is listed in the propstore translation tranche. This
means "deprecate" is contradicted by an existing per-policy
expectation in the canonical fixture set. The foreman needs to
decide: either (a) deprecate PROPAGATING AND drop the fixture,
or (b) make PROPAGATING actually do something different in the
dialectical-tree path, or (c) keep the stub and deliberately make
the fixture a known-skipped variance.
