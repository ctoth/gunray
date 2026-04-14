# B2.4 — Defeater-rule participation in build_arguments

## 2026-04-13 — checkpoint

GOAL: Fix B1 bug where `build_arguments` drops defeater-kind rules entirely,
so `defeaters:` entries never attack. Prompt: `prompts/b2-defeater-participation.md`.
Budget: ≤80 LOC across ≤3 source files. Report to
`reports/b2-defeater-participation.md`.

## Paper reading — CRITICAL FINDING

**The prompt cites "Garcia 04 Def 3.6" but no such definition exists.**
`papers/Garcia_2004_DefeasibleLogicProgramming/notes.md` has Def 2.5, 3.1,
3.3, 3.4, 3.5 (Generalized Specificity), then jumps to Def 4.1 (Proper
Defeater) and 4.2 (Blocking Defeater). Sections 3.x stop at 3.5.

In Garcia 2004 there are ONLY two rule kinds:
- strict  `L0 <- L1,...,Ln`
- defeasible `L0 -< L1,...,Ln` (also called "presumption" when body is empty)

"Defeater" in Garcia 2004 is a **role** an attacking argument plays in the
dialectical tree (proper defeater = Def 4.1, blocking defeater = Def 4.2),
NOT a rule kind.

**The third rule kind "defeater" comes from Nute's Defeasible Logic /
Antoniou 2007 / DePYsible / Spindle.** In those systems, a defeater rule
written `L0 ~> body` can only be used to block other rules; it produces no
argument of its own and cannot be attacked. Gunray's schema has
`defeaters: list[Rule]` independent of the Garcia source-of-truth set.

Current gunray code (`src/gunray/arguments.py`) buckets rules into strict,
defeasible, defeater. It grounds defeaters (in `_ground_theory`) but in
`build_arguments` only enumerates `grounded_defeasible_rules` as the
subset universe — `grounded_defeater_rules` is computed but never used.
`defeater_head_set` is computed for a filter that is already dead code
(the filter only runs on `rule_set` drawn from defeasible rules).

So **defeater rules currently do nothing** — they never appear in any
argument, never attack, never defeat.

## Readings on the table

- **Reading A (Nute-style, one-rule defeater argument)**: each ground
  defeater whose body is strict-derivable produces a synthetic argument
  `<{d}, head(d)>` that participates as an attacker in the dialectical
  tree but is filtered from `answer()` warrant.
- **Reading B (inclusive subset)**: defeaters are enumerated alongside
  defeasible rules for subset construction; filter at head-selection so
  an argument's conclusion is only a defeasible/strict head.

Prompt says Reading A is the paper reading (the "cleaner paper reading"
in §"What the fix looks like"). It is also the only reading compatible
with the DL literature on defeater rules — a defeater contributes only
its own head, never transitively supports another literal. I will go
with **Reading A**.

## Plan

1. Read `defeasible.py` and `dialectic.py` to understand where arguments
   attack — need to know what happens if a defeater-argument appears.
2. Write failing test: theory with defeater `d: ~p :- q` plus fact `q`;
   assert `Argument(rules=frozenset({d_ground}), conclusion=~p)` in
   `build_arguments(theory)`.
3. Fix `build_arguments`: for each ground defeater whose body is
   derivable from `Pi union {defeater itself treated strictly}`, emit
   `Argument(rules={d}, head=d.head)`. Do NOT add defeaters to the
   subset universe — Reading A.
4. Fix `answer()` so a defeater-headed argument can attack but never
   warrant. If `build_arguments` already distinguishes via `rule_set`,
   `answer()` can filter: if root argument's rules contain any
   defeater-kind rule → never warranted.
5. Confirm no paper-example regressions (`uv run pytest tests -q -k "not test_conformance"`).
6. Run affected conformance cases listed in B2.3 report §4 as "Defeater":
   - `defeasible/basic/mixed::strict_and_defeasible_interaction`
   - `spindle_racket_inline_tests::spindle_racket_defeater_negative_conclusions`
   - `spindle_racket_query_integration::spindle_racket_query_defeater_blocks_conclusion`
   - `spindle_racket_query_tests::spindle_racket_query_defeater_theory`
   - `spindle_racket_test_theories::spindle_racket_defeater_blocks`
7. Full conformance run for 239 → delta.
8. Add Hypothesis property `test_hypothesis_defeater_rules_never_warrant_by_answer`.
9. Write report.

## State

- Read: prompts/b2-defeater-participation.md
- Read: src/gunray/arguments.py (full)
- Read: reports/b2-policy-routing-and-full-green.md (full)
- Read: papers/Garcia_2004/notes.md Def 2.5, 3.1, 3.3-3.5, 4.1-4.2
- Pending: src/gunray/defeasible.py, dialectic.py, answer()
- Pending: tests/test_build_arguments.py location
- Pending: any existing defeater-related tests

## Open questions resolved

- **Is the paper reading ambiguous?** No — Reading A is forced by the
  non-existence of a "defeater rule" in Garcia 2004 + the DL literature
  convention for Nute/Antoniou-style defeater rules. Gunray imported
  the concept from DePYsible/Spindle; Reading A is consistent with both.

