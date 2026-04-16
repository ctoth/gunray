# B2.1 — Policy usage scout report

**Scout:** B2.1
**Date:** 2026-04-13
**Mode:** Read-only. No code edits, no commits.
**Question:** Who uses `Policy.PROPAGATING`? What does it mean? Does it
have any runtime effect today?

---

## 1. Gunray source call sites

### 1.1 Definition

`src/gunray/schema.py:33-40`:

```python
class Policy(str, Enum):
    """Named evaluation policies supported by Gunray."""

    BLOCKING = "blocking"
    PROPAGATING = "propagating"
    RATIONAL_CLOSURE = "rational_closure"
    LEXICOGRAPHIC_CLOSURE = "lexicographic_closure"
    RELEVANT_CLOSURE = "relevant_closure"
```

### 1.2 Adapter routing

`src/gunray/adapter.py:30-42`:

```python
def evaluate(self, item: Program | DefeasibleTheory, policy: Policy | None = None) -> object:
    if isinstance(item, Program):
        return self._datalog.evaluate(item)
    if isinstance(item, DefeasibleTheory):
        actual_policy = policy if policy is not None else Policy.BLOCKING
        if actual_policy in {
            Policy.RATIONAL_CLOSURE,
            Policy.LEXICOGRAPHIC_CLOSURE,
            Policy.RELEVANT_CLOSURE,
        }:
            return self._closure.evaluate(item, actual_policy)
        return self._defeasible.evaluate(item, actual_policy)
    return self._suite_bridge().evaluate(item, policy)
```

`src/gunray/adapter.py:44-61` — same shape for `evaluate_with_trace`.

The adapter recognizes three closure policies and forwards them to
`ClosureEvaluator`. For any other policy value (i.e. `BLOCKING` or
`PROPAGATING`) it forwards to `DefeasibleEvaluator.evaluate`.

### 1.3 Defeasible evaluator — **the critical finding**

`src/gunray/defeasible.py:45-52`:

```python
def evaluate_with_trace(
    self,
    theory: SchemaDefeasibleTheory,
    policy: Policy,
    trace_config: TraceConfig | None = None,
) -> tuple[DefeasibleModel, DefeasibleTrace]:
    del policy  # honored by the dialectical-tree path; unused for the strict-only shortcut
```

The `policy` parameter is **deleted on entry**. The comment claims
the dialectical-tree path honors it; it does not. The parameter is
never read again in `defeasible.py`, never forwarded into
`_evaluate_via_argument_pipeline`, and the pipeline itself
(`build_arguments`, `build_tree`, `mark`, section projection) takes
no policy parameter anywhere.

### 1.4 Dialectic — no policy signature

`src/gunray/dialectic.py` functions `build_tree` (line 240),
`mark` (line 336), `answer` (line 489) — none accept a policy
parameter. Grep for `policy` in the whole `src/gunray/` tree:

```
src\gunray\defeasible.py       (parameter; deleted on entry)
src\gunray\adapter.py          (parameter; forwarded)
src\gunray\closure.py          (used only for rational/lex/relevant)
src\gunray\conformance_adapter.py  (translation shim)
src\gunray\semantics.py        (docstring only)
```

There is NO `policy` reference inside `dialectic.py`, `arguments.py`,
`preference.py`, `disagreement.py`, or any other dialectical-tree
component.

### 1.5 Closure evaluator

`src/gunray/closure.py:40-237` — `ClosureEvaluator.evaluate` branches
on `RATIONAL_CLOSURE` / `LEXICOGRAPHIC_CLOSURE` / `RELEVANT_CLOSURE`
and raises `ValueError("Unsupported closure policy: ...")` on anything
else. Does not handle `BLOCKING` or `PROPAGATING` (by design; the
adapter never routes them here).

### 1.6 Conformance adapter

`src/gunray/conformance_adapter.py:66-141` — `_translate_policy`
converts a suite `Policy` enum value to the matching gunray `Policy`
by name (`Policy(policy.value)`). No per-policy logic; passes through.

### 1.7 README

`README.md:21`:

```python
model = GunrayEvaluator().evaluate(theory, Policy.BLOCKING)
```

Single doc example, uses BLOCKING.

---

## 2. Gunray test call sites

Every gunray test passes `Policy.BLOCKING`. **No gunray test passes
`Policy.PROPAGATING`.**

- `tests/test_trace.py:96, 147, 210, 254, 344` — five
  `evaluator.evaluate_with_trace(theory, Policy.BLOCKING)` calls.
- `tests/test_defeasible_evaluator.py:120, 145, 161, 181` — four
  `evaluator.evaluate(theory, Policy.BLOCKING)` calls.
- `scripts/show_defeasible_case.py:52, 59, 77` — debug script uses
  `Policy.BLOCKING` for gunray and for the depysible adapter.
- `tests/test_closure_faithfulness.py:33-37` — `_POLICY_PAIRS` tuple
  containing `RATIONAL_CLOSURE`, `LEXICOGRAPHIC_CLOSURE`,
  `RELEVANT_CLOSURE`. Does not include BLOCKING or PROPAGATING.

No gunray test file imports or references `Policy.PROPAGATING` at all.
No gunray test references `AmbiguityPolicy`, `attacker_basis`, or
`resolve_ambiguity_policy` — the old `ambiguity.py` module and its
tests were deleted in B1.2 and never restored.

---

## 3. Propstore call sites

### 3.1 Grounder default and forwarding

`propstore/propstore/grounding/grounder.py:74-156`:

```python
def ground(
    rule_files: Sequence[LoadedRuleFile],
    facts: tuple[GroundAtom, ...],
    registry: PredicateRegistry,
    *,
    policy: Policy = Policy.BLOCKING,
) -> GroundedRulesBundle:
    ...
    evaluator = GunrayEvaluator()
    raw_model = cast(DefeasibleModel, evaluator.evaluate(theory, policy))
```

The docstring (lines 126-134) explicitly says:

> Phase 1 theories cannot diverge between `BLOCKING` and `PROPAGATING`
> because the translator does not yet emit conflict pairs, but the
> keyword is still threaded through so callers can opt into the
> richer regimes once Phase 2 lands.

This is propstore's **only** internal call site that mentions
`PROPAGATING`. No propstore CLI, world-model, or worldline code
passes `Policy.PROPAGATING`. The other `policy=` occurrences
(`propstore/world/*.py`, `propstore/cli/compiler_cmds.py`,
`propstore/worldline/*.py`, `propstore/praf/*.py`) all refer to
propstore's own `RenderPolicy` / world-resolution policy types,
not gunray `Policy`.

### 3.2 Propstore tests — the one real PROPAGATING caller

`propstore/tests/test_grounding_grounder.py:622-680` — a single test
`test_grounder_policy_is_configurable` passes
`policy=Policy.PROPAGATING`. The test's own docstring (lines
633-643) admits:

> Phase 1 cannot construct a theory where the two policies actually
> diverge because the translator does not yet emit
> `DefeasibleTheory.conflicts` pairs ... This test therefore pins
> the narrower contract: calling with `Policy.PROPAGATING` returns
> a valid four-sectioned bundle that still preserves the canonical
> birds-fly derivation.

Smoke test only. Asserts return shape, does not assert any
differential behavior.

### 3.3 Propstore conformance tranche

`propstore/tests/test_defeasible_conformance_tranche.py:37, 43`
lists the fixture id
`antoniou_ambiguous_attacker_blocks_only_in_propagating` in both the
gunray-direct tranche and the propstore-translation tranche. The
translation tranche (lines 217-244) branches on
`case.expect_per_policy` and, when present, iterates each policy
name, calling
`GunrayEvaluator().evaluate(translated, Policy(policy_name))`. So
the propstore tranche explicitly drives gunray with
`Policy.PROPAGATING` when the fixture supplies a per-policy
expectation. This is the only differential consumer in either
repository.

---

## 4. Conformance fixture policy tags

Every YAML in
`datalog-conformance-suite/src/datalog_conformance/_tests/defeasible/`
was searched for `propagating` and for `expect_per_policy`. The
only fixture with a per-policy expectation block for blocking vs
propagating is:

`datalog-conformance-suite/src/datalog_conformance/_tests/defeasible/ambiguity/antoniou_basic_ambiguity.yaml`

Two test cases:

1. `antoniou_ambiguous_attacker_blocks_only_in_propagating`
   (lines 12-52). Theory: defeasible `p`, `a`, `~a`, `~p :- a`.
   Expectations:

   ```yaml
   expect_per_policy:
     blocking:
       defeasibly: { p: [[]] }
       undecided: { a: [[]], "~a": [[]], "~p": [[]] }
     propagating:
       undecided: { p: [[]], "~p": [[]], a: [[]], "~a": [[]] }
   ```

   Under BLOCKING, `p` is `defeasibly` provable because the
   attacker's body `a` is not defeasibly established. Under
   PROPAGATING, `p` is `undecided` because ambiguity on `a`
   propagates to kill `p`.

2. `antoniou_ambiguity_propagates_to_downstream_rule`
   (lines 53-95). Same theory plus `q :- p`.

   ```yaml
   expect_per_policy:
     blocking:
       defeasibly: { p: [[]], q: [[]] }
       undecided: { a: [[]], "~a": [[]], "~p": [[]] }
     propagating:
       undecided: { p: [[]], "~p": [[]], a: [[]], "~a": [[]], q: [[]] }
   ```

No other fixture under `datalog-conformance-suite/.../defeasible/`
has a blocking/propagating `expect_per_policy` block. Every other
fixture uses plain `expect:` and does not distinguish the two
policies.

Other fixtures mention "blocking" in prose descriptions
(`bozzato_example1_bob.yaml`, `goldszmidt_example1_nixon.yaml`,
`morris_example5_birds.yaml`) but only as narrative commentary on
the reference implementation's output. None of them bind a
per-policy expectation.

Other fixtures with `expect_per_policy` use the closure trio
(`rational_closure`, `lexicographic_closure`, `relevant_closure`)
in `morris_core_examples.yaml` — that is a separate axis and
routes into `ClosureEvaluator`, not the defeasible path.

---

## 5. Runtime reachability

**Verdict: policy has zero runtime effect on gunray's post-B1
defeasible path.**

Trace the value from entry to exit:

1. Caller passes `Policy.PROPAGATING` to
   `GunrayEvaluator.evaluate(theory, policy)`
   (`src/gunray/adapter.py:30`).
2. Adapter sees `PROPAGATING` is not in the closure set and forwards
   to `DefeasibleEvaluator.evaluate(theory, Policy.PROPAGATING)`
   (`src/gunray/adapter.py:41`).
3. `DefeasibleEvaluator.evaluate` calls its own
   `evaluate_with_trace(theory, Policy.PROPAGATING)`
   (`src/gunray/defeasible.py:42`).
4. `evaluate_with_trace` line 51 executes `del policy`. The name is
   unbound. No further reference.
5. The function dispatches to `_evaluate_strict_only_theory_with_trace`
   (strict-only shortcut) or `_evaluate_via_argument_pipeline`
   (full defeasible path). Neither takes a `policy` argument.
6. `_evaluate_via_argument_pipeline` calls `build_arguments(theory)`,
   `build_tree(arg, criterion, theory)`, `mark(tree)`, and section
   projection. None of these touch a policy.

Therefore `Policy.PROPAGATING` and `Policy.BLOCKING` produce
byte-identical outputs on every input today. The only observable
difference is the enum value stored in a trace (if the trace ever
records it — `DefeasibleTrace` does not).

Supporting evidence from `propstore/logs/test-runs/`: the
2026-04-13 190247 run (post-B1.6 equation cutover) shows the
Antoniou propagating fixtures failing with
`NotImplementedError: DefeasibleEvaluator.evaluate_with_trace:
defeasible path rewired in B1.6`. An earlier 153349 run from the
same day shows the same fixtures PASSED before the rewire. The
pre-B1.6 code had a `policy`-aware fixpoint path (the deleted
`_has_live_opposition` / `_attacker_body_available` /
`_has_blocking_peer` machinery), and those fixtures passed
because that old path routed `Policy.PROPAGATING` to a "supported"
attacker basis. Post-B1 that machinery is gone and the parameter
is vestigial.

