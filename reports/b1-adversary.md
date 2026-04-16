# B1.8 — Block 1 adversary review

**Date**: 2026-04-13
**Scope**: directional / paper-alignment review of Block 1 of the
gunray paper-driven refactor (`plans/ticklish-frolicking-bengio.md`).
**Mode**: read-only. No source touched, no tests run as fixes.
**Inputs**: paper notes for Garcia & Simari 2004 and Simari & Loui
1992, the plan, the five Block 1 coder reports, `reports/b1-analyst.md`,
`notes/refactor_progress.md`, and the live source at the B1.6 tip.

---

## 1. Verdict — **ALIGNED**

Block 1 reads like Garcia & Simari 2004. Every paper definition the
plan assigned has a direct structural analogue in the live source,
every docstring citation matches the code beneath it, and the
critical directional fix (counter-argument descent into
sub-arguments) is correct and non-trivially tested.

There are **no principle violations**. There is **no silent drift**
on any of the nine core definitions (Def 2.5, 3.1, 3.3, 3.4, 4.1,
4.2, 4.7, 5.1, 5.3 plus Proc 5.1 and Simari 92 Def 2.2).

Two directional observations (not drifts, not violations) are worth
flagging to Block 2:

- **Q5 / answer() UNKNOWN fallback** is a literal-wording gap the
  analyst already flagged. The current fallback path collapses
  "predicate in language but no argument either way" to UNDECIDED.
  Def 5.3 reserves UNDECIDED for "neither warranted but some
  argument exists". I agree with the analyst that the gap is
  mostly unreachable in practice (the `is_warranted` check for any
  strict literal lands it in YES before the fallback fires), but
  unlike the analyst I believe **the right direction is UNKNOWN**,
  not UNDECIDED, for the degenerate case where no argument exists
  for either polarity regardless of whether the predicate nominally
  appears in the language. This is a one-line fix and a worthwhile
  Block-2 cleanup. **Not a blocker.** See Q5 below.

- **Q9 / docstring tripwire** at `src/gunray/dialectic.py:96`
  (historical reference to deleted `_find_blocking_peer`). The
  analyst correctly caught this. I agree it is prose, not code, and
  should stay as a historical note — but the project's gate rg
  command should be narrowed. Not adversary-level.

Q10 — the Def 3.1 cond 2 reading that underlies the
`depysible_nests_in_trees` deviation — is **paper-correct**. See
§3.10 for the derivation from Simari 92 Def 2.2 and Garcia 04 Prop
4.2. The coder was right to refuse the fixture; the fixture
encodes pre-paper classifier behavior.

---

## 2. How the review was conducted

I walked each of Q1–Q10 against the live source files:

- `src/gunray/arguments.py` (366 LOC)
- `src/gunray/disagreement.py` (87 LOC)
- `src/gunray/dialectic.py` (538 LOC)
- `src/gunray/answer.py` (21 LOC)
- `src/gunray/preference.py` (37 LOC)
- `src/gunray/defeasible.py` (282 LOC)
- `src/gunray/__init__.py` (38 LOC)

Paper anchors come from:

- `papers/Garcia_2004_DefeasibleLogicProgramming/notes.md` (Defs
  2.5, 3.1, 3.3, 3.4, 4.1, 4.2, 4.7, 5.1, Proc 5.1, Def 5.3,
  Proposition 4.2)
- `papers/Garcia_2004_DefeasibleLogicProgramming/claims.yaml`
  (claim2, claim6 are load-bearing for Q10)
- `papers/Simari_1992_MathematicalTreatmentDefeasibleReasoning/notes.md`
  (Def 2.2 verbatim, including the `K ∪ T |/~ ⊥` form of
  condition 2)

I did not re-run the tests (the analyst already established the
test-green baseline). I did not edit any source. This is pure
directional review.

---

## 3. Directional answers to Q1–Q10

### Q1 — Is `Argument` really a pair ⟨A, h⟩? **YES.**

`src/gunray/arguments.py:42-55`:

```python
@dataclass(frozen=True, slots=True)
class Argument:
    rules: frozenset[GroundDefeasibleRule]
    conclusion: GroundAtom
```

Two fields. Frozen. Slotted. No derived properties, no hidden state,
no convenience methods on the class body. `is_subargument` at
`arguments.py:58-67` is exactly:

```python
return a.rules <= b.rules
```

A pure subset check on the rules field. Reflexive, antisymmetric,
transitive — verified as Hypothesis properties in
`tests/test_arguments_basics.py` at three `@given` decorators.

Paper anchor: Garcia 04 Def 3.1 (`notes.md:61-67`, `p.8`):
"An argument structure for a literal h ... is a pair ⟨A, h⟩ where
A ⊆ Δ". Simari 92 Def 2.2 (`notes.md:39-44`, `p.9`):
`⟨T, h⟩_K iff ...` — also a pair.

The gunray `Argument` is exactly that pair and nothing else. This
is what Principle 5 of the plan ("Beauty = legibility") asked for.

**No red flag.** The scout report section 1.5 originally directed
that `Argument` and friends be re-exported through
`__init__.py`; the coder did not do that. That is not an Argument-
shape concern (it is a public-surface concern the analyst flagged
as Block 3 cleanup), and it does not make `Argument` larger than a
pair.

