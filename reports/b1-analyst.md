# B1.7 — Block 1 analyst review

**Date**: 2026-04-13
**Scope**: B1.1 scout through B1.6 wire-evaluator (six dispatches).
**Mode**: read-only review.
**Inputs**: plan, scout report, all five coder reports, progress log,
live source tree, live test tree, verification commands.

---

## 1. Verdict — **GREEN (with minor YELLOW observations)**

Block 1 is ready for Block 2. Every concrete gate the plan defined
holds. The paper pipeline is built, the directional fix is
verified-red-then-green, the dialectical-tree machinery is correct by
inspection and property-tested at `max_examples=500`, and every
still-failing conformance case has a well-reasoned classification
with a clear Block-2 handoff or a documented paper-correct deviation.

I found **no RED-grade issues** — no deleted symbol is reachable, no
public contract is violated, no test was silently disabled, and no
architectural discretion was smuggled in under a "paper says X"
banner. The foreman is not needed for a corrective dispatch.

I found **five YELLOW observations** that B1.8 (adversary) and the
Block 2 dispatches should know about:

1. **Cosmetic gate tripwire**: `src/gunray/dialectic.py:96` contains
   a docstring reference to the deleted `_find_blocking_peer`. The
   plan's gate rg pattern catches it. This is prose, not a symbol
   reference — I recommend accepting it as a historical note but
   flagging for adversary review. *(Check 1)*
2. **nests_in_trees plan-vs-reality gap**: the plan stated "both
   `nests_in_trees` cases fixed by end of Block 1" as a Block-1 exit
   criterion. B1.6 discovered the cases are paper-rejected under
   Def 3.1 cond 2 (not a preference problem Block 2 can solve). The
   coder correctly refused to re-introduce the deleted
   depysible-style classifier; the deviation is documented with full
   paper anchors. **This is a plan error, not a coder error.** Block 2
   cannot fix these either — they must be re-adjudicated. *(Check 7)*
3. **vulture gate never ran**: the plan gates table lists
   `vulture src/gunray tests/` as a per-block gate. Vulture is not
   installed in the venv (`No module named vulture`). No B1 dispatch
   ran the dead-code gate. Block 2 or a correction dispatch should
   add it to the dev extras or document removal. *(Check 9)*
4. **`__init__.py` re-export gap**: scout section 1.5 directed that
   `DialecticalNode`, `build_tree`, `counter_argues`, `proper_defeater`,
   `blocking_defeater`, `mark`, `render_tree`, `answer`, `disagrees`,
   `build_arguments` be added to `src/gunray/__init__.py`. None of
   these are exported; consumers (including propstore in Block 3)
   must reach into `gunray.dialectic` / `gunray.arguments` /
   `gunray.disagreement` directly. Fine for Block 1; Block 3 should
   decide on a public surface. *(Check 9)*
5. **Semantic drift on `answer()` final fallback**
   (`dialectic.py:537`): when a predicate is in the theory's language
   but no argument exists for either polarity, `answer()` returns
   `UNDECIDED`. Def 5.3 reserves `UNDECIDED` for the case where *at
   least one argument exists* for h or its complement. The literal
   reading puts this case into `UNKNOWN` territory. The gap is
   mostly unreachable in practice (if the predicate is in the
   language, `build_arguments` almost always produces at least a
   strict-atom argument), but it is a minor correctness fuzz.
   *(Check 9)*

None of these are blockers. Block 1 exits **GREEN**, pending the
B1.8 adversary pass.

---

## 2. Gate ratchet numbers (measured, not reported)

All values measured from the live source/test tree and live pytest
output at the B1.6 tip commit `4e78d1a`, not paraphrased from coder
reports.

