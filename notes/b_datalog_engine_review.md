# Surface B Datalog Engine Review — scout progress

## 2026-04-16

**GOAL:** Audit `evaluator.py / stratify.py / relation.py / compiled.py / semantics.py` for bugs and write
report to `reviews/2026-04-16-full-review/surface-b-datalog-engine.md`.

**STATUS: REPORT WRITTEN.** File at
`reviews/2026-04-16-full-review/surface-b-datalog-engine.md`. Within ~1500 word
target.

**DONE:**
- Read all 5 in-scope source files.
- Read `notes/cptrload_timeout_analysis.md`, `notes/indexing_analysis.md`, `notes/refactor_complete.md`.
- Ran `uv run pyright` and `uv run ruff check` on the 5 files: **clean** (0 errors / All checks passed).
- Ran `uv run pytest tests/test_evaluator_review_v2.py tests/test_compiled_matcher.py -q`: **8 passed**.
- Ran `uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.conformance_adapter.GunrayConformanceEvaluator -k "nemo_negation"`: **all 28 PASS**.
- Inspected `src/gunray.tar`: stale POSIX tar of pre-refactor `gunray/` (300KB). Untracked, not in `.gitignore`. Delete candidate.
- Reviewed semi-naive driver, stratification, compiled matcher, indexing, costing, validator, _unify.

**KEY FINDINGS (in report):**

1. **B1 (high, policy):** `_validate_program` no longer checks negation
   safety (commit `3ea1a00` deleted the check). Engine now silently adopts
   Nemo-style existential reading. No user-facing doc.
2. **B2 (med, latent):** `_unify` at evaluator.py:622-628 uses `is None`
   instead of `_UNBOUND` sentinel — conflates missing key with `None` value.
3. **B3 (low):** `_variables_in_atom` at evaluator.py:668-672 is dead code
   (zero callers) — survived vulture sweep `916a5a0`.
4. **B4 (med):** `add_values` at semantics.py:38-43 silently coerces
   non-numeric mixed types to `f"{left}{right}"`. No SemanticError.
5. **B5 (med, arch):** `_match_positive_body` is a private function
   imported by `arguments.py` and `scripts/profile_case.py`. Architecture
   leak.
6. **B6 (low):** Stray `src/gunray.tar` — untracked 300 KB stale snapshot.
7. **B7 (low, scaling):** `IndexedRelation` index cache has no eviction.
8. **B8 (low):** `IndexedRelation.difference` discards indexes.
9. **B9 (low):** `_positive_atom_cost` uses `average_lookup_size`, blind
   to skewed key distributions.
10. **B10 (low, latent):** Compiled matcher's slots list is mutated in
    place; relies on dict comprehension copying values out before recursion.

**Prior finding 1 (`_positive_atom_cost` sort)**: NOT a bug today.
`88a1638` superseded it with `average_lookup_size` fanout estimate.

**Prior finding 2 (28 nemo_negation `SafetyViolationError`)**: Already fixed
by commit `3ea1a00`. The "known critical" item is closed; only policy
documentation remains.

**STUCK:** Done. No blockers.

**FILES TOUCHED (read-only inspection):**
- `src/gunray/evaluator.py`, `stratify.py`, `relation.py`, `compiled.py`, `semantics.py`
- `src/gunray/parser.py` (partial), `src/gunray/conformance_adapter.py` (partial), `src/gunray/arguments.py` (partial)
- `src/gunray/errors.py`
- `tests/conftest.py`, `tests/test_conformance.py`
- `notes/cptrload_timeout_analysis.md`, `notes/indexing_analysis.md`, `notes/refactor_complete.md`
- `.venv/Lib/site-packages/datalog_conformance/_tests/negation/nemo_negation.yaml` (fixture)

**FILES WRITTEN:**
- `reviews/2026-04-16-full-review/surface-b-datalog-engine.md` (the deliverable)
- `notes/b_datalog_engine_review.md` (this file)
