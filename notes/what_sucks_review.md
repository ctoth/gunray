# What sucks / what would make this sing — 2026-04-13

**GOAL:** Q asked for unsolicited honest critique of the gunray code (vs. papers) —
what would make it really sing. Not CLI (Q regrets mentioning). Forming opinions,
not reporting facts.

**OBSERVATIONS SO FAR:**

1. **Known bug from prior notes:** `defeasible.py` undecided classification does
   not propagate upstream through dependency chains. `nests_in_trees(tweety)` case:
   `_has_blocking_peer` only checks direct conflicts on the atom, not whether a
   prerequisite (e.g. `flies(tweety)`) is itself undecided. Two test failures, one
   root cause. (From `defeasible_conformance.md`.)

2. **The README itself admits a huge gap from the papers:** defeasible evaluator is a
   "strict-body specificity heuristic" not Simari-Loui 1992 Def 2.6/Lemma 2.4 activation-
   model specificity. Defeat is "direct live-attacker blocking at the grounded-rule
   level" not dialectical S/I-argument levels (Simari 1992 Def 4.3-4.5). Closure is
   zero-arity propositional only and rejects defeaters/superiority/conflicts.

3. **The papers we already own offer concrete upgrades:**
   - **Simari 1992:** full argument structures `<T, h>` with minimality, activation-
     model specificity, unique stable set via dialectical levels.
   - **Garcia & Simari 2004 (DeLP):** dialectical *trees* with U/D marking, four-valued
     answers (YES/NO/UNDECIDED/UNKNOWN), proper-vs-blocking defeater distinction,
     acceptable-line conditions (concordance, sub-argument exclusion, block-on-block
     ban). Gunray currently collapses DeLP's answer space into four sections derived
     after the fact rather than by dialectical construction.

4. **Trace API is rule-fire centric, not argument-centric.** `DefeasibleTrace` holds
   flat lists of `ProofAttemptTrace` and `ClassificationTrace` keyed by atom. There
   is no notion of an argument `<T, h>` as a first-class object, no dialectical tree,
   no U/D marking, no way to render "here is the tree of why I concluded this" — which
   is precisely the killer feature of argumentation over plain Datalog.

5. **`_can_prove` fixpoint is O(candidates × rules × fixpoint iterations).** Recomputes
   `opposing_atoms`, `attackers`, and specificity closures per iteration. Specificity
   cache helps on `_strict_body_closure` but the attacker-search is not indexed.

6. **Module sizes:** defeasible 784, evaluator 732, closure 699, parser 415 — closure
   is suspiciously large given it's explicitly "narrow zero-arity propositional only."

7. **Evaluator bug from cptrload notes (2026-04-11):** `_positive_atom_cost` sorts by
   total relation size before constraint count — produces bad join orders for 3+ way
   joins. Fix is one-line: swap the sort key. Not yet applied as of this session.

**THE BIG SHAPE:** The project has the *data* to become a real DeLP — good papers,
working Datalog core, working blocking semantics — but the defeasible evaluator is
currently a classifier-over-rule-fires rather than an argument constructor. Users
can't ask "show me the argument tree for X" because arguments don't exist as objects.

**BLOCKER:** None. Forming the pitch for Q now.

**NEXT:** Skim closure.py briefly to see if it's actually 699 lines of zero-arity
propositional code (suspicious) and then deliver opinion to Q.

## 2026-04-13 — Plan phase

**DONE:**
- Delivered opinion ("what sucks" list). Q approved the argument-as-first-class
  direction and asked for a beautiful paper-driven plan including propstore update.
  Constraints: TDD, commit frequently, paper-driven, beautiful.
- Entered plan mode. Plan file: `C:\Users\Q\.claude\plans\ticklish-frolicking-bengio.md`.
- Two Explore agents in parallel produced (a) consumer contract report
  (propstore + tests + scripts) and (b) paper-to-code mapping.
- One Plan agent argued against initial 10-phase decomposition and won several
  points.

**KEY FINDINGS from explorations:**
- Propstore consumes: `GunrayEvaluator.evaluate`, `model.sections[four keys]`,
  `DefeasibleTheory(strict_rules, defeasible_rules, defeaters, superiority,
  conflicts)`, `Rule(id, head:str, body:list[str])`, `parse_atom_text`,
  `Constant`/`Variable`. Four section keys are contract. `aspic_bridge` has a
  `~`-strip hack in `_split_section_predicate` that should be killed.
- `tests/test_defeasible_core.py` imports private helpers
  (`_is_more_specific`, `_supporter_survives`, `_has_blocking_peer`,
  `_expand_candidate_atoms`). Not a real contract — accident of TDD history.
  Plan agent says quarantine these tests in Phase 1, start fresh.
- Nothing first-class about arguments today. Specificity is strict-body subset
  heuristic. No tree, no marking, no Def 4.7 conditions, no sub-argument descent.
- Disagreement is predicate-pair set + `~` prefix, not Garcia Def 3.3 semantic
  (K ∪ {L1,L2} ⊬ ⊥). Closure module already has strict closure — reusable.

**PLAN AGENT WINS (adopted):**
1. **Swap Phases 3 and 5** — specificity is a strategy object plugged into an
   already-working tree. Trivial preference first; Simari 2.4 last. Isolates
   risk.
2. **Insert Phase 1.5** — Def 3.3 disagreement via `closure.py` before argument
   construction. Wrong attackers propagate to every later phase.
3. **Insert Phase 5.5** — ambiguity policy (BLOCKING/PROPAGATING) as tree-
   construction strategy. PROPAGATING is not in Garcia 04; need to decide its
   fate explicitly rather than silently change its meaning under propstore's
   default `Policy.BLOCKING`.
4. **Split Phase 5 along the Def 4.7 seam**, not build/mark. Acceptable-line
   conditions (concordance, sub-arg exclusion, block-on-block ban) are where
   the `nests_in_trees` bug actually lives.
5. **`Answer` enum and `PreferenceCriterion` protocol go in Phase 1** — north
   stars, not payoffs.
6. **Rewrite `test_defeasible_core.py` at Phase 1** (quarantine old + start
   fresh); don't preserve private-helper tests.
7. **Fold cleanup into Phase 7** — atomic cutover. Delete old fixpoint in same
   commit that flips `DefeasibleEvaluator.evaluate` to tree path. Drop Phase 10.
8. **Promote `render_tree` to Phase 5's debugger**, not a post-facto cherry.
9. **New `arguments.py` + `dialectic.py` sibling modules**, not code in
   `defeasible.py`. Thin seam, boring switch.
10. **Cross-check harness** runs old and new in tests only, not in production.
    Assert `new_path.sections == old_path.sections` across conformance suite
    for phases 2-6.

**REVISED PHASE COUNT:** 8 phases (0 baseline + 1 foundations + 1.5 disagreement
+ 2 arguments + 3 defeat + 4 tree+acceptable-lines + 5 policy + 6 cutover +
7 propstore). Renumber to 0-7 in final plan.

**BLOCKER:** None. Ready to draft plan file.

**NEXT:** Write plan to `ticklish-frolicking-bengio.md`, ExitPlanMode.

