# Surface D — I/O and public API review

## 2026-04-16

**GOAL:** Audit `parser.py`, `schema.py`, `types.py`, `errors.py`, `adapter.py`, `__init__.py`, `trace.py`, `conformance_adapter.py` against README contract. Verify four prior findings (preference exports gap, Policy.PROPAGATING fate, trace argument-centricity, parser robustness). Deliver one .md to `reviews/2026-04-16-full-review/surface-d-io-and-api.md`.

**DONE so far:**
- Read README, `__init__.py`, `parser.py`, `schema.py`, `types.py`, `errors.py`, `adapter.py`, `trace.py`, `conformance_adapter.py`, `preference.py`, prior notes (`readme_rewrite.md`, `policy_propagating_fate.md`, `what_sucks_review.md`).
- Skim of `defeasible.py` lines 1-265, `arguments.py` 40-127, `dialectic.py` (function map + 160-220).

**OBSERVATIONS / FINDINGS gathered:**

1. **Preference exports gap CONFIRMED.** `__init__.py:19` imports only `PreferenceCriterion, TrivialPreference`. README line 143 says `from gunray.preference import GeneralizedSpecificity` — that's the README's own escape hatch, but `GeneralizedSpecificity`, `SuperiorityPreference`, `CompositePreference` are NOT in `__all__` (`__init__.py:29-61`). The README opted to import from the submodule directly, which works but is inconsistent with how every other paper-level type is exported. Decide: surface them or document that `gunray.preference` is the second-tier surface.

2. **Policy.PROPAGATING fully removed (not deprecated-with-warning).** `schema.py:59-62` lists only `BLOCKING, RATIONAL_CLOSURE, LEXICOGRAPHIC_CLOSURE, RELEVANT_CLOSURE`. No DeprecationWarning shim. Callers writing `Policy.PROPAGATING` get `AttributeError`; callers writing `Policy("propagating")` get `ValueError`. Comment at `schema.py:3-9` and docstring at `schema.py:48-51` document the decision. **The "clear error per `notes/policy_propagating_fate.md`" is actually a raw `AttributeError`, not a custom error.** That's the trade-off the foreman accepted (notes/policy_propagating_fate.md:79-89).

3. **Trace upgrade NOT delivered.** `trace.py` is still entirely rule-fire / atom-classification centric. Lines 124-141 define `ProofAttemptTrace` and `ClassificationTrace` keyed by `GroundAtom` with `supporter_rule_ids` / `attacker_rule_ids` — flat lists, no `Argument` objects, no `DialecticalNode`/tree, no U/D markings. `DefeasibleTrace.proof_attempts` and `.classifications` (lines 150-155) are flat lists. `Argument` and `DialecticalNode` exist as first-class objects (`arguments.py:43`, `dialectic.py:169`) and `render_tree` exists (`dialectic.py:393`), but **the trace API does not surface them**. The README claims (line 121-127) that traces capture proof attempts with classification — true at the atom level, false at the argument-tree level. The "killer feature" the what-sucks doc identified (an actual dialectical-tree trace) is not in `trace.py`.

4. **GunrayEvaluator dispatch has weird third path.** `adapter.py:42` falls through `isinstance(item, Program)` and `isinstance(item, DefeasibleTheory)` to `self._suite_bridge().evaluate(item, policy)` — which silently constructs a conformance bridge for unknown input types. This means `GunrayEvaluator().evaluate("hello")` will try the suite bridge (which then either translates a suite type or raises `TypeError`). Not a clean dispatch.

5. **Strict-only DefeasibleTheory shortcut.** `defeasible.py:74` `_is_strict_only_theory` checks `not theory.defeasible_rules and not theory.defeaters and not theory.superiority`. **Conflicts are not checked.** A theory with conflicts but no defeasible/defeaters/superiority will still hit the strict-only Datalog shortcut and skip the dialectical pipeline. Probably correct (no defeasible content = nothing to attack), but worth noting that the shortcut ignores `theory.conflicts`.

