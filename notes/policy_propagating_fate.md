# Policy.PROPAGATING — foreman decision

**Date:** 2026-04-13
**Context:** Block 2 kickoff. Scout report: `reports/b2-scout-policy.md`.
**Plan reference:** Block 2 step 6.2 in
`C:\Users\Q\.claude\plans\ticklish-frolicking-bengio.md` — the
foreman picks between deprecate, map-to-stricter, or
defer-and-skip.

## Finding (from scout)

1. `Policy.PROPAGATING` is **not in Garcia & Simari 2004** or
   **Simari & Loui 1992**. Scout confirmed zero matches for
   "propagating" in either paper's notes. The distinction comes
   from **Antoniou 2007 §3.5** (c7 vs c7' meta-program clauses —
   `defeasibly(U)` vs `supported(U)` in the overruled clause).
   The deleted `src/gunray/ambiguity.py` mapped
   `BLOCKING → attacker_basis="proved"` and
   `PROPAGATING → attacker_basis="supported"`, a direct
   projection of Antoniou's distinction.

2. **Zero gunray callers** pass `Policy.PROPAGATING`. Every
   gunray test, script, and internal call site uses
   `Policy.BLOCKING`.

3. **One propstore caller** passes `PROPAGATING`:
   `propstore/tests/test_grounding_grounder.py:660` — a smoke
   test whose own docstring says it pins no differential
   behavior.

4. **Two conformance fixtures** have `expect_per_policy`
   blocking-vs-propagating expectations, both in
   `defeasible/ambiguity/antoniou_basic_ambiguity.yaml`. Both
   currently FAIL post-B1.6.

5. **`defeasible.py:51`** executes `del policy` immediately on
   entry to `evaluate_with_trace`. The parameter is functionally
   dead in both the strict-only and the B1.6 defeasible path.
   `src/gunray/dialectic.py`'s `build_tree`, `mark`, and
   `answer` take no policy parameter at all.

## Decision: DEPRECATE

Remove `Policy.PROPAGATING` from `src/gunray/schema.py`.

### Rationale

The three options and why DEPRECATE wins:

- **Deprecate.** The enum value is dead code. It cites a paper
  (Antoniou 2007) that is not in this refactor's source-of-truth
  paper set. The only caller is a propstore smoke test that
  pins no behavior and changes independently in Block 3 anyway.
  The two conformance fixtures that exercise it are testing a
  regime gunray does not claim to implement under the paper-
  driven refactor. This matches Q's "rip shit out, no gentle
  movement" mandate.

- **Map to stricter variant.** Inventing a "proper-defeater-only"
  tree-construction mode to give PROPAGATING a meaning would be
  gunray adding non-paper semantics under a Block 2 banner. The
  refactor is explicitly paper-driven; adding Antoniou semantics
  that are not in our two canonical papers contradicts the
  refactor's own principles. Rejected.

- **Defer and skip.** Marking the enum value as unused but alive,
  skipping the two antoniou fixtures, and deferring the decision
  to a future Block is exactly the gentle movement the
  scorched-earth principle rejects. Rejected.

### Consequences of deprecation

1. **`src/gunray/schema.py`**: delete the
   `PROPAGATING = "propagating"` line from the `Policy` enum.
2. **`src/gunray/defeasible.py`**: the `del policy` line stays
   (the parameter is still part of the public signature for
   `evaluate_with_trace`, preserved for contract stability). The
   only change is that `Policy.BLOCKING` is now the only
   meaningful value — document this in the function docstring.
3. **Conformance suite**: the two `antoniou_basic_ambiguity`
   cases become expected failures and are classified as
   `regime-not-implemented` in the running Block 2 conformance
   delta. They join the `depysible_nests_in_trees_{tweety,tina}`
   pair as "fixtures that test regimes gunray does not claim to
   implement under the paper-driven semantics."
4. **Propstore test**: `test_grounding_grounder.py:660` will
   break at `Policy.PROPAGATING` resolution. **Fix scheduled for
   Block 3** (propstore update) — that's the one-line change to
   use `Policy.BLOCKING` or drop the policy argument entirely.
   Block 2 coder adds a forward-looking note in the dispatch
   report about this propstore breakage so Block 3 can address
   it.
5. **Plan document update**: the plan's Block 2 step 6.2
   description says "decide PROPAGATING's fate"; this file is
   the decision. The Block 2 coder can reference this file
   rather than re-deriving the decision.

### Where this decision lands in commits

The PROPAGATING deprecation lands as a small commit inside the
B2.3 dispatch (policy routing + full green), not in a dedicated
dispatch. It's a one-line enum edit plus a docstring adjustment;
bundling it with the Block 2 full-green drive keeps the
commit graph simple.

### If this decision turns out wrong

If a Block 3 propstore consumer, a future gunray caller, or a
user complaint surfaces a real need for Antoniou-style ambiguity
propagation, the fix is to re-add `Policy.PROPAGATING` and
implement a tree-construction variant that requires proper
defeaters at every expansion. The shape of that variant is
already sketched in Garcia 04 Def 4.7 cond 4's reasoning about
blocking-of-blocking — it would be the natural extension. This
decision is reversible.
