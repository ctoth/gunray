# B1.1 Scout Progress

## GOAL
Produce `reports/b1-scout.md` with 6 sections for the B1.2-B1.6 coders. Read-only.

## DONE (2026-04-13)
- Read prompt `prompts/b1-scout.md` (264 lines, 6 sections enumerated).
- Read `src/gunray/__init__.py` (30 lines) — exports DefeasibleEvaluator, DefeasibleModel, DefeasibleTheory, DefeasibleTrace, GunrayEvaluator, Model, Policy, ProofAttemptTrace, Program, Rule, SemiNaiveEvaluator, TraceConfig, DatalogTrace, ClassificationTrace.
- Read `src/gunray/schema.py` (83 lines) — has Policy enum, Program, Rule(id,head,body), DefeasibleTheory, Model, DefeasibleModel. Uses `@dataclass(slots=True)` (NOT frozen — mutable lists). DefeasibleSections is `Mapping[str, ModelFacts]`.
- Read `src/gunray/types.py` (103 lines) — `@dataclass(frozen=True, slots=True)` convention. Has Atom, Rule (AST-style), GroundAtom(predicate, arguments: tuple[Scalar,...]), DefeasibleRule(rule_id, kind, head, body), GroundDefeasibleRule (same shape with GroundAtom). Wildcard, Variable, Constant.
- Read `src/gunray/adapter.py` (71 lines) — GunrayEvaluator dispatches Program→SemiNaiveEvaluator, DefeasibleTheory→DefeasibleEvaluator (or ClosureEvaluator for rational/lex/relevant closure). Has `_suite_bridge()` lazy-loading GunrayConformanceEvaluator.
- Read `src/gunray/conformance_adapter.py` (141 lines) — GunrayConformanceEvaluator with `_core = GunrayEvaluator()`. Reuses `_core` via bridge pattern. Has evaluate(), evaluate_with_trace(), satisfies_klm_property().
- Read `src/gunray/ambiguity.py` (39 lines) — AmbiguityPolicy dataclass, resolve_ambiguity_policy(), attacker_basis_atoms(). Entire file is 39 lines, scheduled for deletion.
- Read `src/gunray/closure.py` (699 lines fully) — `_strict_closure(facts: set[str], strict_rules: list[Rule]) -> set[str]` at lines 198-209 **ONLY handles zero-arity propositional strings, NOT first-order atoms**. KEY FINDING: closure.py is propositional-only and CANNOT be directly reused for `disagrees(h1, h2, K)` with ground atoms. B1.3 coder will need a NEW strict closure over GroundAtom sets. Will flag.
- Read `src/gunray/parser.py` (415 lines fully) — `parse_defeasible_theory(theory) -> tuple[dict[str, set[tuple[Scalar,...]]], list[DefeasibleRule], set[tuple[str,str]]]` at lines 53-69. `parse_atom_text()` at 121. `ground_atom(atom, binding) -> GroundAtom` at 232. `_complement(predicate) -> str | None` at 281 — adds/removes `~` prefix.

## STILL TO DO
- Scan `tests/test_defeasible_core.py` — count tests, private helpers imported, coverage lost.
- Look for strict-only example (Simple one from `strict_only_basic_facts.yaml`).
- Look for goldszmidt_example1_nixon.yaml for Nixon Diamond.
- Write `reports/b1-scout.md` (6 sections).

## NEW DONE (continuation, 2026-04-13)
- Read `src/gunray/defeasible.py` in full (784 lines across 4 pages).
- Read `README.md` (146 lines) — Tweety example lines 8-23 verbatim captured.
- Located `depysible_birds.yaml` fixture at `.venv/Lib/site-packages/datalog_conformance/_tests/defeasible/basic/depysible_birds.yaml`. Contains `depysible_nests_in_trees_tina`, `depysible_nests_in_trees_tweety`, `depysible_nests_in_trees_henrietta`, etc.
- `depysible_nests_in_trees_tina` expects `undecided: nests_in_trees: [[tweety]]` (surprising — query is "tina" but expected is tweety; this appears to match the fact setup).
- Grep for ambiguity imports: only `src/gunray/defeasible.py:24` and `tests/test_defeasible_core.py:6` use it. No other consumers — safe to delete.
- Plan-listed deletions (_can_prove, _find_blocking_peer, _has_blocking_peer, _has_live_opposition, _supporter_survives, _is_more_specific, _strict_body_closure, _expand_candidate_atoms, _attacker_body_available) all verified present in `defeasible.py`.
- `_positive_closure` (defeasible.py:272-290) and `_ground_rules` (defeasible.py:293-325) — bodies captured.
- `_strict_body_closure` (defeasible.py:647-665) — body captured.

## KEY OBSERVATIONS (updated)
1. **closure.py CANNOT be reused for disagrees()**: `_strict_closure(facts: set[str], strict_rules: list[Rule])` operates on zero-arity string literals and rejects parens at line 141-143. B1.3 coder needs a NEW closure over `set[GroundAtom]` / `list[GroundDefeasibleRule]`. The model is `_strict_body_closure` at defeasible.py:647-665 which already operates on GroundAtom sets — but is scheduled for deletion. Coder should RECREATE its logic in the new disagreement module.
2. **schema vs types convention split**: schema.py uses `@dataclass(slots=True)` (mutable, lists); types.py uses `@dataclass(frozen=True, slots=True)`. New Argument and DialecticalNode should follow types.py frozen convention.
3. **ambiguity.py has exactly 2 consumers**: defeasible.py and test_defeasible_core.py. Both scheduled for rewrite/deletion. Safe to delete ambiguity.py entirely.
4. **Strict-only shortcut** `_is_strict_only_theory` (defeasible.py:239-240) must survive B1.2.
5. The `ambiguity` module is imported from `.ambiguity` (relative), not `gunray.ambiguity` (absolute), per defeasible.py:24.

## FILES read
- `src/gunray/{types,schema,__init__,adapter,conformance_adapter,ambiguity,closure,parser,defeasible}.py` all fully read.
- `README.md` fully read.
- `depysible_birds.yaml` partially read (lines 265-501).

## NEXT
1. Read `tests/test_defeasible_core.py` (count, what's imported).
2. Read `strict_only_basic_facts.yaml` for a canonical strict-only example.
3. Read `goldszmidt_example1_nixon.yaml` for Nixon Diamond.
4. Write `reports/b1-scout.md`.

## KEY OBSERVATIONS / SURPRISES
1. **closure.py is propositional-only** (`_ensure_zero_arity_literal` at 141-143 rejects parens). The prompt suggested B1.3 can reuse it for `disagrees`. It CANNOT — the downstream coder must write new strict closure over GroundAtom sets. This is a real finding to flag.
2. **schema.py uses `slots=True` WITHOUT frozen** (mutable lists) — types.py uses `frozen=True, slots=True`. Two conventions. The refactor's new types should follow types.py's frozen convention for Argument/DialecticalNode.
3. The `_complement` helper lives in BOTH parser.py (line 281, predicate-level, str) and closure.py (line 696, literal-level, str). Paper pipeline will likely need ground-atom-level complement.
4. GroundDefeasibleRule already exists in types.py:88-93.

## FILES
- `prompts/b1-scout.md` — the prompt.
- `src/gunray/{types,schema,__init__,adapter,conformance_adapter,ambiguity,closure,parser}.py` — all read.
- Still to read: `src/gunray/defeasible.py`, `README.md`, `tests/test_defeasible_core.py`, fixture files.

## NEXT
Read defeasible.py (paginated — 784 lines), then README.md excerpt, then fixtures, then write reports/b1-scout.md.