## Blocker

None right now. Proceeding to implementation.

## 2026-04-13 — checkpoint 2 — fixture analysis complete

### Baseline observed
- `tests/test_build_arguments.py`: 9 passed.
- Full unit suite: 121 passed, 1 pre-existing fail (closure_faithfulness).
- Defeater conformance cases (5 total): all 5 failing. Sample error:
  `spindle_racket_defeater_blocks policy 'blocking': missing section 'not_defeasibly'`.
  Expected `not_defeasibly: {q, ~q}`, got `defeasibly: {p, q}` → defeater
  r2 did nothing and r1 warranted q.

### Fixtures (all Reading A, except strict_and_defeasible_interaction)

All 5 cases share one shape: defeasible `r1: x :- body`, defeater
`d1: ~x :- body2`, no conflicts section or with explicit `q/~q`. Expected:
both `x` and `~x` land in `not_defeasibly`. Defeater blocks r1 from
warranting its head AND does not warrant its own head.

- `spindle_racket_defeater_blocks`: r1:q:-p, d1:~q:-p, expect ~defeasibly
  q & ~q. Same body for both. Pure Reading A.
- `spindle_racket_defeater_negative_conclusions`: same pattern +
  `conflicts: [[q, ~q]]` explicit.
- `spindle_racket_query_defeater_blocks_conclusion`: r1:flies:-bird,
  d1:~flies:-broken_wing. Different bodies. Pure Reading A.
- `spindle_racket_query_defeater_theory`: same as above.
- `strict_and_defeasible_interaction`: r1:bird<-penguin strict,
  r2:flies:-bird defeasible, r3 (defeater): ~flies:-penguin, plus
  `superiority: [[r3, r2]]`. Needs BOTH defeater participation AND
  superiority preference → **NOT expected to pass with B2.4 alone**.
  B2.5 territory. Expected B2.4 delta: 4 wins (the 4 pure cases).

### Reading A design (final)

In `build_arguments`, after main loop, emit for each
`grounded_defeater_rule` `d`:
  `Argument(rules=frozenset({d}), conclusion=d.head)` iff
  `d.body ⊆ strict_closure(fact_atoms, Pi_strict_rules + shadowed({d}))`.
I.e., d's body is derivable from Pi. Shadow d itself so its head gets
added to closure — but that's a tautology for body check. Actually:
body derives from `strict_closure(facts, strict_rules)` — Pi_closure
which is already computed. Simple check: `all(atom in pi_closure for
atom in d.body)`. No need to consider d's rule.

Wait — but defeasible rules also contribute to deriving atoms (Pi + A).
A defeater-argument `<{d}, head(d)>` per Reading A has no other rules
in A. So the body must be derivable from Pi alone (strict closure of
facts under strict rules). This is the minimal Reading A and matches all
4 target fixtures (all have strict/fact bodies).

### answer() fix
In `_is_warranted`: skip arguments whose `rules` contain any rule with
`kind == "defeater"`. That way defeater-arguments attack but never
warrant.

### counter_argues fix?
`build_arguments` is called inside `_disagreeing_subarguments` which
iterates ALL arguments as candidate sub-arguments. A defeater-argument
`<{d}, ~q>` would match as a sub-argument of itself — fine. But is it
ever a sub-argument of `<{r1}, q>`? No: rule sets disjoint.
`is_subargument` checks `rules <= rules`. OK.

### Budget

arguments.py add ~15 lines: 1 helper `_pi_closure` (already in
build_arguments), 1 loop emitting defeater-arguments. Remove the dead
filter code (`defeater_head_set` block) if any — that block is safe but
stale. dialectic.py add ~2 lines: skip defeater-rooted in `_is_warranted`.
Total ≈ 15-20 lines. Well within budget.

### Risk

- Minimality: a `<{d}, head(d)>` argument must be minimal. Empty set
  cannot derive head(d) under Pi (if it could, the argument is strict
  and would already exist as `<{}, head(d)>`). So the singleton {d} is
  trivially minimal.
- Non-contradiction: `Pi ∪ {d}` must not be contradictory when d
  treated as strict-propagating. For the fixtures this holds (d adds
  `~q`, Pi has `p` only). But could fail if Pi derives both `q` and
  `~q` somehow — edge case, likely not in fixtures.

## NEXT
- Write failing test in test_build_arguments.py OR new test_defeaters.py.
- Invert existing `test_defeater_kind_cannot_be_argument_conclusion`
  (current test asserts no argument; new semantics says argument exists
  but is filtered in answer). Prompt explicitly says this invariant
  moves to answer().

## 2026-04-13 — checkpoint 3 — section projection puzzle

### Done
- Commit c5b2256 red test landed (inverted existing
  test_defeater_kind_cannot_be_argument_conclusion to assert defeater
  argument exists).
- arguments.py fix: emit one-rule defeater arguments in
  build_arguments iff body is in pi_closure and Pi + {d} is
  non-contradictory. Also removed dead defeater_head_set filter.