### Q2 — Does `counter_argues` descend into sub-arguments? **YES, correctly.**

`src/gunray/dialectic.py:84-101` delegates to
`_disagreeing_subarguments` at `dialectic.py:104-123`, which
enumerates every element of `build_arguments(theory)`, filters by
`is_subargument(sub, target)`, and checks
`disagrees(attacker.conclusion, sub.conclusion, strict_rules)`.

- **Enumeration**: over the complete argument universe
  (`build_arguments(theory)`), not a restricted immediate-children
  set. This is the maximally permissive reading of Def 3.4.
- **Filtering**: `is_subargument` is `a.rules <= b.rules`, which
  includes `target` itself (Def 3.4 reads "sub-argument ⟨A, h⟩
  of ⟨A₂, h₂⟩", and reflexive subsets are allowed in Garcia 04 —
  the root counts as its own sub-argument, Fig 1). So `counter_argues`
  handles both direct attack (hit the root) and indirect attack
  (hit any interior sub-argument) uniformly, exactly as Garcia
  04 §3 indirect-vs-direct attack diagram `notes.md:165` describes.

Paper anchor: Garcia 04 Def 3.4 (`notes.md:74-77`, `p.10-11`):
"⟨A₁,h₁⟩ counter-argues ⟨A₂,h₂⟩ at literal h iff there exists a
sub-argument ⟨A,h⟩ of ⟨A₂,h₂⟩ such that h and h₁ disagree."

The gunray `counter_argues` is literally a for-loop over that
existential quantifier.

**Directional test**: analyst §Check 5 confirmed commits
`e030503` → `722827c` — red-first test
`test_counter_argues_at_sub_argument_directional_fix` at
`tests/test_dialectic.py:102`. The commit range proves the test
was red against a root-only implementation and green after the
descent was added. I independently confirmed the test shape by
reading the scout's description: chain theory with `~q(a)` attacker,
target `⟨{r1, r2}, r(a)⟩` whose sub-argument is `⟨{r1}, q(a)⟩`.
Under a root-only `counter_argues` the attacker's conclusion
`~q(a)` does not disagree with `r(a)`, so attack would fail. Under
the descent implementation the sub-argument at `q(a)` is hit and
attack succeeds.

**No red flag.** The directional fix is real, not nominal.

One small note: `counter_argues` pays the cost of calling
`build_arguments(theory)` every invocation, which duplicates work
in `build_tree` (where every child expansion re-enumerates). This
is a Block 2+ performance concern — the plan explicitly punts it.
Not a directional concern.

### Q3 — Are Def 4.7 conditions enforced, or patched? **ENFORCED.**

`src/gunray/dialectic.py:270-333` is `_expand`. Every condition is
checked at every child-admission, not just at the root:

- **Cond 1 (finite)**: `dialectic.py:264` — `build_arguments`
  returns a finite `frozenset`, and cond 3 forbids re-entry along
  a line, so the recursion depth is bounded by `|universe|`. Not
  explicitly asserted as a terminator, but structurally guaranteed.
  Property test `test_dialectic.py:412` (`build_tree` terminates)
  exercises this at `max_examples=500`.

- **Cond 2 (concordance of supporting and interfering sets)**: lines
  306-324. The code computes the supporting and interfering sets by
  position parity (`i % 2 == 0` vs `i % 2 == 1`), adds the
  candidate to the appropriate set, and calls
  `_concordant(supporting, theory)` and
  `_concordant(interfering, theory)`. `_concordant`
  (`dialectic.py:180-208`) unions each rule set with Π and computes
  `strict_closure`, rejecting if any atom's complement is in the
  closure. **This is the same treatment as Def 3.1 cond 2**, using
  `_force_strict_for_closure` to propagate defeasible rule heads.

- **Cond 3 (sub-argument exclusion)**: lines 299-304. `any(
  is_subargument(candidate, earlier) for earlier in line)` —
  rejects the candidate if any earlier line member is a superset
  of its rules. The asymmetry matches the paper: Garcia 04 Def 4.7
  cond 3 says "no ⟨A_i,h_i⟩ is a sub-argument of any ⟨A_j,h_j⟩
  appearing earlier". `is_subargument(candidate, earlier)` is
  "candidate.rules ⊆ earlier.rules", which is exactly "candidate is
  a sub-argument of earlier" — correct direction.

