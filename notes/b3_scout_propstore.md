# B3.1 Propstore Surface Scout — progress notes

Date: 2026-04-13

## GOAL
Inventory every propstore consumer of gunray for the B3.2 coder.
Report path: `C:\Users\Q\code\gunray\reports\b3-scout-propstore.md`.

## DONE
- Read prompt `prompts/b3-scout-propstore.md`.
- Grepped `from gunray|import gunray` across propstore → 23 matches across 9 files (2 are plan/notes docs, 3 are logs, 4 are real source/test files).
  - Real source files: `propstore/grounding/translator.py` (1), `propstore/grounding/grounder.py` (2).
  - Real test files: `tests/test_grounding_translator.py` (9), `tests/test_grounding_grounder.py` (1), `tests/test_defeasible_conformance_tranche.py` (5).
- Read `propstore/grounding/grounder.py` in full: `ground(rule_files, facts, registry, *, policy=Policy.BLOCKING) -> GroundedRulesBundle`, uses `_normalise_sections(raw_model.sections)` with `_FOUR_SECTIONS` tuple.
- Read `propstore/grounding/bundle.py` in full: `GroundedRulesBundle` is `@dataclass(frozen=True)` with fields `source_rules: tuple[LoadedRuleFile, ...]`, `source_facts: tuple[GroundAtom, ...]`, `sections: Mapping[...]`. Has `empty()` classmethod and module-level `_build_empty_sections()` helper.
- Read `_split_section_predicate` at `propstore/aspic_bridge.py:203-214`. Called at lines 431 (inside `grounded_rules_to_rules`) and 524 (inside `_ground_facts_to_axioms`). Both callers unpack polarity + stripped predicate name.
- Confirmed `Policy.PROPAGATING` references in live propstore code:
  - `propstore/tests/test_grounding_grounder.py:640` (docstring) + `:661` (actual call with `policy=Policy.PROPAGATING`). Count = 2 live references + 1 docstring mention in `propstore/grounding/grounder.py:131` mentioning "BLOCKING and PROPAGATING" (no actual symbol use).
  - `propstore/tests/test_defeasible_conformance_tranche.py` has `from gunray.schema import Policy` at line 206 and uses `Policy(policy_name)` at line 213 — policy value is passed in from parametrization, need to find the parametrize markers to see if `"propagating"` strings appear.
  - Prompt says lines 37, 43 of tranche file — those are `_GUNRAY_TRANCHE_IDS`/`_PROPSTORE_TRANSLATION_TRANCHE_IDS` strings that contain `"antoniou_ambiguous_attacker_blocks_only_in_propagating"` — that's a **test case name string**, not the enum value. Need to verify whether these count as a breakage point. Probably not — they are YAML test IDs.

## STILL TO DO
- Read `propstore/propstore/grounding/translator.py` (need the gunray-schema import context + how sections are consumed).
- Finish reading `propstore/tests/test_defeasible_conformance_tranche.py` lines 220+ to see parametrize `policy_name` values (might contain `"propagating"` string literals).
- Read `propstore/tests/test_grounding_grounder.py` around lines 630-680 for the full `Policy.PROPAGATING` test.
- Read `propstore/tests/test_grounding_translator.py` — 9 imports, needs full surveying for `model.sections` access + string-parsing of predicates.
- Grep `model.sections|bundle.sections|.sections[|"definitely"|"defeasibly"|"not_defeasibly"|"undecided"` across propstore.
- Read `propstore/pyproject.toml` for the gunray dependency wiring.
- Find test invocation command (likely `uv run pytest tests -q` in propstore root) + any relevant conftest.
- Check for any gunray imports I might have missed outside `from/import` (e.g. `importlib` or path hacks).
- Write the final report to `reports/b3-scout-propstore.md`.

## KEY OBSERVATIONS
- `_split_section_predicate` is purely propstore-internal — two call sites, both in `aspic_bridge.py`. The B3.2 coder can replace calls with reads of `Argument.conclusion` once gunray exposes arguments through the new field.
- `GroundedRulesBundle` is a **frozen dataclass**, not slotted, not NamedTuple. Adding a new optional field is straightforward — must use `field(default=...)` or factory, and it's a dataclass so field order matters.
- `ground()` signature: `(rule_files: Sequence[LoadedRuleFile], facts: tuple[GroundAtom, ...], registry: PredicateRegistry, *, policy: Policy = Policy.BLOCKING) -> GroundedRulesBundle`. Adding a keyword like `return_arguments: bool = False` after `policy=` is trivial.
- The grounder casts `evaluator.evaluate(theory, policy)` → `DefeasibleModel`. The B3.2 coder will need to know that gunray must expose arguments separately (or the new `DefeasibleModel` shape already carries them).