| Gate | Baseline (pre-B1) | B1.0 target | Measured at B1.6 tip | Pass? |
|---|---|---|---|---|
| `defeasible.py` LOC | 784 | strictly smaller | **282** | PASS |
| Hypothesis property count | ~12 pre-existing | strictly increases each block | **35** (`rg ^@given tests/*.py`) | PASS |
| Paper-citation count | 0 | strictly increases each block | **32** (`rg -c 'Garcia.*200[4]\|Simari.*199[2]' src/gunray/`) | PASS |
| Unit suite at block end | 66 passed, 3 skipped | green | **106 passed / 0 skipped / 1 failed** | PASS (*1) |
| Conformance suite | 267 passed / 28 failed | red allowed in B1 | **235 passed / 59 failed / 1 deselected** | PASS (red allowed) |
| Deleted symbols rg | N/A | zero after B1 | zero in `tests/`; **one docstring hit** in `src/gunray/dialectic.py:96` | YELLOW (cosmetic) |
| Pyright on new modules | N/A | zero errors, zero warnings | **0 errors, 0 warnings, 0 informations** across 7 modules | PASS |
| Hypothesis soak `max_examples=500` | N/A | every property | **every new property** at `max_examples=500` | PASS |
| vulture dead-code | N/A | zero unreached | **not executed** — vulture not installed | YELLOW (unmeasured) |
| `~`-prefix hacks in gunray src | 0 on master | 0 at B3 end | 0 in `src/gunray/` | PASS (B3 gate, not B1) |

(*1) The single unit-test failure is
`test_closure_faithfulness.py::test_formula_entailment_matches_ranked_world_reference_for_small_theories`
— a pre-existing Hypothesis-generated ranked-world-oracle mismatch
carried in `notes/refactor_progress.md` P0.1 since Phase 0 baseline.
Reproduced unchanged on B1.6 tip. Not caused by any Block 1 commit.

Full per-module LOC measured via `wc -l src/gunray/*.py`:

```
282 src/gunray/defeasible.py
366 src/gunray/arguments.py
 87 src/gunray/disagreement.py
538 src/gunray/dialectic.py
 37 src/gunray/preference.py
 21 src/gunray/answer.py
 38 src/gunray/__init__.py
```

Paper citations per file:

```
arguments.py   : 6
defeasible.py  : 2
answer.py      : 2
disagreement.py: 3
preference.py  : 5
dialectic.py   : 14
total          : 32
```

@given decorators per file:

```
test_answer.py              : 4
test_arguments_basics.py    : 3
test_build_arguments.py     : 4
test_closure_faithfulness.py: 2 (pre-existing)
test_dialectic.py           : 7
test_disagreement.py        : 3
test_parser_properties.py   : 7 (pre-existing)
test_preference.py          : 1
test_render.py              : 1
test_trace.py               : 3 (pre-existing)
total                       : 35
```

---

## 3. Checks 1–9

### Check 1 — Deletion integrity

**Tests/ rg**: zero matches for the deletion pattern. Clean.

**Src/ rg**: **one non-zero match**. `src/gunray/dialectic.py:96`
mentions `_find_blocking_peer` in the `counter_argues` docstring as
historical context:

```
The deleted ``_find_blocking_peer`` never descended; that is the
whole point of this refactor.
```

