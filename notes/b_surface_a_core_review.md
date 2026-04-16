# Surface A core-semantics review — scout notes

GOAL: Audit defeasible.py, arguments.py, dialectic.py, preference.py, answer.py, disagreement.py and write findings to `reviews/2026-04-16-full-review/surface-a-core-semantics.md`.

## 2026-04-16 — checkpoint after first read pass

### DONE
- Read all six in-scope files.
- Read prior notes: what_sucks_review.md, defeasible_conformance.md.
- Read `__init__.py`. Confirmed: `GeneralizedSpecificity`, `SuperiorityPreference`, `CompositePreference` are NOT exported from package, NOT in `__all__`. Yet `defeasible.py` imports them locally and `tests/test_superiority.py` exists.
- Need to grep README.md for which import path it uses.

### KEY FILE OBSERVATIONS (kept for posterity, will translate to report)

**defeasible.py**
- L72: `del policy` — Policy parameter discarded (B2 deprecation, documented).
- L294 `_is_strict_only_theory`: only checks defeasible/defeaters/superiority empty. Does NOT verify Π is non-contradictory. A strict-only theory with `p.` and `~p :- ... .` (strict-rule-derived) bypasses Def 3.1 cond 2.
- L298-313 `_evaluate_strict_only_theory_with_trace`: copies model.facts into both definitely AND defeasibly. Per Def 5.3 strict ⇒ defeasibly is correct, but no contradiction guard.
- L141: `if arg.conclusion in warranted: continue` — correct memoization for warrant; but skips trace info for second tree.
- L192: `defeater_touches = atom in defeater_probed or complement(atom) in defeater_probed` — both literals routed to not_defeasibly even when only one side has a defeater. Needs paper check.
- L268-284 `_supporter_rule_ids`: O(|atoms| × |arguments|), called per atom inside loop.
- L142-144: `mark(build_tree(arg, criterion, theory)) == "U"` — `build_tree` is called per argument, each call rebuilds universe internally.

**arguments.py**
- L137 `build_arguments`: 2^|defeasible_rules| naive enumeration. Documented.
- L201-220: outer loop iterates `range(0, len(rule_universe)+1)`, then `if not rule_set: continue` at L221 — wastes a no-op closure pass for empty subset.
- L232: minimality check assumes ascending size order from `combinations`. Correct but fragile.
- `_positive_closure_for_grounding` rebuilt every call. No caching of grounded theory.

**dialectic.py**
- L58 `_theory_strict_rules`: re-grounds on every call. Called from `_disagreeing_subarguments` AND `_concordant`.
- L104 `_disagreeing_subarguments`: calls `build_arguments(theory)` (full enumeration) inside per-pair check. Called by `counter_argues`, `proper_defeater`, `blocking_defeater`, `_defeat_kind`.
- L240 `build_tree`: builds `universe` then passes it down — but `_expand` ignores it and the inner helpers call `build_arguments` again.
- L266: `universe = build_arguments(theory)` — built but only used for outer `for candidate in universe` loop in `_expand`; per-candidate work explodes regardless.
- L336 `mark`: pure recursion, fine for tree but `_render_lines` (L421) re-recurses `mark` for every node → O(N²) render.
- L499 `answer`: top-level entry — calls `build_arguments` then for each warranted check goes through `_is_warranted` → `build_tree` → `_expand` → `_defeat_kind` → `_disagreeing_subarguments` → `build_arguments`. Recursive explosion.

**preference.py**
- L138-141 `_covers`: vacuous coverage (empty antecedents → True). 
  - prefers(defeasible, strict_with_empty_rules): right_ant=∅ → vacuous True; left_ant non-empty likely not covered → returns True. So defeasible >_spec strict. WRONG per paper.
  - But guarded? No — only `if left == right: return False` at L109. No empty-rules guard like SuperiorityPreference has.
- L153 `SuperiorityPreference`: explicit empty-rules guard at L232. Inconsistent with GeneralizedSpecificity.
- L243 `CompositePreference`: first-fire is asymmetric provided each child is asymmetric. Verified by inspection above. OK.
- L83 `GeneralizedSpecificity.__init__`: only caches `_strict_rules`. Re-grounds the theory anyway via `_ground_theory`.

**answer.py / disagreement.py**: small, mostly clean.
- disagreement.strict_closure: no indexing on rule heads, but small theories.

### CONFIRMED FROM PRIOR NOTES

- `what_sucks_review.md`: previously identified the trace as rule-fire centric — the refactor DID build first-class `Argument` (good!) but `DefeasibleTrace` per defeasible.py L258-265 still only carries `definitely`, `supported`, `classifications`, `proof_attempts`. NO field for the dialectical tree itself. So traces still don't expose the tree, despite the refactor's whole point.
- `defeasible_conformance.md`: 2 nests_in_trees test failures per old code. Need to check if new tree-based code resolves them — that's a verifier's job, not mine.

### __init__.py finding (verified)
- `GeneralizedSpecificity`, `SuperiorityPreference`, `CompositePreference` are NOT in __init__.py imports/exports.
- `tests/test_superiority.py` and other tests exist using these classes.
- `defeasible.py` uses local imports for these.
- README.md imports `from gunray.preference import GeneralizedSpecificity` (per prompt) — bypasses package surface.
- This is finding #4 from the prompt: real and an oversight.

### NEXT
- Verify the README import path with grep.
- Check trace.DefeasibleTrace fields for the tree.
- Spot-check Garcia 2004 paper for Def 4.7 condition wording (just enough to validate one finding).
- Write the report at reviews/2026-04-16-full-review/surface-a-core-semantics.md.

### STUCK
- None.

### BLOCKER
- None.
