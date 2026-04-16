# CPtrLoad Timeout Analysis
## 2026-04-11

**GOAL:** Identify root cause of timeout in `strict_only_souffle_hmmer_CPtrLoad` and propose fix.

**OBSERVATIONS SO FAR:**

1. The test case is in `datalog-conformance-suite/.../defeasible/strict_only/strict_only_recursion_souffle_example_hmmer.yaml` (3.2MB, 107K lines).
2. It's a strict-only defeasible theory, so `_is_strict_only_theory()` returns True, routing to `_evaluate_strict_only_theory()` which delegates to `SemiNaiveEvaluator.evaluate()`.
3. The program has ~50K+ fact rows across predicates like `DirectFlow`, `HeapAlloc`, `Load`, `Store`, `StackAlloc`, `Global`, `ExtReturn`, `EscapePtr`.
4. There are 24 rules — this is a pointer analysis from Souffle's HMMER benchmark.

**KEY RULES (the blowup):**
```
IsPtr(dest,o) :- DirectFlow(src,dest), IsPtr(src,o).          # join DirectFlow × IsPtr
IsPtr(dest,o) :- Load(dest, addr), IsPtr(addr, o1), Memory(o1,o).  # 3-way join
Memory(o1,o2) :- Store(src,addr), IsPtr(src,o2), IsPtr(addr, o1).  # 3-way join with IsPtr×IsPtr
IsReachable(v,o) :- Memory(o1,o), IsReachable(v,o1).          # recursive join
CPtrLoad(dest, addr) :- Load(dest, addr), IsPtr(addr, o), CFormat(o), LptrVar(dest). # 4-way join
CFormat(o) :- CPtrLoad(_,v), IsPtr(v,o).                      # feeds back into CPtrLoad
```

**ROOT CAUSE HYPOTHESIS:** The `_match_positive_body` function does a nested-loop join: for each body atom, it iterates ALL rows in the model for that predicate × ALL current bindings. With IsPtr growing large (N pointers × M objects), and Memory doing IsPtr×IsPtr, the intermediate binding lists explode combinatorially. The `DirectFlow × IsPtr` join produces |DirectFlow| × |IsPtr| candidate bindings before filtering — no indexing.

**SPECIFIC MECHANISM:** `_match_positive_body` at evaluator.py:136-155. For each atom, it does `for binding in bindings: for row in rows: _unify(...)`. With no hash index on the predicate's rows, a body atom like `IsPtr(addr, o1)` where `addr` is already bound scans ALL IsPtr rows instead of looking up by first column. This is O(|bindings| × |relation|) per atom instead of O(|bindings|) with an index.

## 2026-04-11 — Deep dive (agent session)

**Prior notes said naive fixpoint was the cause. That is OUTDATED.** Commit b0e92a4 added real semi-naive delta tracking to `_evaluate_stratum`. The code correctly:
- Initializes delta from seed facts
- For each recursive body position, overrides that position with delta and earlier positions with previous_only
- Non-recursive rules fire only on iteration 1
- Deduplicates against model in `_apply_rule`

**Stratification confirmed correct via runtime:**
- Stratum 8: {LptrVar} (5 rules, self-recursive)
- Stratum 9: {IsPtr, Memory, IsReachable} (11 rules) — the heavy stratum
- Stratum 10: {CFormat, CPtrLoad, CPtrStore} (8 rules)

**Fact sizes:** DirectFlow: 31303, Load: 11017, ExtReturn: 3404, EscapePtr: 2757, Store: 1705, Global: 1053, Function: 595, StackAlloc: 274, HeapAlloc: 45

**ACTUAL ROOT CAUSE: `_positive_atom_cost` (evaluator.py:300-329) produces bad join orders for 3+ way joins.**

The cost function uses `len(rows)` (total relation size) as primary sort key. It IGNORES that bound variables enable indexed lookups reducing effective scan to a small fraction. This causes:

1. After the delta atom binds variables, the next atom chosen is the smallest *total* relation rather than the most *selective* one.
2. For r9 `IsPtr :- Load(dest,addr), IsPtr(addr,o1), Memory(o1,o)` with Memory-delta driving:
   - After Memory(o1,o) binds {o1,o}: Load has 0 constrained terms but only 11K rows. IsPtr has 1 constrained term (o1 bound) but 50K+ rows.
   - Cost sorts Load (11017,0,0) before IsPtr (50000,-1,-1). Load wins → FULL SCAN.
   - Each delta Memory tuple scans ALL 11017 Load rows. With 1K delta: 11M iterations.
   - Correct order: IsPtr (indexed by o1, ~20 matches) → Load (indexed by addr, ~2 matches) = 40K iterations. **275× less.**

3. Same pattern hits r12 (Memory rule), r19 (CPtrLoad 4-way join), and r23/r24 (CFormat first-iteration).

**FIX:** Change `_positive_atom_cost` sort key from `(len(rows), -constrained, ...)` to `(-constrained, len(rows), ...)`. This ensures atoms with bound variables (indexed lookups) are always preferred over atoms without, regardless of total relation size. Correctness is unaffected — join order changes performance only, not results.

**Estimated impact:**
- r9 with Memory delta: 11M → 40K iterations per fixpoint step (275×)
- r19 (CPtrLoad): ~5.5M → ~2K per step (2750×)
- Total stratum 9: ~220s → ~2s (estimated)

**RISK:** Could regress ordering for some edge case (small constrained relation with high fan-out). Mitigate by running full conformance suite.

**Profiling run dispatched** (background, bee08242a) to confirm binding counts empirically. Awaiting output.

## 2026-04-13 — P0.2 dispatch STOPPED: "before" shape no longer present

**GOAL:** Apply the one-line `_positive_atom_cost` sort-key swap from the
2026-04-11 fix note.

**OBSERVED:** Current `_positive_atom_cost` in `src/gunray/evaluator.py:484-517`
returns:

```
(
    rows.average_lookup_size(tuple(lookup_columns)),
    len(rows),
    -constrained_terms,
    -bound_term_variables,
    atom.predicate,
)
```

This does NOT match the "before" shape `(len(rows), -constrained, ...)` the
note describes. A leading `rows.average_lookup_size(...)` term was added —
that key uses the indexed relation's own estimate of how many rows a lookup
on the currently-bound columns would fan out to. That is semantically stronger
than the proposed `-constrained` swap: it directly minimizes the estimated
scan rather than just preferring "has any constrained term."

**GIT EVIDENCE:** `git log --oneline -- src/gunray/evaluator.py` shows commit
`88a1638 "Choose joins by estimated lookup fanout"` — this is the commit that
superseded the sort-key by introducing fanout-based ordering. It lives between
the 2026-04-11 analysis and today.

**BLOCKER:** The dispatch's explicit hard-stop directive:

> "If the current `_positive_atom_cost` does not match the 'before' shape in
> the notes, STOP and report the discrepancy without committing."

The "before" shape is absent. Applying the described swap on top of the
current shape would REMOVE the fanout-estimate leading term, which is a
regression, not a fix.

**NO CODE CHANGES MADE. NO COMMITS.** Reporting to Q.

**FILES:**
- `src/gunray/evaluator.py:484-517` — current `_positive_atom_cost`
- `src/gunray/relation.py:63` — `average_lookup_size` implementation
- commit `88a1638` — the supersession