---

## 6. Paper reading

### 6.1 Garcia & Simari 2004

`papers/Garcia_2004_DefeasibleLogicProgramming/notes.md`: every
occurrence of "blocking" refers to **blocking defeaters**
(Definition 4.2, p.20) — a *defeat-kind* concept. A blocking defeater
is an argument that counter-argues another at a disagreement point
when neither is strictly preferred. Garcia 04 §4 Def 4.7 condition 4
forbids chaining blocking defeaters on blocking defeaters
(the "block-on-block ban" B1.4 implemented in
`src/gunray/dialectic.py:296`).

**"Propagating" does not appear in Garcia 04 at all.** The word is
not in the notes. There is no blocking-vs-propagating ambiguity
regime distinction in Garcia & Simari 2004. Garcia 04 has one
semantics: the dialectical-tree marking procedure (Def 5.1 / Proc
5.1), which produces warranted / not-warranted per the tree's
marking — a three-way answer (warranted / not-warranted /
unknown). Ambiguity resolution is implicit in the proper-defeater
construction and is not a selectable policy.

### 6.2 Simari & Loui 1992

`papers/Simari_1992_MathematicalTreatmentDefeasibleReasoning/notes.md`:
no matches for "propagating", "blocking", or "ambiguity" (grep
returned zero). Simari 92 does not distinguish the two regimes
either. It predates the Nute / Antoniou ambiguity-regime literature
and provides only the generalized specificity criterion
(Lemma 2.4) that Block 2 is about to land.

### 6.3 Antoniou 2007 — the actual source

`papers/Antoniou_2007_DefeasibleReasoningSemanticWeb/notes.md`
lines 73-82 and 180-181 document the distinction precisely. The
DR-Prolog meta-program has two variants:

- **Ambiguity blocking** — c7: `overruled(R,X) :- supportive_rule(S,~X,[Ui]), defeasibly(Ui), sk_not defeated(S,~X).` An attacker overrules a rule only if the attacker's body is itself *defeasibly* proven.
- **Ambiguity propagating** — c7': `overruled(R,X) :- supportive_rule(S,~X,[Ui]), supported(Ui), sk_not defeated(S,~X).` An attacker overrules a rule if the attacker's body is *supported* (a weaker basis that propagates ambiguity downstream).

Testable property 5 (p.10): "If $p$ is ambiguous, dependent
literals also become ambiguous."

Antoniou 2007 explicitly lists other implementations by which
variant they support: Delores and DR-DEVICE are "only ambiguity
blocking" (p.29). Multi-variant support is an Antoniou distinguishing
feature.

`gunray/notes/what_sucks_review.md:90-93` (2026-04-11 plan agent
review) already states the right diagnosis: "PROPAGATING is not
in Garcia 04; need to decide its fate explicitly rather than
silently change its meaning under propstore's default
`Policy.BLOCKING`."

### 6.4 Lineage in gunray

The deleted `src/gunray/ambiguity.py` module (see b1-scout report
section 6.3) mapped `Policy.BLOCKING → attacker_basis="proved"` and
`Policy.PROPAGATING → attacker_basis="supported"`. That mapping is
a direct projection of Antoniou's c7 vs c7' distinction into
gunray's old fixpoint evaluator. It is not drawn from Garcia 04,
Simari 92, or any paper in the defeasible-logic-programming
(DeLP) lineage — it is an Antoniou/DR-Prolog import.

---

## 7. Historical notes

### 7.1 B1 scout's own flag

`reports/b1-scout.md:1597`: when enumerating
`tests/test_defeasible_core.py` tests scheduled for deletion, the
scout noted:

> 5. `test_equal_strength_opponents_are_classified_as_blocking_peers`
>    (100-138) — exercises `_has_blocking_peer` with
>    `Policy.PROPAGATING`. Coverage dropped: propagating-ambiguity
>    peer detection. **Do not preserve** — propagating semantics are
>    not part of Block 1's TrivialPreference path.