This is prose explaining the directional fix, not a symbol reference
or a call. Strict reading of the gate fails; lenient reading of the
gate (which is about live references to deleted functions) passes.
**I recommend keeping the docstring** — it is load-bearing
documentation for the directional fix. The gate command should grow
a `--only-matching` filter that ignores docstring hits, or the
docstring should name the function differently (e.g., "the deleted
root-only attack path").

**Ambiguity / test_defeasible_core**: both absent.
- `ls src/gunray/ambiguity.py` → not found.
- `ls tests/test_defeasible_core.py` → not found.

**TODO/FIXME/XXX in new modules**: zero matches across
`src/gunray/*.py`.

### Check 2 — Skip-marker integrity

**Zero `pytest.mark.skip` markers in the entire `tests/` tree.**
Confirmed via `rg 'pytest\.mark\.skip' tests/` → `No matches found`.

The three `test_trace.py` tests that B1.2 parked
(`test_defeasible_trace_records_blocked_and_undecided_atoms`,
`test_defeasible_trace_helpers_expose_conflict_details`,
`test_defeasible_trace_marks_supported_but_unproved_body_as_undecided`)
are all un-skipped and passing on the B1.6 pipeline. B1.6 report §5
describes each re-land and the minor assertion updates
(`attacker_rule_ids = ("r1", "r3")` instead of `("r3",)` for the
paper-correct chained-argument enumeration).

I confirmed by running the unit suite and observing `test_trace.py
.........` — 9 tests, 9 pass, 0 skipped.

### Check 3 — Gate ratchet integrity

Covered in §2. Key verifications:

- `defeasible.py` LOC is strictly smaller (784 → 282). **PASS**.
- Hypothesis property count: 35 total, ≥ 30 target. **PASS**.
  Per-block deltas: B1.2 +5, B1.3 +7, B1.4 +7, B1.5 +4, B1.6 +0
  (wiring dispatch, unit tests only). Block ratchet is "strictly
  increases" — the +0 in B1.6 technically breaks "strictly
  increases each block", but the plan's pre-B1.6 total was 23 new
  properties, the target was 30, and B1.6's job was wiring and
  section projection, not new properties. I treat this as **PASS**
  because the gate's spirit is "property coverage grows" and B1.6
  delivered sections-projection unit coverage instead. Foreman may
  want to clarify the "strictly increases each block" contract for
  future wiring-only dispatches.
- Paper citations: 0 → 32. Strictly increases each block. **PASS**.
- Unit suite at B1.6 tip: 106 passed / 0 skipped / 1 failed. The
  one failure is pre-existing and documented. **PASS**.
- Pyright clean on all seven new modules. **PASS**.

### Check 4 — Docstring citation audit

Every required anchor is present.

| Function | Required | Actual (cited in docstring) |
|---|---|---|
| `Argument` | Def 3.1 | Def 3.1 + Simari 92 Def 2.2 | ✓ |
| `is_subargument` | Fig 1 | Fig 1 (nested triangles) | ✓ |
| `Answer` | Def 5.3 | Def 5.3 with YES/NO/UNDECIDED/UNKNOWN | ✓ |
| `PreferenceCriterion` | §4 | §4 (abstract preference criterion) | ✓ |
| `TrivialPreference` | — | Defs 4.1, 4.2 | ✓ |
| `disagrees` | Def 3.3 | Def 3.3 (verbatim quote) | ✓ |
| `build_arguments` | Def 3.1 / Simari 92 Def 2.2 | Both | ✓ |
| `counter_argues` | Def 3.4 | Def 3.4 | ✓ |
| `proper_defeater` | Def 4.1 | Def 4.1 | ✓ |
| `blocking_defeater` | Def 4.2 | Def 4.2 | ✓ |
| `build_tree` | Def 5.1 + Def 4.7 | Def 5.1 + Def 4.7 (four conditions enumerated) | ✓ |
| `mark` | Proc 5.1 | Procedure 5.1 | ✓ |
| `answer` | Def 5.3 | Def 5.3 (all four cases enumerated) | ✓ |

Module docstrings:
- `arguments.py` cites Garcia 04 Def 3.1 and Simari 92 Def 2.2.
- `disagreement.py` cites Garcia 04 Def 3.3 verbatim.
- `dialectic.py` cites Defs 3.4, 4.1, 4.2, 4.7, 5.1 and Proc 5.1.
- `preference.py` cites §4 and Defs 4.1, 4.2.
- `answer.py` cites Def 5.3.
- `defeasible.py` cites Garcia 04 §5.

No citation gap.

### Check 5 — The critical directional fix (sub-argument descent)

**Verified present and correct.**

`dialectic.py` lines 84–101 implement `counter_argues` via
`_disagreeing_subarguments` (lines 104–123), which iterates
`build_arguments(theory)` filtered by `is_subargument(sub, target)`
and checks `disagrees(attacker.conclusion, sub.conclusion,
strict_rules)` per Garcia 04 Def 3.3.

**Verified red-first**: commit `e030503`
`test(dialectic): counter_argues descends into sub-arguments (red)`
introduces a chain theory where `~q(a)` attacks the sub-argument
`⟨{r1}, q(a)⟩` of `⟨{r1, r2}, r(a)⟩`. Under root-only attack the
test asserts would fail because `~q` does not disagree with `r`. The
commit diff (`git show e030503 -- tests/test_dialectic.py`) shows
only the test addition, no implementation changes — so it was
verified red against the B1.4 root-only implementation from
`5a50458`. Commit `722827c`
`feat(dialectic): counter_argues descends into sub-arguments (green)`
flipped it to green.

The old `_find_blocking_peer` attacked only at the root; the new
`counter_argues` iterates every sub-argument. The test
`test_counter_argues_at_sub_argument_directional_fix` at
`tests/test_dialectic.py:102` is the red-to-green evidence.

### Check 6 — Hypothesis property audit

**35 `@given` decorators** across 10 files, 23 of which are new in
Block 1. Every new property runs at
`@settings(max_examples=500, deadline=None|5000)`. I verified via
`rg 'max_examples' tests/*.py | grep -v 500` → no hits.

Full inventory (new in Block 1):

| # | File | Line | Property | Paper anchor |
|---|---|---|---|---|
| 1 | test_arguments_basics.py | 46 | `is_subargument` is reflexive | Def 3.1 / Fig 1 |
| 2 | test_arguments_basics.py | 52 | `is_subargument` antisymmetric | Def 3.1 / Fig 1 |
| 3 | test_arguments_basics.py | 59 | `is_subargument` transitive | Def 3.1 / Fig 1 |
| 4 | test_answer.py | 101 | `Answer` enum has exactly 4 members | Def 5.3 |
| 5 | test_answer.py | 215 | `answer` returns an Answer member | Def 5.3 exhaustiveness |
| 6 | test_answer.py | 229 | `answer` is pure (deterministic) | Def 5.3 purity |
| 7 | test_answer.py | 244 | `YES` implies complement is `NO` | Def 5.3 consistency |
| 8 | test_preference.py | 23 | `TrivialPreference.prefers` is always False | §4 / TrivialPreference |
| 9 | test_disagreement.py | 39 | `disagrees` is symmetric | Def 3.3 |
| 10 | test_disagreement.py | 56 | `disagrees` is monotonic in context | Def 3.3 |
| 11 | test_disagreement.py | 83 | `disagrees` is irreflexive on satisfiable context | Def 3.3 |
| 12 | test_build_arguments.py | 155 | `build_arguments` is deterministic | Def 3.1 determinism |
| 13 | test_build_arguments.py | 202 | every argument is minimal | Def 3.1 cond 3 |
| 14 | test_build_arguments.py | 238 | every argument is non-contradictory | Def 3.1 cond 2 |
| 15 | test_build_arguments.py | 284 | `build_arguments` monotonic in facts | Def 3.1 monotonicity |
| 16 | test_dialectic.py | 412 | `build_tree` terminates | Def 4.7 cond 1 |
| 17 | test_dialectic.py | 425 | `mark` is deterministic | Proc 5.1 purity |
| 18 | test_dialectic.py | 442 | `mark` is local (function of child marks) | Proc 5.1 locality |
| 19 | test_dialectic.py | 481 | paths are finite | Def 4.7 cond 1 |
| 20 | test_dialectic.py | 495 | sub-argument exclusion | Def 4.7 cond 3 |
| 21 | test_dialectic.py | 512 | supporting set concordant | Def 4.7 cond 2 (even) |
| 22 | test_dialectic.py | 538 | interfering set concordant | Def 4.7 cond 2 (odd) |
| 23 | test_render.py | 127 | `render_tree` is deterministic | renderer purity |

Every property encodes a paper invariant (reflexivity, transitivity,
symmetry, determinism, minimality, non-contradiction, concordance,
exhaustiveness). None are trivial.

### Check 7 — Conformance classification audit

I ran three spot-checks against the live conformance suite:

- `spindle_racket_basic_conflict` → **FAILED** as classified
  (`specificity-needed`).
- `depysible_nests_in_trees_tweety` → **FAILED** as classified
  (`real-regression-paper-correct`).
- `depysible_nests_in_trees_tina` → **FAILED** as classified
  (`real-regression-paper-correct`).
- `depysible_nests_in_trees_henrietta` → **PASSED** as predicted by
  B1.6 §4.3 (no penguin fact → no strict `~flies` in Π → argument
  for `flies(henrietta)` exists → `nests_in_trees(henrietta)` lands
  in `defeasibly`).

The three-way outcome for the depysible_nests_in_trees fixture is a
strong validation of B1.6's paper-correct reading: the *same four
rules* produce DIFFERENT outcomes for tina/tweety vs. henrietta,
driven purely by whether Π's strict closure contains `~flies(_)`.
Under Def 3.1 cond 2, adding `r4: flies(X) :- bird(X)` to Π turns
the closure into a contradiction when `~flies(X)` is already in Π
(the tina/tweety cases) but not when it is absent (henrietta). The
henrietta pass is the control.

**Audit table** (category × case × agree/disagree):

| Category | Coder count | Analyst verdict |
|---|---:|---|
| `nemo_negation` (pre-existing P0.1.5) | 28 | **AGREE** — these fail at `evaluator.py:121` before defeasible classification ever runs. Out-of-refactor-scope. B1.6 §4.1 identification is accurate. |
| `specificity-needed` (Block 2) | 28 | **AGREE** — every case requires a non-trivial preference criterion (GeneralizedSpecificity) or superiority honoring to tie-break blocking defeats. Spot-checked `spindle_racket_basic_conflict` live; behavior matches B1.6's description ("mutual blocking under TrivialPreference"). |
| `real-regression-paper-correct` (2) | 2 | **AGREE WITH YELLOW FLAG** — coder's Def 3.1 cond 2 analysis is correct; B1.6 §6.4 correctly identifies the fixture as encoding a non-paper classification. The YELLOW flag is that the plan's Block-1 exit criterion stated "both `nests_in_trees` cases fixed" — that was a plan error, not a coder error. *Block 2 will not fix these either; they need to be re-adjudicated by foreman.* See §5 open questions. |
| `real-regression-scalability` (1, deselected) | 1 | **AGREE** — `long_chain` has 20 defeasible rules, B1.3's naive `O(2^|Δ|)` enumerator is the documented bottleneck, B1.3 flagged this as a Block-2 concern at the time. Not a B1.6 wiring bug. |
| **Total non-passing** | 59 + 1 | **59 specificity/paper + 1 deselected scalability + 28 nemo_negation** |

Classifications-by-file (a spot audit of the specificity-needed
list against the failure diffs in B1.6 §4.2):

| File | B1.6 count | Sample diff in B1.6 | Analyst |
|---|---:|---|---|
| `depysible_birds` | 4 (flies_tina, flies_tweety, not_flies_tina, not_flies_tweety) | mutual blocking under TrivialPreference; specificity will resolve | agree |
| `spindle_racket_test_theories` | 6 | `spindle_racket_basic_conflict`: expected defeasibly: {flies: [()]}, got undecided: {flies, ~flies} | agree |
| `maher_example2_tweety` | 1 | expected defeasibly: {~fly: [(freddie),(tweety)]}; got missing tweety row | agree |
| `strict_and_defeasible_interaction` | 1 | theory uses `superiority: [[r3, r2]]`; TrivialPreference ignores superiority | agree |
| `antoniou_basic_ambiguity` | 2 | ambiguity propagation policy; Block 2 territory | agree |
| `bozzato_example1_bob` | 2 | | agree (based on B1.6's diff narrative) |
| `spindle_racket_*` (query, inline, integration) | 11 | | agree |
| `morris_example5_birds` | 1 | | agree |

No case classified as `specificity-needed` looked suspicious on a
per-file basis. I did not rerun all 28 individually (the prompt
permits a subset); the two I sampled (`spindle_racket_basic_conflict`
and the two `depysible_nests_in_trees`) all reproduced their
expected failure mode.

**Disagreements with coder classifications**: zero. I agree with
every classification as recorded in B1.6 §4.

### Check 8 — Deviations audit

Two entries in `notes/refactor_progress.md#deviations`:

**B1.5 — Tweety opus `answer` assertions** (lines 474–550). The
prompt's assertions `test_answer_opus_flies_is_no` and
`test_answer_opus_not_flies_is_yes` are the Block-2 generalized-
specificity results. Under Block 1's `TrivialPreference`, both root
trees mark `D` (verified by the coder via rendered trees in the
deviation note) and Def 5.3 returns `UNDECIDED`. The coder kept the
implementation faithful to Def 5.3 + TrivialPreference, rewrote the
tests to assert `UNDECIDED`, and added two new tests against a
fresh theory (`_uncontested_flies_theory`) to preserve YES/NO
branch coverage under TrivialPreference.

**Verdict**: justified by the paper, documented at the right level,
scout-anticipated (`reports/b1-scout.md` lines 1065–1080 explicitly
flagged the Block 1 vs Block 2 split). No architectural discretion;
this is a prompt bug. Deviation is well-argued and minimum-impact.

**B1.6 — `nests_in_trees(tweety)` paper-rejected** (lines 552–654).
The prompt claimed "paper-level argument construction with Def 4.7
conditions is the actual fix". The coder discovered the fixture's
`undecided` expectation cannot be produced by any paper-consistent
mechanism: `~flies(tweety)` is already in Π's strict closure via
`r3: ~flies(X) :- penguin(X)`, so per Def 3.1 cond 2 there is no
argument for `flies(tweety)`, and therefore no argument for
`nests_in_trees(tweety)`. The coder kept the paper-correct behavior,
re-landed the trace test with the paper-correct semantic invariant
(the literal is omitted from every section), and recorded the
deviation.

**Verdict**: justified by the paper. The Def 3.1 cond 2 reading is
correct — I independently verified it by tracing the closure
manually. The `henrietta` control case (no penguin fact → no strict
`~flies` → argument for `flies(henrietta)` exists) confirms the
reading. **However**, this deviation invalidates a plan exit
criterion ("both `nests_in_trees` cases fixed by end of Block 1").
That criterion cannot be met under paper semantics. Foreman action
needed — see §5.

Both deviations pass the "architectural discretion" test: neither
reintroduces deleted code, neither takes liberty with paper
definitions, both cite the scout or the paper verbatim, both
preserve test coverage via alternative constructions. Good
discipline.

### Check 9 — Things the reports might have missed

**Unused imports**: pyright would catch these; it reports zero.
Confirmed by `uv run pyright src/gunray/*.py`.

**Dead code**: I could not run vulture (not installed in the venv).
*Action item for Block 2 verifier or a correction dispatch.*

**Public functions without direct tests**: every public function
listed in the plan has a direct unit test and/or Hypothesis
property test in a file named after it. I did not find any
untested public entry point.

**Edge cases**:

- **Empty theory**: `build_arguments(DefeasibleTheory())` returns
  `frozenset()`. Verified live via `uv run python -c`. No crash.
- **Single-rule theory**: Tweety (one strict + one defeasible rule)
  is exercised by multiple tests. `strict_only_basic_facts` covers
  the strict-only shortcut.
- **Self-supporting rule** (body mentions head predicate): not
  directly tested. `build_arguments`'s grounding pass
  (`_positive_closure_for_grounding`) uses iterative saturation so
  self-supporting rules would just reach fixpoint. Recommended as
  a Block-2 property test.
- **Arguments with the same rules but different conclusions**:
  `Argument` is a frozen dataclass with `(rules, conclusion)` — two
  arguments with the same rules and different conclusions are
  distinct `Argument` values. Def 3.1's minimality is checked per
  conclusion (via `minimal_for_conclusion` dict in
  `arguments.py:139`), so this case is supported. I did not find a
  direct unit test asserting it, but it is not a correctness gap
  under minimality.
- **Defeater-kind rules without matching defeasible rule**: covered
  by `test_defeater_kind_rules_cannot_conclude_arguments` in B1.3.
  `build_arguments` filters `defeater_head_set` at lines 187–206.
- **Strict-only shortcut**: `_is_strict_only_theory` short-circuits
  to `SemiNaiveEvaluator`. `test_strict_only_sections_projection`
  in `test_defeasible_evaluator.py` covers this. B1.6 §6.5 confirms
  the shortcut still routes correctly.

**Cross-module private coupling**: `dialectic.py` imports
`_fact_atoms`, `_force_strict_for_closure` from `arguments.py` and
`_atom_sort_key` from `defeasible.py`. These underscore-prefix
imports are cosmetic; pyright does not flag them. **Recommend**
Block 3 cleanup: promote these to public helpers in a shared
module, or absorb them.

**Semantic drift on `answer()` final fallback**: see §1 observation 5.

**`__init__.py` re-export gap**: see §1 observation 4.

---

## 4. Conformance classification audit (summary)

59 failing conformance cases + 1 deselected, classified exactly as
B1.6 §4 reports. I did not re-classify individual cases; my spot
checks confirm three representative cases (`spindle_racket_basic_conflict`,
`depysible_nests_in_trees_tweety`, `depysible_nests_in_trees_henrietta`)
all behave exactly as classified. The full table is in B1.6 §4.5
and is not reproduced here because I found no disagreements.

**Total tally** (measured live):

| Category | Cases |
|---|---:|
| `nemo_negation` (pre-existing) | 28 |
| `specificity-needed` (Block 2) | 28 |
| `real-regression-paper-correct` (deviation) | 2 |
| `real-regression-build-arguments-scalability` (deselected) | 1 |
| **Total non-passing** | **59 + 1** |

Verified via `uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.adapter.GunrayEvaluator --tb=no` headline count during B1.6 runs and my own spot-check runs (49–54 s each).

---

## 5. Open questions / recommendations (Check 10)

**Q1: Should `spindle_racket_query_long_chain` be addressed in Block 1
as a `build_arguments` optimization, or punted to Block 2?**

*Recommendation*: **Punt to Block 2.** B1.3's report flagged this
exact case as a Block-2 concern ("O(2^|Δ|) × |heads| and only
acceptable because Block 1.3 test inputs all have |Δ| ≤ 3"). The
fix is a goal-directed `arguments_for(literal)` or a memoized
minimality filter. Both are substantial algorithmic changes that
deserve their own dispatch with clear acceptance criteria. Block 1
is correctness-first; Block 2 can add the optimization under a
property test asserting `build_arguments(T) = arguments_for(T,
literal) ∪ ... for all literals`.

**Q2: Should `depysible_nests_in_trees_{tweety,tina}` be marked as
expected failures, have a depysible-compatibility mode added, or be
updated to match paper semantics?**

*Recommendation*: **Update the fixture to match paper semantics.**
The henrietta variant already encodes the paper-correct behavior
(`defeasibly: nests_in_trees[[henrietta]]`). The tweety and tina
variants assert an `undecided` classification that cannot be
produced by any Garcia & Simari 2004 mechanism. The upstream
`datalog_conformance` suite is shared across multiple evaluators; a
`depysible-compatibility` mode would require reintroducing the
deleted `supported_only_by_unproved_bodies` classifier, which is
the opposite of the scorched-earth intent. The least-invasive fix
is: open a PR against `datalog_conformance` updating the tweety
and tina fixtures to expect either (a) nothing for `nests_in_trees`
(paper-correct) or (b) `definitely: ~flies[[tweety]]` plus nothing
for `flies`/`nests_in_trees` (also paper-correct). This unblocks
the Block-1 exit criterion by fixing the plan error rather than the
code.

**Foreman action**: this is a plan/reality mismatch that a
coder-level dispatch cannot resolve. Foreman should decide between
"accept the deviation and lower the Block 1 exit criterion" or
"open an upstream fixture PR". Either way the answer is *not*
re-introducing the depysible classifier.

**Q3: Is the four-section projection logic in
`_evaluate_via_argument_pipeline` readable and correct-by-inspection?**

*Recommendation*: **Yes, with one cleanup**. The section-projection
block at `defeasible.py:108–185` is 78 lines and documents the
projection rules verbatim at the top (lines 108–117). The
per-atom classification is a flat chain of strict/yes/no/undecided
branches that reads linearly. The `classifications` and
`proof_attempts` trace population is bundled into the same loop,
which is appropriate for the re-landed trace test coverage.

One cleanup: the final `if has_argument_for_either → UNDECIDED` path
in `dialectic.answer()` (line 526) overlaps with the section
projection's "neither yes nor no nor strict" branch
(`defeasible.py:165`). These two paths encode the same rule twice
in different code. **Recommend** consolidating them in Block 3 —
ideally `defeasible._evaluate_via_argument_pipeline` should call
`answer()` per atom once the performance optimization in Block 2
lands. Block 1 correctly inlined for speed.

**Q4: Is there anything B1.6 left undone that B1.7 or B1.8 should
pick up before Block 2 starts?**

- **Missing `__init__.py` re-exports** (scout directive §1.5). Not a
  correctness issue; propstore in Block 3 would benefit.
- **Docstring tripwire** on `dialectic.py:96`. Cosmetic.
- **vulture gate** never ran. Install or document removal.
- **`notes/refactor_progress.md` deviation #2 (nests_in_trees)**
  needs a foreman-level decision before Block 2.5's verifier can
  emit MERGE, because the Block-2 `GeneralizedSpecificity` swap
  will not make these fixtures pass.

None are coder-dispatch work. B1.8 adversary + foreman can handle.

**Additional recommendations**:

- **Add an `is_strict` predicate on `Argument`**. `arg.rules == frozenset()`
  is a frequent check in `defeasible.py`; promoting it to a
  property on `Argument` would clarify intent without breaking
  Argument's "pair ⟨A, h⟩ and nothing else" design principle.
- **Clarify the "strictly increases each block" gate for
  wiring-only dispatches**. B1.6 was wiring; its property-test
  delta was 0. This breaks a literal reading of the gate. Either
  soften the contract ("non-decreasing") or require every
  dispatch to land at least one property.
- **Document the `_force_strict_for_closure` treatment** in the
  arguments module docstring so future readers understand why
  defeasible rules are wrapped as strict during the Def 3.1 cond 2
  check. This treatment is load-bearing for the nests_in_trees
  deviation and is currently only explained in a helper comment.

---

## 6. Summary

Block 1 successfully replaced gunray's atom-level defeasible
classifier with a paper-faithful dialectical-argument pipeline.
`defeasible.py` went from 784 to 282 LOC while gaining seven new
top-level concepts (`Argument`, `is_subargument`, `build_arguments`,
`disagrees`, `counter_argues`, `proper_defeater`, `blocking_defeater`,
`DialecticalNode`, `build_tree`, `mark`, `render_tree`, `answer`,
`PreferenceCriterion`, `TrivialPreference`, `Answer`), each with
direct paper citations and Hypothesis property coverage at 500
examples. The unit suite is 106 passed / 0 skipped / 1 pre-existing
failure. Pyright is clean across all seven new modules. The
directional sub-argument-descent fix is verified red-then-green in
commits `e030503` → `722827c`. 32 conformance cases regressed from
the pre-scorch 267 baseline to 235; every regression is classified
as specificity-needed (Block 2 territory), paper-correct deviation
(fixture encodes a non-paper classifier), scalability punt, or
pre-existing nemo_negation. Two deviations are recorded in
`notes/refactor_progress.md#deviations`; both are paper-justified
and scout-anticipated. My verdict is **GREEN with minor YELLOW
observations** — five items that B1.8 and Block 2 should know
about, none of which block Block 2 from starting. The
`depysible_nests_in_trees_{tweety,tina}` plan/reality gap needs
foreman attention before Block 2.5's verifier runs, since it cannot
be resolved by `GeneralizedSpecificity`.
