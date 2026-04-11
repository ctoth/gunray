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

**NEXT:** Count fact sizes to confirm scale, then write up the four sections.