The only unit test for `Policy.PROPAGATING` in gunray was deleted
in B1.2. It was never re-landed.

### 7.2 B1.6 wire report — explicit deferral

`reports/b1-wire-evaluator-and-nests-fix.md:253-258` lists
`antoniou_ambiguous_attacker_blocks_only_in_propagating` in the
"not-yet-passing fixtures" table and says:

> Actual has `defeasibly` missing because the `BLOCKING` policy
> semantics under TrivialPreference do not match the
> ambiguity-propagation expectation. Both ambiguity policies are
> Block 2 territory.

So B1 knowingly left the Antoniou fixtures failing and flagged
"both ambiguity policies" as Block 2 work — which is precisely
what B2.1 is scouting.

### 7.3 Propstore test run logs

`propstore/logs/test-runs/20260413-190247-full-suite-equation-cutover-rerun.txt:3666-3669`:
post-B1.6 the three Antoniou conformance cases (both gunray-direct
and translation tranche) fail with the same `NotImplementedError`,
confirming they regressed when B1.6 rewired the defeasible path.
An earlier same-day run (`153349-full-suite-conflict-cleanup.txt:713-717`)
shows those cases PASSED pre-rewire.

### 7.4 No Deviations-section mention of PROPAGATING

`notes/refactor_progress.md:531-546` lists the P0.1.5 / P0.1.6 /
`nests_in_trees` deviations. None of them mention
`Policy.PROPAGATING` — the current deviation set is silent on it.
`notes/what_sucks_review.md:90-93` is the only free-form note
that flags PROPAGATING as a decision point, and it defers to
"Insert Phase 5.5 — ambiguity policy (BLOCKING/PROPAGATING) as
tree-construction strategy".

---

## 8. Verdict matrix

The scout does not pick. Here is how each foreman option scores
against the observed evidence.

### Option 1 — **Deprecate PROPAGATING**

**Supports:**

- Zero gunray internal callers pass `Policy.PROPAGATING`. All five
  test-trace sites and four defeasible-evaluator sites use
  `Policy.BLOCKING`.
- The gunray defeasible path does `del policy` on entry. The
  parameter is already functionally deprecated at runtime.
- The concept is not in Garcia 04 or Simari 92 — the two papers
  that define gunray's current pipeline. It is an Antoniou 2007
  import that lost its home when B1.2 deleted `ambiguity.py`.
- Only one propstore caller ever passes `PROPAGATING` and that
  caller is a smoke test whose own docstring says it pins no
  behavior.
- The old `_has_blocking_peer` / `attacker_basis` machinery that
  gave PROPAGATING meaning was deleted in B1.2; nothing has
  replaced it and the dialectical-tree path has no natural
  surface for a "supported" attacker basis.

**Contradicts:**

- Two conformance fixtures
  (`antoniou_ambiguous_attacker_blocks_only_in_propagating` and
  `antoniou_ambiguity_propagates_to_downstream_rule`) have
  `expect_per_policy` blocks that require differential behavior.
  The propstore tranche is wired to drive gunray with both
  `Policy.BLOCKING` and `Policy.PROPAGATING` on those fixtures.
  Deprecation means dropping the fixtures (or marking them
  `skip:`), which is a visible regression in the conformance
  corpus.
- Reference implementations (SPINdle, DR-Prolog, Delores) do
  expose the distinction — walking away from it narrows the
  corpus gunray can validate against.

**Cost estimate:** low. Remove `PROPAGATING` from the enum,
remove the smoke test from propstore, remove the two Antoniou
fixtures (or `skip:` them), update docstrings in `grounder.py`
and `notes/what_sucks_review.md`.

### Option 2 — **Map PROPAGATING to a stricter tree-construction variant**

**Supports:**