## STUCK
Not stuck.

## CHECKPOINT 2 ADDITIONS
- Read `propstore/grounding/translator.py` in full. It imports only `from gunray import schema as gunray_schema` at module scope. Uses `gunray_schema.Scalar`, `gunray_schema.Rule`, `gunray_schema.DefeasibleTheory`. No section access, no Policy references. `_stringify_atom` emits `~predicate(args)` surface for negated atoms — this is the *inverse* of `_split_section_predicate`: propstore feeds `~` INTO gunray via predicate text, and gunray echoes it back on the way out. The B3.2 coder will see that propstore's strong-negation surface round-trips via gunray's string layer.
- Read `tests/test_defeasible_conformance_tranche.py` 220+: it iterates `case.expect_per_policy.items()` and calls `Policy(policy_name)` with `policy_name` coming from the suite YAML (keys like `"propagating"` / `"blocking"`). If B2.3 deprecated `Policy.PROPAGATING`, whether this breaks depends on whether `Policy("propagating")` still resolves. This is a RUNTIME string-to-Policy construction — **not** a direct `Policy.PROPAGATING` symbol reference.
- Read `tests/test_grounding_grounder.py` 605-723: `test_grounder_policy_is_configurable` constructs `policy=Policy.PROPAGATING` and asserts `bundle.sections["defeasibly"].get("flies", frozenset())`. This is the only direct `Policy.PROPAGATING` symbol use in propstore.
- Read `pyproject.toml`: `gunray @ git+https://github.com/ctoth/gunray`. `uv.lock` pins gunray to commit `5078df5ee65ae17ee2a614299ba395ed8a7664d9` (Jan-dated, not current master HEAD). The B3.2 coder will need to `uv add` or `uv lock --upgrade-package gunray` to pull the latest.
- Read `tests/conftest.py`: NO grounder/bundle/policy fixtures. All grounder tests build rule documents inline. The B3.2 coder does not inherit shared fixtures — every test constructs bundles via direct `GroundedRulesBundle(...)` calls.
- All `bundle.sections[...]` / `bundle.sections.get(...)` accesses in propstore (full list):
  - propstore/aspic_bridge.py:429 (in grounded_rules_to_rules)
  - propstore/aspic_bridge.py:522 (in _ground_facts_to_axioms)
  - propstore/grounding/grounder.py:164 (raw_model.sections read, not bundle.sections)
  - propstore/sidecar/rules.py:183 (read in populate())
  - tests: test_grounding_grounder.py ×10, test_gunray_integration.py ×5, test_sidecar_grounded_facts.py ×4

## COUNT of Policy.PROPAGATING that B2.3 breaks (direct symbol refs only)
- 1 direct symbol use: `tests/test_grounding_grounder.py:661` (call site)
- 1 docstring mention: `tests/test_grounding_grounder.py:640` (docstring describes "Policy.PROPAGATING" in triple-backticks — will not cause runtime break but should be updated for consistency)
- 1 docstring mention: `propstore/grounding/grounder.py:131` (docstring says "BLOCKING and PROPAGATING" — bare word, not the symbol)
- INDIRECT risk: `tests/test_defeasible_conformance_tranche.py:206-213` calls `Policy(policy_name)` where `policy_name` may be the string `"propagating"` from YAML suite cases. This breaks iff B2.3 removed the enum value (not just the attribute).
- Runtime-breaking direct symbol references: **1** (`test_grounding_grounder.py:661`). With docstring references: 2. With indirect string-constructor risk: up to 3 files affected.

## NEXT
- Read the `sidecar/rules.py` section-reading block for verbatim context (line 183).
- Read test_gunray_integration.py imports + section-access sites (lines 458, 461, 540, 545, 627, 729).
- Read test_sidecar_grounded_facts.py around line 217/229/451/540.
- Find any `conftest.py` references to gunray (already checked — none).
- Check grounding/__init__.py for re-exports.
- Check logs/tests for any stray gunray imports I might have missed.
- Write the final report.