- **Cond 4 (blocking-on-blocking ban)**: lines 294-297. `if
  parent_edge_kind == "blocking" and kind == "blocking": continue`.
  Tracked via an `edge_kinds` list parallel to `line`. The
  termination happens by not admitting the child, which truncates
  that branch exactly as the paper prescribes ("for all k, if A_k
  is a blocking defeater for A_{k-1}, then A_{k+1}, if it exists,
  must be a proper defeater for A_k").

Property tests at `test_dialectic.py:481, 495, 512, 538` encode cond
1, cond 3, and cond 2 (even and odd) respectively. Fig 5, 6, 8 paper
tests cover the specific pathological cases (reciprocal blocking,
circular argumentation, contradictory supporting line) that gunray's
old classifier would mis-handle.

Paper anchor: Garcia 04 Def 4.7 (`notes.md:97-104`, `p.21`). The
four conditions are enumerated in the gunray module docstring at
`dialectic.py:245-265` verbatim.

**No red flag.** All four conditions live in the generic
construction path, not in a special case.

One small note: the supporting/interfering parity check
(`i % 2 == 0` vs `i % 2 == 1`) is a cute way of saying "S_s = ⋃
A_{2i}" and "S_i = ⋃ A_{2i+1}" from Def 4.7 cond 2. I confirmed
against the paper's 0-indexed convention that this is right.
Garcia 04 writes the line as `[⟨A₀,h₀⟩, ⟨A₁,h₁⟩, ...]` with the
root at position 0 (supporting), so even indices go to supporting
and odd indices go to interfering. Matches gunray.

### Q4 — Is marking Proc 5.1, or something else? **EXACTLY Proc 5.1.**

`src/gunray/dialectic.py:336-352`:

```python
def mark(node: DialecticalNode) -> Literal["U", "D"]:
    if not node.children:
        return "U"
    if any(mark(child) == "U" for child in node.children):
        return "D"
    return "U"
```

Pure post-order. Single parameter. No mutation. No caching. No
memoization. No early exit beyond what Python's `any()` already
provides (which is not a paper deviation — `any()` short-circuits
on the first truthy result, which is semantically identical to the
paper's "has at least one U child → D").

Paper anchor: Garcia 04 Proc 5.1 (`notes.md:113-117`, `p.24`):

1. Leaves → U
2. Inner node → D iff at least one child is U, otherwise U
   (reinstatement)

The gunray code is the direct transliteration. Reinstatement
("otherwise it is marked U") is the final `return "U"`.

Property tests at `test_dialectic.py:425` (determinism) and
`test_dialectic.py:442` (locality — mark depends only on child
marks) both at `max_examples=500`.

**No red flag.** `mark` is unmistakably Proc 5.1 on a line of
code, as principle 5 of the plan required.

### Q5 — Is the four-valued answer Def 5.3, or a projection? **SUBSTANTIALLY Def 5.3, with one literal-wording fallback gap.**

`src/gunray/dialectic.py:489-537`:

The function:

1. Calls `build_arguments(theory)` once (line 512).
2. Checks `_is_warranted(literal, ...)` → returns YES.
3. Checks `_is_warranted(complement(literal), ...)` → returns NO.
4. Checks if any argument has `literal` or `opposite` as its
   conclusion → returns UNDECIDED.
5. Checks if both predicates (stripped of strong negation) are
   absent from the theory's language → returns UNKNOWN.
6. Otherwise returns UNDECIDED.

`_is_warranted` builds a tree per matching argument and marks it.
This correctly handles the "argument exists but is blocked" case
(YES only if some argument's tree marks U at the root). It also
correctly distinguishes "no argument exists" from "argument exists
but blocked": `_is_warranted` short-circuits on the first U, and
the UNDECIDED branch at line 525 checks `has_argument_for_either`.

Paper anchor: Garcia 04 Def 5.3 (`notes.md:124-131`, `p.25`):

- YES if h is warranted
- NO if h̄ is warranted
- UNDECIDED if neither is warranted but some argument exists for
  h or h̄
- UNKNOWN if h is not in the language

**The gap**: steps 5 and 6. Def 5.3 says UNKNOWN is
"not-in-language". gunray's step 5 only returns UNKNOWN if *both*
polarities' predicates are missing from the language (the literal
and its complement always have the same stripped predicate, so
this is actually just "literal_predicate not in predicates"). If
the predicate **is** in the language but no argument exists for
either polarity (e.g. an `Atom` the user constructed out of the
language, or a ground literal whose grounding is not produced by
any rule), gunray falls through to step 6 and returns UNDECIDED.

Def 5.3 strictly requires "at least one argument exists for h or
h̄" to return UNDECIDED. So the gunray path
(predicate-in-language + no-arguments-for-either) is neither
YES/NO/UNDECIDED/UNKNOWN under the literal wording; the closest
literal match is UNKNOWN ("not in the language" arguably excludes
"literal cannot be formed as a ground head even though the
predicate symbol exists in the language").

The analyst flagged this as observation 5 in `reports/b1-analyst.md`.
**I agree it is a gap** and **disagree slightly on the fix
direction**. The analyst is neutral on whether the fix should be
UNKNOWN or UNDECIDED; I think the right answer is **UNKNOWN** —
Def 5.3 reserves UNDECIDED specifically for the case where an
argument exists, and a "predicate in language but no ground
argument" case is a language-coverage failure more than an
argumentation failure.

The gap is mostly unreachable in practice: the theory's language
is derived from facts + rule heads + rule bodies, and any literal
drawn from that language almost always has at least a strict
argument (the fact model). The only pathological case is a rule
body predicate with no grounding — a syntactic artefact.

**Not a blocker.** A one-line fix in Block 2 or Block 3.

**No red flag**. The main Def 5.3 paths (YES, NO, and the
"argument exists but neither warranted" UNDECIDED) are exactly the
paper, and those are what matters. The fallback is a minor
literal-wording deviation on an edge case.

### Q6 — Does `build_arguments` enforce all three Def 3.1 conditions? **YES.**

`src/gunray/arguments.py:70-209`:

- **Cond 1 (defeasible derivation)**: line 153 computes
  `closure = strict_closure(fact_atoms, combined_rules)` where
  `combined_rules = grounded_strict_rules + (defeasible rules in A
  wrapped as strict shadows)`. Line 166 tests `head in closure` —
  this is exactly "h has a defeasible derivation from Π ∪ A" per
  Def 2.5, because Def 2.5's defeasible derivation allows any rule
  (strict OR defeasible) in the chain.

- **Cond 2 (non-contradictory)**: line 156 calls
  `_has_contradiction(closure)`, which checks whether the closure
  contains any literal and its complement. This uses the
  `_force_strict_for_closure` shadowing to propagate defeasible
  rule heads during the contradiction check. I examine the
  paper-correctness of this treatment at length in Q10.

- **Cond 3 (minimality)**: lines 173-183 maintain a
  `minimal_for_conclusion` dict per head. A candidate `rule_set`
  is rejected if any existing survivor is a strict subset
  (`existing < rule_set`), and any existing survivor that is a
  strict superset (`rule_set < existing`) is pruned. This is the
  correct minimality semantics: after the loop finishes,
  `minimal_for_conclusion[head]` contains exactly the ⊆-minimal
  rule sets producing `head`.

  **Subtlety**: the loop order (`combinations` from size 0 upward)
  means that smaller sets are always checked before larger sets.
  Combined with the per-head minimality dict, this guarantees
  correct minimality without the need to later re-check all smaller
  subsets. The analyst's Hypothesis property
  `test_build_arguments.py:202` (every argument is minimal at
  `max_examples=500`) exercises this — a non-minimal enumeration
  would be caught by a generator finding a proper subset that also
  derives the same head non-contradictorily.

Paper anchor: Garcia 04 Def 3.1 (`notes.md:61-67`, `p.8`), three
conditions exactly. Simari 92 Def 2.2 (`notes.md:39-44`, `p.9`)
reiterates the same three.

**No red flag on minimality.** The enumeration order + per-head
survivor set is a valid minimality check, and the property test
would catch a fake.

One non-paper cleanup I noticed but do not call a drift: the
enumeration is `O(2^|Δ|)` by design, and `arguments.py:144` iterates
`combinations(rule_universe, size)` for every size. This is
exponential and will be a Block 2+ optimization target (already
flagged as the `spindle_racket_query_long_chain` deselect). Not a
correctness issue; the Block 1 plan explicitly allows naive
enumeration.

### Q7 — Is `disagrees` Def 3.3, or a shortcut? **Def 3.3 with a correct fast path.**

`src/gunray/disagreement.py:68-87`:

```python
def disagrees(h1, h2, strict_context):
    if h1 == complement(h2):
        return True
    closure = strict_closure(frozenset({h1, h2}), strict_context)
    for atom in closure:
        if complement(atom) in closure:
            return True
    return False
```

The fast path (`h1 == complement(h2)`) handles the trivial case
where h1 and h2 are complementary literals. This is not a
**bypass** of the closure — the closure path runs whenever the
fast path misses. The closure path is:

1. Seed with `{h1, h2}`.
2. Close under `strict_context` (only rules with
   `kind == "strict"` propagate).
3. Return true iff any atom in the closure has its complement
   also in the closure.

Paper anchor: Garcia 04 Def 3.3 (`notes.md:69-72`, `p.10`):
"Two literals h and h₁ disagree iff the set Π ∪ {h, h₁} is
contradictory." "Contradictory" in DeLP means "strict closure
contains a complementary pair" (inferred from Prop 4.2 and the
Def 3.1 cond 2 treatment — see Q10).

The fast path is semantically equivalent to a closure-path result
(complementary literals already contain their own complement by
definition, so seeding `{p, ~p}` and closing gives
`{p, ~p}`-plus-whatever, and `~p` is immediately in the closure as
`complement(p)`). So the fast path is an optimization, not a
deviation.

**Is the closure path actually exercised?** The B1.3 test suite
includes `disagrees_via_strict_rule`, and
`tests/test_disagreement.py` has three `@given` properties at
`max_examples=500`, one of which generates non-complementary
literals connected via strict rules. The analyst confirmed these
tests exist and pass. I did not re-run them, but the combination
of a symmetric property + a non-complementary-strict-rule case
forces the closure path to be exercised.

**No red flag.** The fast path is correct optimization, not a
bypass.

One thing I looked for and did not find: an old optimization where
`disagrees` would skip the closure entirely when `strict_context`
is empty. That would be a drift (empty strict closure ≠ empty
closure of a seed set; the seed set itself counts). The gunray
code does the closure unconditionally, so the edge case is fine.

### Q8 — Does the four-section projection preserve the propstore contract? **YES.**

`src/gunray/defeasible.py:187-195`:

```python
sections = {
    "definitely": _atoms_to_section(definitely_atoms),
    "defeasibly": _atoms_to_section(defeasibly_atoms),
    "not_defeasibly": _atoms_to_section(not_defeasibly_atoms),
    "undecided": _atoms_to_section(undecided_atoms),
}
model = DefeasibleModel(
    sections={name: facts_map for name, facts_map in sections.items() if facts_map}
)
```

Four keys. Byte-identical strings. Constructed unconditionally,
then filtered to drop empty ones when building the
`DefeasibleModel` — which preserves the **existing** gunray
behavior (the pre-refactor `defeasible.py` did the same filtering
at `defeasible.py:229-230` as shown in scout 2.2). Propstore reads
`bundle.sections["definitely"]` by string; both the refactor and
the pre-refactor code omit empty keys. Neither the key spelling
nor the omission rule changed.

The section projection rules at `defeasible.py:108-117`
(comment block) are:

```
strict   = ∃⟨∅, h⟩
yes      = ∃⟨A, h⟩ marked U
no       = ∃⟨A, complement(h)⟩ marked U
definitely    iff strict
defeasibly    iff yes OR strict
not_defeasibly iff no AND NOT strict
undecided     iff (NOT yes AND NOT no AND NOT strict)
               AND (some argument for h or complement(h) exists)
```

These are the B1.6 prompt verbatim and they correctly handle the
overlap rule: **strict atoms appear in both `definitely` and
`defeasibly`** (because `defeasibly iff yes OR strict`, line
139). That is the propstore "strict is a subset of defeasible"
contract the scout report highlighted at §2.2. I spot-checked this
by reading the classification branch at `defeasible.py:137-149`:
if `strict`, both `definitely_atoms.add(atom)` and (inside the
`if yes or strict:` block) `defeasibly_atoms.add(atom)` fire.
Correct.

**UNKNOWN handling**: the projection filter at line 130 skips
atoms whose predicate is not in the language, so they land in
**no** section. That matches the pre-refactor "don't invent atoms"
behavior.

**No red flag on section contract.** The four-section projection
is byte-compatible with the pre-refactor shape.

One curiosity: the code **also** classifies strict atoms into
`defeasibly_atoms` even though they are also in `definitely_atoms`
(line 140 unconditionally adds to both). This is the intended
"strict ⊂ defeasibly" overlap, and propstore reads both sections
independently. Correct.

### Q9 — Is anything smuggled in under a "paper says X" docstring? **NO.**

I read every docstring citation in the four argumentation modules:

| File | Location | Citation | Code matches? |
|---|---|---|---|
| `arguments.py:1` | module | Def 3.1 + Simari 92 Def 2.2 | **Yes** — builds a pair with three conditions. |
| `arguments.py:42` | `Argument` | Def 3.1 | **Yes** — pair (rules, conclusion). |
| `arguments.py:58` | `is_subargument` | Fig 1 | **Yes** — subset on rules, reflexive partial order. |
| `arguments.py:70` | `build_arguments` | Def 3.1 / Simari 92 Def 2.2 | **Yes** — enforces all three conditions, the minimality + non-contradiction + derivability check is the paper's. |
| `arguments.py:212` | `_force_strict_for_closure` | Def 3.1 cond 1 | **Yes** — wraps defeasible rules as strict for closure computation. **Key for Q10** — see §3.10. |
| `disagreement.py:1` | module | Def 3.3 verbatim | **Yes** — computes strict closure of seeds and looks for complementary pairs. |
| `disagreement.py:41` | `strict_closure` | (no paper cite; helper) | n/a |
| `disagreement.py:68` | `disagrees` | Def 3.3 | **Yes**. |
| `dialectic.py:1` | module | Defs 3.4, 4.1, 4.2, 4.7, 5.1; Proc 5.1 | **Yes** — all five plus the procedure. |
| `dialectic.py:84` | `counter_argues` | Def 3.4 (literally quoted) | **Yes** — iterates sub-arguments per the existential quantifier. |
| `dialectic.py:104` | `_disagreeing_subarguments` | Defs 3.4, 4.1, 4.2 | **Yes** — returns all disagreeing sub-arguments. |
| `dialectic.py:126` | `proper_defeater` | Def 4.1 | **Yes** — pairs `_disagreeing_subarguments` with `criterion.prefers`. |
| `dialectic.py:147` | `blocking_defeater` | Def 4.2 | **Yes** — pairs `_disagreeing_subarguments` with neither-prefers. |
| `dialectic.py:168` | `DialecticalNode` | Def 5.1 | **Yes** — immutable node with argument + children tuple. |
| `dialectic.py:180` | `_concordant` | Def 4.7 cond 2 | **Yes** — unions rule sets with Π, closes, rejects contradictions. Uses `_force_strict_for_closure` for cond-2 parity with Def 3.1. |
| `dialectic.py:240` | `build_tree` | Def 5.1 + Def 4.7 (four conditions enumerated) | **Yes** — all four conditions enforced at every admit. |
| `dialectic.py:336` | `mark` | Proc 5.1 | **Yes** — leaf U, any-U-child D, all-D-children U. |
| `dialectic.py:441` | `_theory_predicates` | Def 5.3 UNKNOWN | **Yes** — builds language from facts, rule heads, rule bodies. |
| `dialectic.py:467` | `_is_warranted` | Def 5.2 (warrant) | **Yes** — "some argument has a U-root tree". |
| `dialectic.py:489` | `answer` | Def 5.3 | **Yes in main paths**, literal-wording gap on the predicate-in-language-no-argument fallback (see Q5). |
| `preference.py:1` | module | §4 | **Yes** — protocol. |
| `preference.py:18` | `PreferenceCriterion` | §4 | **Yes**. |
| `preference.py:26` | `TrivialPreference` | Defs 4.1, 4.2 | **Yes** — `prefers` always False. |
| `answer.py:1` | module | Def 5.3 | **Yes**. |
| `answer.py:8` | `Answer` | Def 5.3 | **Yes** — four values. |
| `defeasible.py:1` | module | Garcia 04 §5 | **Yes** — argument pipeline projecting into sections. |

Every docstring citation matches the code underneath it. The
closest thing to a smuggled-in deviation is the `answer` fallback
at Q5, which is a literal-wording gap rather than a citation
mismatch: the docstring and the code both implement Def 5.3's
main paths correctly; only the fallback path for "predicate in
language but no argument" deviates from the paper's literal
reading of UNKNOWN. That is an observation-level issue, not a
violation.

**No red flag.** Zero smuggled code.

### Q10 — Is the `nests_in_trees` deviation actually paper-correct? **YES. The coder's reading of Def 3.1 cond 2 is correct.**

This is the critical question and I want to be definitive.

#### The claim under review

B1.6's deviation in
`notes/refactor_progress.md#deviations` (lines 587-670) argues:

Given the theory

```
strict:       s1: ~flies(X) :- penguin(X)
              s2: bird(X)   :- penguin(X)
facts:        penguin(tweety).
defeasible:   r3: flies(X)          :- bird(X)
              r4: nests_in_trees(X) :- flies(X)
```

Π's strict closure already contains `~flies(tweety)`. Adding `r3` to
any candidate `A` puts `flies(tweety)` in the closure of `Π ∪ A`
(via the defeasible rule `r3` propagating on the strict chain
`penguin(tweety) → bird(tweety)`). So the closure contains both
`flies(tweety)` and `~flies(tweety)`. By Def 3.1 cond 2 (Π ∪ A is
non-contradictory) **no argument exists for `flies(tweety)` under
any A** — every candidate `A` fails cond 2.

Consequently no argument exists for `nests_in_trees(tweety)`
either: every candidate derivation of `nests_in_trees(tweety)` must
chain through `r3 → r4`, and every such chain is rejected.

The fixture expects `nests_in_trees: [[tweety]]` in the `undecided`
section. B1.6 says: no. Under the paper, `nests_in_trees(tweety)`
is omitted from every section.

The alternative reading Q10 offers is: "Π ∪ A is non-contradictory"
might be a purely set-theoretic check — `{penguin(tweety),
(~flies(X) :- penguin(X)), r3}` has no syntactic complementary
pair as a *set of formulas*, so cond 2 is satisfied. Under that
reading `⟨{r3}, flies(tweety)⟩` is a valid argument and the
fixture would pass.

Which reading is correct?

#### The paper-based answer: the coder is right.

**Evidence 1: Simari 92 Def 2.2 is explicit.**

`papers/Simari_1992_MathematicalTreatmentDefeasibleReasoning/notes.md:39-44`
(Simari 92 p.9) defines:

```
⟨T, h⟩_K iff
  (1) K ∪ T |~ h
  (2) K ∪ T |/~ ⊥
  (3) ∄ T' ⊂ T, K ∪ T' |~ h
```

Condition 2 is `K ∪ T |/~ ⊥` — "K ∪ T does **not defeasibly
derive** ⊥". The relation `|~` is the defeasible consequence
operator defined at Simari 92 p.6 (notes.md:32-37):

> Γ |~ A iff there exists a sequence B₁, ..., B_m with A = B_m
> and each B_i is an axiom, or A_i ∈ Γ, or A_i follows by modus
> ponens or instantiation of a universally quantified sentence.

In other words: chain the rules. This is exactly the defeasible
derivation of Def 2.5 (Garcia 04). The contradiction check under
Simari 92 Def 2.2 cond 2 **must chain the rules in T**. Not a
syntactic set test.

Applied to the tweety case: T = {r3}, K = {penguin(tweety), s1,
s2}. Is `K ∪ T |~ ⊥`? Yes: K |~ penguin(tweety), K |~ bird(tweety)
via s2, K |~ ~flies(tweety) via s1 (all strict), K ∪ T |~
flies(tweety) via r3 (defeasible), and flies(tweety) contradicts
~flies(tweety). So `K ∪ T |~ ⊥`. Cond 2 fails. ⟨{r3}, flies(tweety)⟩
is not an argument structure.

The coder's reading is paper-exact under Simari 92 Def 2.2.

**Evidence 2: Garcia 04 Prop 4.2 would be vacuous under the
alternative reading.**

`papers/Garcia_2004_DefeasibleLogicProgramming/claims.yaml:72-83`
(claim6) records Proposition 4.2:

> No argument structure in DeLP can be self-defeating because the
> requirement that Π ∪ A be non-contradictory prevents any argument
> from containing a counter-argument point against itself.
> *(p.18, Proposition 4.2)*

A "self-defeating" argument in the Simari 1992 / Garcia 2004 sense
is one where applying A's own rules produces a contradiction with
its own conclusion. Under the set-theoretic alternative reading,
"Π ∪ A is non-contradictory" only excludes syntactic
complementary-literal pairs at the top level of the set. A set
like {penguin(tweety), (~flies(X) :- penguin(X)), (flies(X) :-
bird(X))} has no such pair. Under the alternative reading,
self-defeating arguments are **not prevented** by cond 2 — cond 2
would be satisfied by the set regardless of what the rules chain
into.

The only way Prop 4.2's claim has teeth is if "non-contradictory"
is interpreted as "the closure of Π ∪ A under all applicable rules
(strict and A's defeasible) contains no complementary pair". That
is exactly what `_force_strict_for_closure` does.

Garcia 04 Prop 4.2 is therefore a direct corroboration of Simari
92 Def 2.2's `|/~ ⊥` semantics: cond 2 is about defeasible closure,
not about set membership.

**Evidence 3: the `henrietta` control case.**

The coder report and the analyst report both point out that the
same four-rule theory, with `penguin(tweety)` replaced by
`bird(henrietta)` (no penguin fact), produces a **different
outcome**: `nests_in_trees(henrietta)` lands in `defeasibly`
because there is no strict rule firing `~flies(henrietta)`, so
`⟨{r3, r4}, nests_in_trees(henrietta)⟩` is a valid argument.

Under the set-theoretic alternative reading, henrietta and tweety
would produce the same outcome, because the **set** `Π ∪ A` is
non-contradictory in both cases (the set doesn't contain
`flies(X)` or `~flies(X)` as standalone sentences — only as rule
heads). But the **closure** differs: tweety's closure contains the
complementary pair, henrietta's does not. The analyst's live
spot-check at Check 7 confirms the pass/fail split. That split
can only be explained under the Simari 92 `|/~ ⊥` reading.

**Evidence 4: Garcia 04's definition of "contradictory" across
Def 3.3 and Def 3.1 is uniform.**

Garcia 04 Def 3.3 (`notes.md:69-72`) says two literals disagree iff
"Π ∪ {h, h₁} is contradictory". The gunray `disagrees` implementation
(also in `_has_contradiction` used for cond 2) computes the strict
closure and looks for a complementary pair. Everyone agrees this
is the right reading for Def 3.3 — nobody thinks `disagrees(p, q)`
is a syntactic set-membership test. The analyst, the coder, and
the scout all treat Def 3.3 as closure-based.

But Def 3.3 uses the exact same language as Def 3.1 cond 2
("contradictory" vs. "non-contradictory"). The paper does not
define these terms separately — they are the same property applied
to different sets. If Def 3.3 is closure-based (which nobody
contests), Def 3.1 cond 2 is closure-based too. Under that
uniform reading, the coder is right and the fixture is wrong.

#### Is `_force_strict_for_closure` over-eager?

No. It is literally the `|~` consequence operator from Simari 92
Def 2.2 cond 2, applied to A ∪ Π for contradiction detection.
Wrapping defeasible rules as strict-kind for the purpose of
`strict_closure(facts, rules)` propagation is the mechanical way
to say "chain under A's rules too". The wrapper is confined to
the closure computation inside `build_arguments` and `_concordant`
— it does not leak into the argument structures themselves (the
`Argument` objects still carry the original defeasible rules).
The wrapper is a local implementation detail, not a semantic
change.

One nuance I want to record: the wrapper treats **every** rule in
A as a propagator during the contradiction check, which is
slightly stronger than Simari 92's "some derivation exists"
quantifier. But `strict_closure` is a closed-world consequence
(it derives everything derivable), and Simari 92's
`K ∪ T |~ ⊥` asks whether **any** derivation produces ⊥, which is
equivalent to "⊥ is in the closure". So the closed-world treatment
is correct.

#### Bottom line

**The coder's reading of Def 3.1 cond 2 is paper-correct.**

The `_force_strict_for_closure` treatment is not over-eager — it is
the mechanical implementation of Simari 92 Def 2.2's `|/~ ⊥` under
the closed-world defeasible consequence operator.

The `depysible_nests_in_trees_tweety` and
`depysible_nests_in_trees_tina` fixtures expect
`undecided: {nests_in_trees: [(tweety)]}` (and `(tina)`). Under
the paper, no argument for `nests_in_trees(tweety/tina)` exists,
so the literal is omitted from every section. The fixtures encode
the pre-paper depysible classifier's behavior (which used a
non-Garcia `supported_only_by_unproved_bodies` reason code), not
Garcia & Simari 2004.

**The deviation stands.** B1.6 is paper-correct to refuse the
fixture. Block 2's `GeneralizedSpecificity` will not and cannot
fix these cases — the rejection is at the Def 3.1 cond 2 level,
which is independent of any preference criterion. Foreman
decision is needed on whether to update the upstream fixture, not
on whether to change the gunray code.

**Flag**: GREEN (deviation is correct).

---

## 4. Disagreements with the analyst

The analyst's `b1-analyst.md` is thorough and I agree with every
substantive finding. Specifically:

- I agree with the directional fix audit (Check 5) — the
  sub-argument descent is correct and non-trivially tested.
- I agree with the Def 4.7 enforcement audit (Check 6 property
  test table).
- I agree with the deleted-symbol tripwire interpretation (Check 1:
  the docstring reference is prose and should stay).
- I agree with the conformance classification audit (Check 7),
  including the three-way nests_in_trees henrietta-vs-tweety/tina
  outcome validation.
- I agree with the two deviations being justified at the right
  level (Check 8).

**Two small differences**:

1. **Q5 / answer() fallback** — the analyst observation 5 says the
   fallback "is a minor correctness fuzz" and takes no position on
   whether UNKNOWN or UNDECIDED is the right answer. I think
   **UNKNOWN** is the literal-wording-correct target for the
   predicate-in-language-no-argument edge case, because Def 5.3
   explicitly gates UNDECIDED on "at least one argument exists".
   The analyst is right that the gap is mostly unreachable; I am
   specifying the fix direction in case Block 2 or Block 3 picks
   this up.

2. **Q10 / nests_in_trees deviation** — the analyst agrees the
   deviation is paper-correct and independently verified the
   closure reasoning by tracing the theory manually. I agree.
   Where I go further is in anchoring the verdict to **Simari 92
   Def 2.2 cond 2's literal form `K ∪ T |/~ ⊥`**. That form
   removes any ambiguity about whether "Π ∪ A non-contradictory"
   is set-theoretic or closure-based — it is unambiguously
   closure-based, because `|~` is the defeasible consequence
   operator defined at Simari 92 p.6. The analyst's verdict is
   correct; my version of it is one level more definitive.

No substantive disagreement. The analyst missed no VIOLATION and
flagged no phantom DRIFT.

---

## 5. Recommendations to the foreman

**Things to leave alone:**

1. **The `nests_in_trees` deviation.** Paper-correct. Do not
   re-introduce the deleted `supported_only_by_unproved_bodies`
   classifier. Do not add a "depysible compatibility" mode.
2. **`_force_strict_for_closure`.** It is the mechanical
   implementation of Simari 92 Def 2.2 cond 2. Do not try to make
   it smarter.
3. **The sub-argument-descent attack.** Correct as implemented.
   Block 2's performance optimizations can memoize `build_arguments`
   or introduce `arguments_for(literal)`, but must not weaken the
   descent.
4. **The `mark` function.** It is Proc 5.1 on a line of code. Any
   caching or mutation "optimization" would introduce bugs.

**Things to fix (not blockers for Block 2 start):**

1. **The `answer()` fallback UNKNOWN gap (Q5)**. One-line fix:
   when `has_argument_for_either` is false, return UNKNOWN
   regardless of the predicate-in-language check. Alternatively,
   make the predicate-in-language check more conservative (a
   predicate is "in the language" iff it has at least one ground
   literal derivable under Π∪Δ, not iff its symbol appears in the
   source). Either fix is a local change with no downstream
   consequences. **Recommended for Block 2**, during the answer()
   consolidation the analyst mentioned at §5 Q3.

2. **Plan exit criterion mismatch on `nests_in_trees`**. The plan
   states "Block 1 ends when ... both `nests_in_trees` cases produce
   correct answers via the new pipeline". Under paper semantics,
   the `tweety` and `tina` cases CORRECTLY produce "no section"
   rather than the fixture's `undecided`. The `henrietta` case
   correctly produces `defeasibly: [[henrietta]]`. Either reword
   the criterion ("produce paper-correct answers, whether or not
   they match the fixture") or update the upstream
   `datalog_conformance` fixture for the tweety/tina cases. I
   recommend the latter — the fixture is wrong. This is a
   foreman-level decision.

3. **`__init__.py` re-exports** — the scout directive §1.5 listed
   the new public symbols that should be re-exported. None of them
   are. This is a Block 3 concern (propstore consumer), not a
   directional issue, but worth adding to the Block 3 todo list
   so it doesn't get forgotten.

4. **Vulture dead-code gate** never ran in Block 1 (not installed
   in the venv). Install it or document removal from the plan's
   gate table. Not directional.

**Things to consider for Block 2:**

1. **Performance on large defeasible rule sets.** The current
   `build_arguments` is `O(2^|Δ|)`. Block 2's
   `GeneralizedSpecificity` will exacerbate this because each
   defeat check invokes `build_arguments` again inside
   `_disagreeing_subarguments`. Consider memoizing
   `build_arguments(theory)` at the module level or introducing a
   per-`build_tree` cache. Already flagged as a Block 2 concern in
   `reports/b1-disagreement-and-build-arguments.md` and acknowledged
   by the analyst's Q1.

2. **Block 2's `GeneralizedSpecificity` will not resolve the
   `nests_in_trees_{tweety,tina}` regression.** The analyst
   already flagged this. The foreman needs to enter Block 2 with
   the understanding that the verifier gate for these two cases
   is unachievable under paper semantics, and the plan's Block 2
   exit criterion needs pre-adjustment.

---

## 6. Summary

Block 1 is paper-aligned. The five coders produced a `Argument`
type that is exactly a pair, a `counter_argues` that descends into
sub-arguments, a `build_tree` that enforces every Def 4.7
condition at every child-admission, a `mark` that is Proc 5.1 on a
line of code, an `answer` that implements Def 5.3 in its main
paths, a `disagrees` that computes the strict closure per Def 3.3,
and a `build_arguments` that enforces all three Def 3.1 conditions
including the closure-based non-contradictory check.

The `nests_in_trees` deviation is paper-correct under Simari 92
Def 2.2 cond 2's literal `K ∪ T |/~ ⊥` reading, and is
corroborated by Garcia 04 Prop 4.2 (no self-defeating arguments)
and the `henrietta` control case.

My verdict is **ALIGNED**. No VIOLATION, no DRIFT. Two observations
(Q5 UNKNOWN fallback wording; docstring tripwire at
`dialectic.py:96`) are non-blocking and can be addressed in Block
2 or Block 3.

Block 1 is ready for Block 2, pending a foreman-level decision on
the `nests_in_trees_{tweety,tina}` fixture/plan mismatch that the
analyst already flagged.
