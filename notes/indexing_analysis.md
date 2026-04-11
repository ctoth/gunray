# Indexing vs Algorithmic Change Analysis
## 2026-04-11

**GOAL:** Determine whether indexed relations alone fix the hmmer timeout, or whether the naive fixpoint loop is the real problem.

**KEY FINDING:** IndexedRelation already exists and is already wired into the evaluator. It did not fix the hmmer timeout.

**EVIDENCE:**
1. `relation.py`: `IndexedRelation` provides lazy hash indexes over arbitrary column subsets with `lookup(columns, values)`.
2. `evaluator.py:182-201`: `_matching_rows()` determines bound columns per atom and calls `rows.lookup()` for hash-indexed access.
3. `evaluator.py:154-156`: `_match_positive_body` uses `_matching_rows` instead of scanning all rows.
4. Despite all this, the hmmer test remains pinned as timing out at 120s.

**ROOT CAUSE:** `_evaluate_stratum` (evaluator.py:123-141) is naive fixpoint: every iteration fires ALL rules against the ENTIRE model. No delta tracking. Class is named `SemiNaiveEvaluator` but the implementation is purely naive.

**WHY NAIVE FAILS EVEN WITH INDEXES:** Indexes reduce per-lookup cost from O(|relation|) to O(fan_out). But naive evaluation still enumerates the FULL join result for every rule every iteration. For HMMER's `Memory(o1,o2) :- Store(src,addr), IsPtr(src,o2), IsPtr(addr,o1)`, the full join result at iteration 40 with 100K IsPtr tuples is ~2M bindings. Semi-naive would process only ~5K delta bindings. The 400:1 ratio × 40 iterations × 24 rules × Python overhead = timeout.
