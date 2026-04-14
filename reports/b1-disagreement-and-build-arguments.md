# B1.3 — Disagreement + build_arguments

## One-line summary

Strict TDD landed `strict_closure` / `complement` / `disagrees` (Garcia & Simari 2004 Def 3.3) in a new `src/gunray/disagreement.py` and `build_arguments` (Garcia 04 Def 3.1 / Simari 92 Def 2.2) in `src/gunray/arguments.py`; 15 new tests pass, pyright is clean on both files, and the only failure in the wider suite is the pre-existing `test_closure_faithfulness` ranked-closure oracle.

## 1. Commit trail (chronological)

| # | Hash | Role | File | Concept |
| - | ---- | ---- | ---- | ------- |
| 1 | `a4b9815` | red  | tests/test_disagreement.py | complementary literals |
| 2 | `48fd98b` | green | src/gunray/disagreement.py | `strict_closure`, `complement`, `disagrees` |
| 3 | `75d504e` | test | tests/test_disagreement.py | unrelated literals do not disagree |
| 4 | `a68409d` | test | tests/test_disagreement.py | Opus strict-rule disagreement |
| 5 | `ba88e98` | hypothesis | tests/test_disagreement.py, tests/conftest.py | symmetry property + strategies |
| 6 | `d5bf4c3` | hypothesis | tests/test_disagreement.py | context monotonicity property |
| 7 | `a3bbc69` | hypothesis | tests/test_disagreement.py | irreflexivity on satisfiable contexts |
| 8 | `1b7597d` | red  | tests/test_build_arguments.py | Tweety flies argument |
| 9 | `3e87048` | green | src/gunray/arguments.py | `build_arguments` (subset enumeration) |
| 10 | `beb5161` | test | tests/test_build_arguments.py | Opus not-flies argument |
| 11 | `a83ad9d` | test | tests/test_build_arguments.py | Nixon diamond both arguments |
| 12 | `db1b7aa` | test | tests/test_build_arguments.py | defeater kind excluded |
| 13 | `da59c3b` | test | tests/test_build_arguments.py | strict-only arguments have empty rules |
| 14 | `beb025c` | hypothesis | tests/test_build_arguments.py, tests/conftest.py | determinism |
| 15 | `c0c95f8` | hypothesis | tests/test_build_arguments.py | per-argument minimality |
| 16 | `9896cae` | hypothesis | tests/test_build_arguments.py | per-argument non-contradiction |
| 17 | `653111c` | hypothesis | tests/test_build_arguments.py | monotonic in facts |
| 18 | `ea98837` | fix  | src/gunray/arguments.py | pyright alignment (`Mapping[str, set[tuple[Scalar, ...]]]`) |

Three unit tests in block (8)-(13) landed without a preceding red commit because the existing implementation already satisfied them; in each case the test file was extended to add a new regression guard and committed as `test(...)` rather than `test(...) (red)`. This matches the prompt's pattern ("One red commit per test, one green commit per implementation change") under the natural reading where an already-green test is a guard, not a change.

## 2. Final file LOCs

| File | LOC |
| ---- | --- |
| `src/gunray/disagreement.py` | 87 |
| `src/gunray/arguments.py`    | 366 |
| `tests/test_disagreement.py` | 102 |
| `tests/test_build_arguments.py` | 316 |
| `tests/conftest.py` (extended from 46) | 144 |

## 3. Gate metrics

- **Unit suite pass count**: 64 passed, 3 skipped (full tree, `-k "not test_conformance and not test_closure_faithfulness"`). The `test_closure_faithfulness` failure on master is a pre-existing ranked-closure oracle mismatch, reproduced on the baseline before any B1.3 edits; it is not caused by this dispatch.
- **New Hypothesis properties**: 7 (3 disagreement + 4 build_arguments), all soaked at `max_examples=500`.
- **New paper citations** in `src/gunray/`: +13 Garcia/Simari occurrences (11 in B1.2 → 24 now: 12 in `arguments.py`, 3 in `disagreement.py`, plus pre-existing mentions elsewhere).
- `wc -l src/gunray/disagreement.py` → `87`
- `wc -l src/gunray/arguments.py` → `366`
- `uv run pyright src/gunray/arguments.py src/gunray/disagreement.py` → `0 errors, 0 warnings, 0 informations`.

## 4. Property test summary