6. **Parser robustness:**
   - `_scan_top_level_mask` (parser.py:354-385) handles unbalanced parens with explicit `ParseError` (379, 384), and unterminated string literals (382). Good.
   - `parse_atom_text` requires `)` to be the last char (parser.py:327): `p(x)y` is rejected with "Unsupported atom syntax". Good.
   - `parse_term_text:156` treats anything starting with `_` as a Wildcard (`_foo`, `_X` all become wildcards). That's likely wrong for variables that happen to start with underscore — but Datalog convention is wildcards are `_` only. Documenting as a quirk.
   - `parse_value_term:184-187` falls through to `Variable(name=stripped)` for anything that isn't a scalar. **No validation that the name is a valid identifier.** `Variable(name="foo bar")` or `Variable(name="123abc")` could be constructed via `parse_atom_text("p(foo bar)")` — actually no, split_top_level on commas would not split this, so `Variable(name="foo bar")` would result. Worth flagging.
   - Negation handling: `parse_rule_text:105-106` checks `candidate.startswith("not ")` (4-char prefix). `not\tfoo` (tab) would NOT match. `not(foo)` would NOT match. Likely intentional Datalog convention but brittle.
   - Unicode predicates: there's no validation of the predicate name in `parse_atom_text:139`. `Atom(predicate="π")` would be accepted. Fine but undocumented.
   - `_parse_unquoted_scalar` (parser.py:403-415) returns `None` for unrecognized strings, causing `_parse_scalar` to also return None, causing `parse_value_term:187` to fall through to `Variable`. So `"foo"` becomes a Variable named `foo`. There is no way to write a string constant without quotes — that's by design but not validated.

7. **`schema.py` invariants NOT enforced at construction.**
   - `Program(facts={...}, rules=["malformed garbage"])` constructs fine; rules are only parsed when the evaluator is called.
   - `DefeasibleTheory` accepts arbitrary tuples for `superiority` and `conflicts`; no validation that referenced rule_ids exist or that conflicts predicates exist.
   - `Rule(id="", head="", body=[])` constructs fine — empty IDs and empty heads are legal at the dataclass level. Parser will catch some of these later.
   - All `@dataclass(slots=True)` (NOT frozen). `Program.facts` mutates after construction. `theory.strict_rules.append(...)` works.

8. **`types.py` is good.** All key types `@dataclass(frozen=True, slots=True)`: `Variable`, `Wildcard`, `Constant`, `Atom`, `Rule`, `GroundAtom`, `DefeasibleRule`, `GroundDefeasibleRule`. Hashable, comparable by value. (lines 12-93)

9. **`errors.py`:** Clean hierarchy with `code` attributes for conformance-suite compatibility. No issues.

10. **`conformance_adapter.py` translation:**
    - `_translate_rule:44` copies `rule.id, rule.head, rule.body` only. **If the suite's Rule has additional fields (e.g. priority, tag), they are silently dropped.** Unknown if the suite has any.
    - `_copy_facts:37-41` casts every row via `tuple(row)`. Loses any per-row metadata.
    - `_translate_policy:75` raises `TypeError` on unknown policy types — good. But `_translate_policy:74` does `Policy(policy.value)` — if the suite has `policy.value == "propagating"`, this raises `ValueError` ("propagating' is not a valid Policy"). Caller gets a generic ValueError rather than a Gunray-specific message.

11. **`adapter.py:25-27`:** `bridge._core = self` reaches into the bridge's private `_core` attribute. Tight coupling; if `GunrayConformanceEvaluator.__init__` changes its private name, this breaks silently.

12. **Public surface `__all__` audit:** All 32 names in `__init__.py:29-61`'s `__all__` correspond to a successful import in lines 3-27. No phantom exports. Public-looking names not in `__all__`: none in `__init__.py` itself, but submodules like `preference.py` expose `GeneralizedSpecificity`, `SuperiorityPreference`, `CompositePreference` without re-export. `_force_strict_for_closure` and `_ground_theory` (private) are imported by `preference.py:18` from `arguments.py` — leaking private symbols across module boundaries.

**STUCK:** Not stuck. Have enough material for the deliverable.

**NEXT:** Write the deliverable to `reviews/2026-04-16-full-review/surface-d-io-and-api.md`. Cap at ~1400 words. Each finding cites file:line.