- A canonical source exists (Antoniou 2007 §3.5 c7/c7'): the
  semantics is well-defined as `attacker_basis ∈ {defeasibly,
  supported}` at the place where an attacker's body is checked.
- Two conformance fixtures pin the expected differential behavior
  and propstore already drives them. Implementing the distinction
  gives propstore measurable coverage gains.
- The foreman's phrase "closer to a grounded-semantics
  approximation than to Garcia 04's standard" is a reasonable
  framing: propagating ambiguity is strictly more conservative
  than blocking (it strictly shrinks the `defeasibly` section).
- The B1.6 wire report explicitly flagged this as Block 2
  territory.

**Contradicts:**

- The Garcia 04 tree-construction pipeline does not naturally
  expose a "supported" attacker-body check. Antoniou's c7' is a
  meta-program clause operating on the `supported` predicate —
  gunray's `build_arguments` / `build_tree` have no equivalent
  seam today. Adding it means changing the tree-construction or
  argument-filtering logic, which is new surface.
- Block 2's headline deliverable is `GeneralizedSpecificity`
  (Simari 92 Lemma 2.4). Expanding Block 2 to also deliver a
  second ambiguity regime widens scope and risks pulling the
  "conformance back to 267 passed" target out of reach.
- The only consumers are the two Antoniou fixtures and a
  propstore smoke test. Implementation cost is not proportional
  to consumer count.

**Cost estimate:** medium-high. New dialectical-tree option,
new unit tests, fixture validation, differential test against
Antoniou's reference; all concentrated in one already-full block.

### Option 3 — **Something else entirely**

**Sub-option 3a — Defer the distinction and skip the two fixtures
for Block 2 only.** Keep the enum, keep the parameter, keep
`del policy`, mark the two Antoniou fixtures `skip: "ambiguity
regime deferred to post-Block-2"`. Unblocks Block 2's 267-pass
target without losing the fixture files. Revisit in Block 3+.

- Supports: preserves corpus, minimal code churn, lets Block 2
  focus on `GeneralizedSpecificity`. The two fixtures are already
  failing post-B1.6 anyway; marking them `skip:` is a honest
  notation of current reality.
- Contradicts: leaves the "does policy do anything?" vestigial
  surface in place, which the adversary reviewer may flag. Also
  leaves `del policy` lying around as a documented falsehood.

**Sub-option 3b — Rename `BLOCKING` to `DEFAULT` and delete
`PROPAGATING`.** Addresses the confusion that Garcia 04's
"blocking" is a defeat-kind, not an ambiguity regime. The single
remaining policy becomes `Policy.DEFAULT` (or no enum at all —
just drop the parameter).

- Supports: eliminates the misleading-namespace problem that
  "BLOCKING" inherits from Antoniou's regime vocabulary while
  gunray's Garcia-04 pipeline uses "blocking" to mean defeater
  kind. Makes the vestigial nature explicit.
- Contradicts: propstore API-breaking (grounder signature
  changes), docs churn, and still requires deciding what to do
  with the two Antoniou fixtures.

**Sub-option 3c — Keep PROPAGATING as a documented stub that raises
`NotImplementedError` at the adapter boundary.** Callers who pass
`Policy.PROPAGATING` get a clear failure mode instead of silently
getting blocking semantics. Forces the decision at the call site.

- Supports: removes the "silent no-op" which is the adversary's
  worst enemy. The one propstore smoke test would need to catch
  `NotImplementedError` or skip.
- Contradicts: will actively fail the two Antoniou fixtures and
  propstore's tranche tests until Block 2+ wires a real
  implementation. Blocks 2's 267-pass target unless the fixtures
  are also skipped.

---

## 9. Hard-stop check

Scout did NOT find any call site whose semantics depend on a
BLOCKING/PROPAGATING distinction that cannot be satisfied by one
of the three options. The two Antoniou fixtures plus the propstore
smoke test are the universe of "real" PROPAGATING consumers, and
every one of them is addressable by one of the options above.
No hard-stop deviation to record.

---

## 10. One-line summary

`Policy.PROPAGATING` is a vestigial Antoniou-2007 import with zero
runtime effect in post-B1 gunray (`del policy` at `defeasible.py:51`),
one propstore smoke-test caller, and two conformance fixtures whose
per-policy expectations are currently failing — any of deprecate /
defer-and-skip / map-to-stricter are viable; foreman picks.