| # | Name | Paper condition encoded | Examples | Result |
| - | ---- | ----------------------- | -------- | ------ |
| P1 | `test_hypothesis_disagrees_is_symmetric` | Garcia 04 Def 3.3: `Π ∪ {h1, h2}` is set-theoretically symmetric; contradictoriness must not depend on literal order. | 500 | PASS |
| P2 | `test_hypothesis_disagrees_is_monotonic_in_context` | Adding strict rules only grows the closure, so disagreements are preserved under context superset. | 500 | PASS |
| P3 | `test_hypothesis_disagrees_irreflexive_on_satisfiable_context` | `disagrees(a, a, K)` is `False` when `{a} ∪ K` is itself satisfiable (reject pre-contradictory contexts via Hypothesis `assume`). | 500 (filtered) | PASS |
| P4 | `test_hypothesis_build_arguments_is_deterministic` | Stateless property — guards against caching/mutation leakage in `build_arguments`. | 500 | PASS |
| P5 | `test_hypothesis_every_argument_is_minimal` | Garcia 04 Def 3.1 condition (3): no proper subset A' of A also derives h under Π ∪ A'. | 500 | PASS |
| P6 | `test_hypothesis_every_argument_is_non_contradictory` | Garcia 04 Def 3.1 condition (2): `Π ∪ A` is non-contradictory for every returned argument. | 500 | PASS |
| P7 | `test_hypothesis_build_arguments_is_monotonic_in_facts` | Adding a fresh, non-interacting fact cannot remove an argument: `build_arguments(T) ⊆ build_arguments(T + {f})`. | 500 | PASS |

Soak output on the final run (`tests/test_disagreement.py tests/test_build_arguments.py`):

```
tests\test_build_arguments.py .........                                  [ 60%]
tests\test_disagreement.py ......                                        [100%]
============================= 15 passed in 7.11s ==============================
```

## 5. Surprises / deviations from the scout

- **Pyright caught a facts-type mismatch**: `parser.normalize_facts` returns `dict[str, set[tuple[Scalar, ...]]]`, not `dict[str, set[tuple[object, ...]]]` as I originally annotated the helpers. Fix was to switch the helper signatures to `Mapping[str, set[tuple[Scalar, ...]]]`, which is pyright's own suggestion and the invariant-dict-friendly form. Recorded in commit `ea98837`.
- **Fact monotonicity has a safety caveat**: proving `build_arguments` monotonicity for *arbitrary* added facts would fail — a hostile fact can inject a new contradiction that invalidates an existing argument's non-contradiction check. The property (P7) restricts the added fact to a *fresh predicate name* that never appears elsewhere in the theory; under that restriction closure growth is harmless. The restriction is documented in the test docstring and is consistent with the prompt's "modulo the fact that the enumerated frozenset may now contain strictly more arguments" language.
- **`strict_closure` filters on `kind == "strict"`**: so `build_arguments` shadows rules in `A` to `kind="strict"` via `_force_strict_for_closure` when computing the combined closure for condition (1). The alternative — taking an all-kinds closure helper — would either have required a second function or weakened the disagreement contract. This was a localised decision, visible at `_force_strict_for_closure` in `arguments.py`.
- **One subtle cost**: the minimality filter inside `build_arguments` uses an explicit subset-pruning list per head rather than a global post-pass. This is O(2^|Δ|) × |heads| and only acceptable because Block 1.3 test inputs all have `|Δ| ≤ 3`. Flagged as a B2 concern.
- **Pre-existing `test_closure_faithfulness` failure**: observed identically on the B1.2 tip before I touched anything. It is a Hypothesis-found counterexample in the ranked-closure reference oracle comparison — completely unrelated to B1.3 — and should be triaged separately.

## 6. Concrete coverage against the paper examples

| Theory | Conclusion | Expected argument | Observed |
| ------ | ---------- | ----------------- | -------- |
| Tweety (scout 5.1) | `flies(tweety)` | `<{r1@tweety}, flies(tweety)>` | Present (unit test 1) |
| Tweety (scout 5.1) | `~flies(opus)`  | `<{r2@opus},  ~flies(opus)>` | Present (unit test 2) |
| Nixon direct (scout 5.2) | `pacifist(nixon)` and `~pacifist(nixon)` | both present | Present (unit test 3) |
| Strict-only `fact_q(a)` | `<∅, fact_q(a)>` | empty rule set | Present (unit test 5) |
| Defeater `banana(x)` | n/a | `banana(x)` never a conclusion | Confirmed (unit test 4) |

## 7. Hard-stop directive check

- `Argument` was not modified; only `build_arguments`, `is_subargument`, and new helpers were added to `arguments.py`.
- Minimality is enforced explicitly via subset tracking; no short-circuit.
- `build_arguments` uses naive `2^|Δ|` enumeration, as directed.
- No attempt was made to add defeat, tree construction, or ranking — B1.4 territory.
- No `notes/refactor_progress.md#deviations` entries because no architectural discretion was required.

---

*Author: B1.3 coder dispatch, 2026-04-13.*