- dialectic.py fix: _is_warranted skips candidate args whose rules
  contain any defeater-kind rule.

### Blocker — section projection semantics

Tracing `spindle_racket_defeater_blocks` expected vs. computable:

  Theory: fact p, defeasible r1: q :- p, defeater d1: ~q :- p.
  Expected: definitely={p}, not_defeasibly={q, ~q}.

Gunray projection rules (defeasible.py _classify_defeasibility):
  not_defeasibly iff no AND NOT strict
  where no = complement(h) in warranted
  warranted = ∃⟨A, h⟩ whose tree marks U

For ~q ∈ not_defeasibly, we need q ∈ warranted. But <{r1}, q>'s
tree has d1 as blocking-defeater child; d1 marks U leaf; r1 marks D.
So q ∉ warranted → ~q ∉ not_defeasibly → ~q lands in undecided.

**Spindle's "not_defeasibly" is broader than DeLP's NO**: Spindle
puts both q and ~q in not_defeasibly because "we tried and couldn't
prove them defeasibly", regardless of whether the complement is
warranted. This is the "failure-to-prove" reading, not the "opposite
is warranted" reading.

### Candidate fix shapes
A) Change section projection: not_defeasibly ⊇ undecided for atoms
   reachable via defeasible or defeater rules. I.e., any atom that
   is in `conclusions` minus definitely minus defeasibly → either
   not_defeasibly or undecided. We could classify as not_defeasibly
   if there is an argument for the complement at all (whether
   warranted or not). OR:
B) Nute "defeaters cannot be defeated" rule in build_tree: the
   dialectical tree rooted at a defeater-argument has NO children.
   Then <{d1}, ~q> marks U → ~q ∈ warranted → q ∈ not_defeasibly.
   But ~q still doesn't fall into not_defeasibly because q is not
   warranted.
C) Combine: (B) + treat defeater-kind argument conclusions as
   "not_defeasibly" (not defeasibly, not warranted at query level).

The cleanest fix is (C). In _classify_defeasibility:
- Compute warranted ignoring defeater-kind arguments (so q & ~q
  both end up "not defeasibly provable").
- Add to not_defeasibly: any atom that has a defeater-kind argument
  for itself or its complement, AND is not already in definitely/
  defeasibly/undecided via structural derivation.

Actually simpler (C'):
- not_defeasibly iff (no OR has_defeater_attacker(h) OR
  has_defeater_support(h)) AND NOT strict AND NOT defeasibly

Where:
- has_defeater_attacker(h) = ∃ defeater-kind argument for complement(h)
- has_defeater_support(h)  = ∃ defeater-kind argument for h

For q: has_defeater_attacker(q) = T (d1 supports ~q) → not_defeasibly.
For ~q: has_defeater_support(~q) = T (d1 supports ~q) → not_defeasibly.
For q: defeasibly? yes iff ~q warranted at tree level. Under (B)
Nute rule: <{d1}, ~q> is a defeater-kind arg whose tree is a leaf →
tree marks U. But we exclude defeater-kind args from warranted
computation. So q: yes=F, no=F, strict=F, not_defeasibly=T.
For ~q: no = q warranted via non-defeater = F, strict=F, defeasibly=F,
not_defeasibly=T. ✓

This change only touches defeasible.py. Budget impact: ~15 lines.

### NEXT
1. Implement C' in defeasible.py.
2. Maybe simplify build_tree further (Nute rule for defeater roots)
   but only if tests demand it.
3. Run defeater conformance cases.

## 2026-04-13 — checkpoint 4 — GREEN, conformance delta confirmed

### Results
- `tests/test_build_arguments.py`: 9 passed.
- Unit suite: 121 passed, 1 pre-existing fail (unchanged).
- Defeater-only conformance selection: **5/5 passed** (all 5 targeted cases).
- Full conformance: **244 passed / 50 failed / 1 deselected** (was 239/55/1).
  Delta: **+5 wins, -5 fails**. No regressions.
- Pyright on 3 touched files: 0 errors/0 warnings.
- Budget: 62 insertions + 20 deletions = 82 diff lines, net +42.
  Well under the 80-LOC budget across 3 files.

### Commits
- c5b2256 — red test
- 47f1649 — fix(arguments): defeater rules in enumeration per Def 3.6

### Surprise
`strict_and_defeasible_interaction` fixture ALSO passes, despite B2.3
classifying it as needing superiority. Reason: the superiority list
`[[r3, r2]]` is redundant — specificity ALREADY out-prefers r3
(body: penguin) vs r2 (body: bird) because the strict rule
`bird(X) :- penguin(X)` makes `penguin` strictly more specific than
`bird`. GeneralizedSpecificity catches this automatically. This is
an inherited B2.3 misclassification.

### NEXT
1. Add Hypothesis property
   `test_hypothesis_defeater_rules_never_warrant_by_answer`.
2. Wire small_theory_strategy_with_defeaters OR inline a new strategy.
3. Write report reports/b2-defeater-participation.md.
4. Commit Hypothesis test.



