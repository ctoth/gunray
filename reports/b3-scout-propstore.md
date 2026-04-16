# B3.1 Scout Report — Propstore Surface

Scope: inventory of every propstore consumer of gunray for the
Block 3 coder dispatches (B3.2, B3.3, B3.4).

Search roots:
- `C:\Users\Q\code\propstore` (the external consumer).
- `C:\Users\Q\code\gunray` (this repo — consulted only to verify
  symbol shapes referenced from propstore).

Method: `Grep` (ripgrep) + `Read`. No edits; no commits.

---

## Section 1 — Every propstore import of gunray

Pattern: `from gunray|import gunray`. Raw ripgrep match count:
**23 occurrences across 9 files** (via `Grep --output_mode count`).
Two of those files are markdown plans/notes (8 matches); three are
pytest log snapshots (3 matches); only **four files** are live source
or test code. The rest are documentation or historical run logs that
the coder does not need to touch.

### 1A — Source code

**`C:\Users\Q\code\propstore\propstore\grounding\translator.py`** (1 import)

```
70:from gunray import schema as gunray_schema
```

5-line context (lines 66–74):
```python
from __future__ import annotations

import json
from collections.abc import Sequence

from gunray import schema as gunray_schema

from collections.abc import Iterable
```

**`C:\Users\Q\code\propstore\propstore\grounding\grounder.py`** (2 imports)

```
51:from gunray.adapter import GunrayEvaluator
52:from gunray.schema import DefeasibleModel, DefeasibleSections, Policy
```

5-line context (lines 47–55):
```python
from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import cast

from gunray.adapter import GunrayEvaluator
from gunray.schema import DefeasibleModel, DefeasibleSections, Policy

from propstore.aspic import GroundAtom, Scalar
from propstore.grounding.bundle import GroundedRulesBundle
```

### 1B — Tests

**`C:\Users\Q\code\propstore\tests\test_defeasible_conformance_tranche.py`** (5 imports)

```
25:from gunray.conformance_adapter import GunrayConformanceEvaluator
26:from gunray.adapter import GunrayEvaluator
27:from gunray.parser import parse_atom_text
28:from gunray.types import Constant, Variable
206:    from gunray.schema import Policy          # inside _evaluate_translated_suite_theory
```

5-line context (lines 22–32), top-of-file module imports:
```python
from datalog_conformance.schema import DefeasibleTheory as SuiteTheory
from datalog_conformance.schema import Rule as SuiteRule
from datalog_conformance.schema import TestCase as SuiteCase
from gunray.conformance_adapter import GunrayConformanceEvaluator
from gunray.adapter import GunrayEvaluator
from gunray.parser import parse_atom_text
from gunray.types import Constant, Variable
```

5-line context (lines 203–215), deferred import in function body:
```python
def _evaluate_translated_suite_theory(case: SuiteCase, *, policy_name: str | None = None) -> object:
    from propstore.grounding.translator import translate_to_theory
    from gunray.schema import Policy

    assert case.theory is not None
    rule_file = _build_rule_file(case.theory)
    facts = _build_fact_atoms(case.theory)
    registry = _build_registry(case.theory)
    translated = translate_to_theory([rule_file], facts, registry)
    policy = None if policy_name is None else Policy(policy_name)
    return GunrayEvaluator().evaluate(translated, policy)
```

Notable: `Policy(policy_name)` constructs the enum **by value** from
a YAML-derived string. If B2.3 removed the `"propagating"` value
entirely (rather than only the `PROPAGATING` attribute), every
parametrized case whose `expect_per_policy` contains a `"propagating"`
key will fail at `Policy("propagating")`. This is an *indirect*
reference that does not match the `Policy.PROPAGATING` grep but is
runtime-critical.

Module-level `sys.path` wiring at the top of the same file
(lines 9–19) inserts `../gunray/src` into `sys.path`:
```python
_REPO_ROOT = Path(__file__).resolve().parents[1]
_SUITE_SRC = _REPO_ROOT.parent / "datalog-conformance-suite" / "src"
_GUNRAY_SRC = _REPO_ROOT.parent / "gunray" / "src"

for _path in (_SUITE_SRC, _GUNRAY_SRC):
    if not _path.exists():
        raise FileNotFoundError(f"Required sibling source tree not found: {_path}")
    path_text = str(_path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)
```

This means the tranche test **does not** load gunray via the
installed git package — it loads gunray from a sibling working tree.
The B3.2 coder must ensure `C:\Users\Q\code\gunray\src` stays in
place.

**`C:\Users\Q\code\propstore\tests\test_grounding_translator.py`** (9 imports, all deferred into test bodies)

```
449:    from gunray.parser import parse_atom_text
479:    from gunray.parser import parse_atom_text
570:    from gunray import schema
607:    from gunray.parser import parse_atom_text
608:    from gunray.types import Variable
761:    from gunray.parser import parse_atom_text
784:    from gunray.parser import parse_atom_text
812:    from gunray.parser import parse_atom_text
813:    from gunray.types import Constant
```

All nine are local imports inside `test_*` functions — the file's
top-level imports avoid gunray on purpose (the module predated the
translator rewrite and uses deferred imports to survive collection
when symbols are missing).

Sample 5-line context (lines 605–613), `test_translate_delp_birds_fly_example`:
```python
    Parsing round-trip uses ``gunray.parser.parse_atom_text`` because
    the schema stores string surface syntax, not structured atoms
    (Diller, Borg, Bex 2025 §3).
    """

    from gunray.parser import parse_atom_text
    from gunray.types import Variable

    from propstore.aspic import GroundAtom
    from propstore.grounding.translator import translate_to_theory
```

Sample 5-line context (lines 567–574), `test_translate_empty_inputs_produces_empty_theory`:
```python
    the empty program has an empty Herbrand base; Garcia & Simari
    2004 §3 treats ``(∅, ∅, ∅)`` as a well-formed DeLP program.
    """

    from gunray import schema

    from propstore.grounding.translator import translate_to_theory

    theory = translate_to_theory([], (), _bird_registry())
```

**`C:\Users\Q\code\propstore\tests\test_grounding_grounder.py`** (1 import, deferred)

```
646:    from gunray.schema import Policy
```

5-line context (lines 643–651), inside `test_grounder_policy_is_configurable`:
```python
    supporting rule, so every atom is unambiguously proved in both
    regimes. This test therefore pins the narrower contract:
    calling with ``Policy.PROPAGATING`` returns a valid four-
    sectioned bundle that still preserves the canonical birds-fly
    derivation. A stronger differential test belongs to a later
    chunk once conflict pairs are translatable.
    """

    from gunray.schema import Policy

    from propstore.aspic import GroundAtom
    from propstore.grounding.grounder import ground
```

### 1C — Scripts

No matches in `C:\Users\Q\code\propstore\scripts\`. The only
`scripts/` files that touch gunray-adjacent work are the propstore
vocabulary reconciliation tools, none of which import gunray.

### 1D — Documentation / plans / logs (coder can ignore)

Historical only — included for completeness so the coder knows the
grep will surface noise:
```
C:\Users\Q\code\propstore\plans\defeasible-logic-integration-remediation-plan-2026-04-12.md:128
C:\Users\Q\code\propstore\plans\defeasible-logic-integration-remediation-plan-2026-04-12.md:142
C:\Users\Q\code\propstore\logs\grounder-tests-red-output.txt:300
C:\Users\Q\code\propstore\logs\test-runs\20260413-190247-full-suite-equation-cutover-rerun.txt:3260
C:\Users\Q\code\propstore\logs\test-runs\20260413-221649-full-suite-current-worktree-rerun.txt:2746
```

---

## Section 2 — Every consumer of `model.sections`

### 2A — Consumers of `bundle.sections` / `model.sections` (propstore source)

**`C:\Users\Q\code\propstore\propstore\grounding\grounder.py`** — the one call site that reads a raw `DefeasibleModel`:

Line 164, inside `ground()`:
```python
    evaluator = GunrayEvaluator()
    raw_model = cast(DefeasibleModel, evaluator.evaluate(theory, policy))

    # Step 3: re-normalise sections. Garcia & Simari 2004 §4 (p.25)
    # non-commitment anchor: every bundle must expose all four section
    # keys even when gunray dropped some for being empty. Diller, Borg,
    # Bex 2025 §3 Definition 9: the output must be a deterministic
    # function of the inputs, so we build the dict in the fixed
    # ``_FOUR_SECTIONS`` order.
    normalized_sections = _normalise_sections(raw_model.sections)
```

`_normalise_sections` (lines 176–226) iterates via `_FOUR_SECTIONS`:
```python
def _normalise_sections(
    raw_sections: DefeasibleSections,
) -> Mapping[str, Mapping[str, frozenset[tuple[Scalar, ...]]]]:
    ...
    normalized: dict[str, Mapping[str, frozenset[tuple[Scalar, ...]]]] = {}
    for name in _FOUR_SECTIONS:
        inner_raw = raw_sections.get(name, {})
        inner_frozen: dict[str, frozenset[tuple[Scalar, ...]]] = {}
        for predicate_id, rows in inner_raw.items():
            inner_frozen[predicate_id] = frozenset(rows)
        normalized[name] = MappingProxyType(inner_frozen)

    return MappingProxyType(normalized)
```

The string keys `_FOUR_SECTIONS` (lines 66–71):
```python
_FOUR_SECTIONS: tuple[str, ...] = (
    "definitely",
    "defeasibly",
    "not_defeasibly",
    "undecided",
)
```

**`C:\Users\Q\code\propstore\propstore\aspic_bridge.py`** — two `bundle.sections` reads, both inside `grounded_rules_to_rules` / `_ground_facts_to_axioms`.

Line 429, inside `grounded_rules_to_rules`:
```python
    facts: dict[_GroundFactKey, set[tuple[Scalar, ...]]] = {}
    for section_name in ("definitely", "defeasibly"):
        section = bundle.sections.get(section_name, {})
        for predicate_id, rows in section.items():
            bucket = facts.setdefault(_split_section_predicate(predicate_id), set())
            for row in rows:
                bucket.add(row)
```

Line 522, inside `_ground_facts_to_axioms`:
```python
    axioms: set[Literal] = set(kb.axioms)
    definitely = bundle.sections.get("definitely", {})
    for predicate_id, rows in definitely.items():
        predicate, negated = _split_section_predicate(predicate_id)
        for row in rows:
            ground = GroundAtom(predicate=predicate, arguments=tuple(row))
            lit = _literal_for_atom(ground, negated, literals)
            axioms.add(lit)
```

Note: the `"not_defeasibly"` and `"undecided"` sections are **not
read** by aspic_bridge — only `"definitely"` and `"defeasibly"` are
consumed today. The bundle still stores all four (the grounder's
normalization pass restores any dropped sections), but aspic_bridge
only cares about the two positive ones when injecting into KB / rule
stores.

**`C:\Users\Q\code\propstore\propstore\sidecar\rules.py`** — sections are read for SQLite persistence.

Line 183, inside `populate_grounded_facts`:
```python
    inserted = 0
    sections = bundle.sections
    for section_name in _SECTION_NAMES:
        inner_map = sections.get(section_name)
        if inner_map is None:
            continue
        for predicate_id in sorted(inner_map.keys()):
            rows = inner_map[predicate_id]
            if not rows:
                ...
                conn.execute(
                    "INSERT INTO grounded_fact_empty_predicate "
                    "(section, predicate) VALUES (?, ?)",
                    (section_name, predicate_id),
                )
                continue
            encoded = sorted(
                json.dumps(list(arg_tuple)) for arg_tuple in rows
            )
            for encoded_arguments in encoded:
                conn.execute(
                    "INSERT INTO grounded_fact "
                    "(predicate, arguments, section) VALUES (?, ?, ?)",
                    (predicate_id, encoded_arguments, section_name),
                )
                inserted += 1
    return inserted
```

The file-local constant `_SECTION_NAMES` (lines 72–77):
```python
_SECTION_NAMES: tuple[str, ...] = (
    "definitely",
    "defeasibly",
    "not_defeasibly",
    "undecided",
)
```

Predicate IDs are persisted raw — the sidecar store does **not**
strip the `~` prefix before writing. That means the `~`-strip hack
is an aspic_bridge-only concern; the sidecar intentionally preserves
whatever predicate tokens gunray hands back.

### 2B — Consumers inside tests

`bundle.sections[...]` access sites across propstore's test files:

```
tests/test_grounding_grounder.py:391  bundle.sections["definitely"] = {}  # type: ignore[index]  (mutation-rejection test)
tests/test_grounding_grounder.py:409  assert set(bundle.sections.keys()) == set(_FOUR_SECTIONS)
tests/test_grounding_grounder.py:433  rows = bundle.sections["definitely"].get(atom.predicate, frozenset())
tests/test_grounding_grounder.py:438  len(rows) for rows in bundle.sections["definitely"].values()
tests/test_grounding_grounder.py:511  assert set(bundle.sections.keys()) == set(_FOUR_SECTIONS)
tests/test_grounding_grounder.py:531  assert set(bundle.sections.keys()) == set(_FOUR_SECTIONS)
tests/test_grounding_grounder.py:533  section = bundle.sections[name]
tests/test_grounding_grounder.py:576  bird_rows = bundle.sections["definitely"].get("bird", frozenset())
tests/test_grounding_grounder.py:580  flies_rows = bundle.sections["defeasibly"].get("flies", frozenset())
tests/test_grounding_grounder.py:616  for row in bundle.sections["defeasibly"].get("flies", frozenset())
tests/test_grounding_grounder.py:666  for row in bundle_propagating.sections["defeasibly"].get("flies", frozenset())
tests/test_grounding_grounder.py:677  for row in bundle_default.sections["defeasibly"].get("flies", frozenset())
tests/test_grounding_grounder.py:719  assert set(bundle.sections.keys()) == set(_FOUR_SECTIONS)
tests/test_grounding_grounder.py:721  total = sum(len(rows) for rows in bundle.sections[name].values())

tests/test_gunray_integration.py:458  assert ("tweety",) in bundle.sections["definitely"].get("bird", frozenset())
tests/test_gunray_integration.py:461  assert ("tweety",) in bundle.sections["defeasibly"].get("flies", frozenset())
tests/test_gunray_integration.py:540  assert ("tweety",) in bundle.sections["definitely"].get("bird", frozenset())
tests/test_gunray_integration.py:545  assert bundle.sections["defeasibly"].get("flies", frozenset()) == frozenset()
tests/test_gunray_integration.py:627  flies_rows = bundle.sections["defeasibly"].get("flies", frozenset())
tests/test_gunray_integration.py:729  assert bundle.sections["defeasibly"].get("flies", frozenset()) == frozenset()

tests/test_sidecar_grounded_facts.py:217  (docstring) "Copy bundle.sections into a plain dict..."
tests/test_sidecar_grounded_facts.py:229  name: dict(inner.items()) for name, inner in bundle.sections.items()
tests/test_sidecar_grounded_facts.py:451  for section_map in bundle.sections.values()
tests/test_sidecar_grounded_facts.py:540  (docstring) "yields a section mapping equal to bundle.sections"
```

Also the translator tranche test (`test_defeasible_conformance_tranche.py`)
reads `.sections` off the raw `DefeasibleModel`, not off a bundle:

Lines 231–262:
```python
    if case.expect_per_policy is not None:
        for policy_name, expected in case.expect_per_policy.items():
            actual_model = _evaluate_translated_suite_theory(case, policy_name=policy_name)
            sections = getattr(actual_model, "sections", None)
            if not isinstance(sections, dict):
                raise AssertionError("Gunray evaluator did not return defeasible sections")
            for section_name, predicates in expected.items():
                assert section_name in sections
                for predicate, rows in predicates.items():
                    actual_rows = {
                        tuple(row) for row in sections[section_name].get(predicate, set())
                    }
                    assert actual_rows == set(rows)
        return

    actual_model = _evaluate_translated_suite_theory(case)
    expected = case.expect
    if expected is None:
        raise AssertionError("Translator tranche requires explicit expectations")

    sections = getattr(actual_model, "sections", None)
    if not isinstance(sections, dict):
        raise AssertionError("Gunray evaluator did not return defeasible sections")

    for section_name, predicates in expected.items():
        assert section_name in sections
        for predicate, rows in predicates.items():
            actual_rows = {
                tuple(row) for row in sections[section_name].get(predicate, set())
            }
            assert actual_rows == set(rows)
```

This test uses `getattr(model, "sections", None)` plus
`isinstance(sections, dict)` — so it reads sections *as a plain dict*
from a bare gunray `DefeasibleModel`, without going through any
propstore bundle. The B3.2 coder must not break this shape, or must
update the test to use the new argument-level API directly.

### 2C — DefeasibleModel constructors in propstore

No propstore code constructs `DefeasibleModel` directly. Verified:
nothing in propstore imports `DefeasibleModel` as a constructor,
only the one `cast(DefeasibleModel, ...)` on `grounder.py:156`.

---

## Section 3 — `_split_section_predicate` and its callers

### Function definition

`C:\Users\Q\code\propstore\propstore\aspic_bridge.py`, lines 198–214:

```python
# ── T2.5: grounded rules -> rules ────────────────────────────────

_GroundFactKey = tuple[str, bool]


def _split_section_predicate(predicate_id: str) -> _GroundFactKey:
    """Decode a bundle section key into ``(predicate, negated)``.

    Gunray serializes strong negation into the predicate token itself
    (for example ``"~fly"``). The ASPIC bridge models polarity on the
    ``Literal`` instead, so section rows must be normalized before they
    participate in grounding or KB injection.
    """

    if predicate_id.startswith("~"):
        return predicate_id.removeprefix("~"), True
    return predicate_id, False
```

Type alias on line 200:
```python
_GroundFactKey = tuple[str, bool]
```

### Caller #1 — `grounded_rules_to_rules` (line 431)

`C:\Users\Q\code\propstore\propstore\aspic_bridge.py`, lines 422–478 (the body of `grounded_rules_to_rules`):

```python
    # Build the positive fact base: union of definitely and defeasibly
    # sections. Diller, Borg, Bex 2025 §3 Def 7 (p.3) treats the fact
    # base as a flat finite set of ground atoms; the per-section split
    # is gunray's four-valued answer record, not a rule-level concern.
    facts: dict[_GroundFactKey, set[tuple[Scalar, ...]]] = {}
    for section_name in ("definitely", "defeasibly"):
        section = bundle.sections.get(section_name, {})
        for predicate_id, rows in section.items():
            bucket = facts.setdefault(_split_section_predicate(predicate_id), set())
            for row in rows:
                bucket.add(row)

    defeasible_rules: list[Rule] = []

    for rule_file in bundle.source_rules:
        for rule_doc in rule_file.document.rules:
            if rule_doc.kind == "strict":
                raise NotImplementedError(
                    "Strict rules deferred to Phase 4"
                )
            if rule_doc.kind == "defeater":
                raise NotImplementedError(
                    "Defeater rules deferred to Phase 4"
                )
            if rule_doc.negative_body:
                raise NotImplementedError(
                    "Negative body (NAF) deferred to Phase 4"
                )

            # rule_doc.kind == "defeasible" with empty negative_body.
            for sigma in _enumerate_substitutions(rule_doc.body, facts):
                antecedent_literals: list[Literal] = []
                for body_atom in rule_doc.body:
                    ground = _apply_substitution(body_atom, sigma)
                    antecedent_literals.append(
                        _literal_for_atom(ground, body_atom.negated, literals)
                    )

                head_ground = _apply_substitution(rule_doc.head, sigma)
                consequent = _literal_for_atom(
                    head_ground, rule_doc.head.negated, literals
                )

                sub_key = _canonical_substitution_key(sigma)
                rule_name = f"{rule_doc.id}#{sub_key}"

                defeasible_rules.append(
                    Rule(
                        antecedents=tuple(antecedent_literals),
                        consequent=consequent,
                        kind="defeasible",
                        name=rule_name,
                    )
                )

    return frozenset(), frozenset(defeasible_rules), literals
```

What this caller consumes: the `(stripped_predicate, negated)` tuple
is used as the **key** in a `dict[_GroundFactKey, set[tuple[Scalar, ...]]]`
fact base. The stripped predicate name is then matched against
`rule_doc.body[*].predicate` / `.negated` in
`_enumerate_substitutions(rule_doc.body, facts)` (line 453). The
polarity bit is threaded through the key so the body-match join
respects strong negation — i.e. `~bird(X)` in a rule body only
matches `~bird(tweety)` in the fact base, never `bird(tweety)`.

The return value polarity flag is **discarded** here because the
`negated` flag appears later via `body_atom.negated` /
`rule_doc.head.negated` when the literals are built. The sole
purpose of `_split_section_predicate` at this call site is **keying
the fact dictionary**.

### Caller #2 — `_ground_facts_to_axioms` (line 524)

`C:\Users\Q\code\propstore\propstore\aspic_bridge.py`, lines 519–530:

```python
    axioms: set[Literal] = set(kb.axioms)
    definitely = bundle.sections.get("definitely", {})
    for predicate_id, rows in definitely.items():
        predicate, negated = _split_section_predicate(predicate_id)
        for row in rows:
            ground = GroundAtom(predicate=predicate, arguments=tuple(row))
            lit = _literal_for_atom(ground, negated, literals)
            axioms.add(lit)

    return KnowledgeBase(axioms=frozenset(axioms), premises=kb.premises)
```

What this caller consumes: **both** the stripped predicate name
(fed into `GroundAtom(predicate=predicate, ...)`) **and** the
polarity flag (fed into `_literal_for_atom(ground, negated, ...)`).
`_literal_for_atom` uses the `negated` flag to construct a new
`Literal` with `negated=negated` so the KB receives strong-negated
facts in their structured form.

### Replacement hint for B3.2

The B3.2 coder will need to replace both call sites with code that
reads the conclusion polarity off an `Argument.conclusion` (or the
analogous field on whatever gunray exposes in the new
`arguments` field). The fact-keying at line 431 presumes a
predicate/polarity pair; the axiom-extraction at line 524 presumes
the same pair plus the argument tuple. There are no other callers
in propstore.

---

## Section 4 — `Policy.PROPAGATING` references that B2.3 will break

### Direct symbol references (will break at import/runtime if B2.3 deletes the attribute)

**Count of direct `Policy.PROPAGATING` symbol uses: 1 runtime call, 1 docstring mention, 1 unrelated docstring in prose.**

Verbatim grep output (pattern: `PROPAGATING`):
```
C:\Users\Q\code\propstore\tests\test_grounding_grounder.py:640
C:\Users\Q\code\propstore\tests\test_grounding_grounder.py:661
C:\Users\Q\code\propstore\propstore\grounding\grounder.py:131
```

#### 4A — `tests/test_grounding_grounder.py:661` (runtime call — WILL BREAK)

Full test `test_grounder_policy_is_configurable`, lines 622–682:

```python
def test_grounder_policy_is_configurable() -> None:
    """``ground(..., policy=...)`` threads the policy through to gunray.

    Garcia & Simari 2004 §4 (p.25) discusses ambiguity resolution —
    blocking versus propagating — in the four-valued answer system.
    Diller, Borg, Bex 2025 §3 invokes gunray's evaluator over the
    ground model, and gunray's ``GunrayEvaluator.evaluate`` accepts
    a ``Policy`` enum argument (``BLOCKING`` is the default). The
    grounder must accept a ``policy`` keyword and thread it through
    so callers can switch between ambiguity regimes.

    Phase 1 cannot construct a theory where the two policies
    actually diverge because the translator does not yet emit
    ``DefeasibleTheory.conflicts`` pairs (see chunk 1.4b report and
    translator docstring: strong negation / contrariness routing is
    deferred). Without a conflict pair nothing can oppose a
    supporting rule, so every atom is unambiguously proved in both
    regimes. This test therefore pins the narrower contract:
    calling with ``Policy.PROPAGATING`` returns a valid four-
    sectioned bundle that still preserves the canonical birds-fly
    derivation. A stronger differential test belongs to a later
    chunk once conflict pairs are translatable.
    """

    from gunray.schema import Policy

    from propstore.aspic import GroundAtom
    from propstore.grounding.grounder import ground

    rule = _build_rule_document(
        rule_id="birds_fly",
        kind="defeasible",
        head=_build_atom("flies", [_build_term_var("X")]),
        body=(_build_atom("bird", [_build_term_var("X")]),),
    )
    rule_file = _build_rule_file([rule])
    facts = (GroundAtom("bird", ("tweety",)),)

    bundle_propagating = ground(
        [rule_file], facts, _bird_registry(), policy=Policy.PROPAGATING
    )
    assert set(bundle_propagating.sections.keys()) == set(_FOUR_SECTIONS)
    flies_rows = {
        tuple(row)
        for row in bundle_propagating.sections["defeasibly"].get(
            "flies", frozenset()
        )
    }
    assert ("tweety",) in flies_rows

    # Default policy (BLOCKING) also works and both runs populate
    # the canonical defeasibly-provable row.
    bundle_default = ground([rule_file], facts, _bird_registry())
    default_flies_rows = {
        tuple(row)
        for row in bundle_default.sections["defeasibly"].get(
            "flies", frozenset()
        )
    }
    assert ("tweety",) in default_flies_rows
```

What it does: **smoke test asserting that `ground(..., policy=Policy.PROPAGATING)`
returns a four-section bundle whose `defeasibly.flies` row includes
`("tweety",)`.** B3.2 coder: replace the attribute with whatever
B2.3 recommends as the new spelling (likely
`Policy("propagating")` or a new enum member) and update the
docstring on line 640 in lockstep.

#### 4B — `tests/test_grounding_grounder.py:640` (docstring prose)

Already shown above inside the `test_grounder_policy_is_configurable`
docstring. It reads:
```
    calling with ``Policy.PROPAGATING`` returns a valid four-
```
Not a runtime reference; coder can update the triple-backticks when
fixing line 661.

#### 4C — `propstore/grounding/grounder.py:131` (docstring prose)

5-line context (lines 127–135):
```python
            ``GunrayEvaluator.evaluate``. Garcia & Simari 2004 §4
            (p.25) discusses blocking versus propagating ambiguity
            regimes. Defaults to ``Policy.BLOCKING`` to match gunray's
            own default. Phase 1 theories cannot diverge between
            ``BLOCKING`` and ``PROPAGATING`` because the translator
            does not yet emit conflict pairs, but the keyword is still
            threaded through so callers can opt into the richer
            regimes once Phase 2 lands.
```

Not a runtime reference — just prose naming the enum values. Coder
should realign the text with whatever terminology B2.3 settled on.

### Indirect references via string-to-enum construction (may break)

**`tests/test_defeasible_conformance_tranche.py:213`** — constructs
the enum **by string value**:

```python
def _evaluate_translated_suite_theory(case: SuiteCase, *, policy_name: str | None = None) -> object:
    from propstore.grounding.translator import translate_to_theory
    from gunray.schema import Policy

    assert case.theory is not None
    rule_file = _build_rule_file(case.theory)
    facts = _build_fact_atoms(case.theory)
    registry = _build_registry(case.theory)
    translated = translate_to_theory([rule_file], facts, registry)
    policy = None if policy_name is None else Policy(policy_name)
    return GunrayEvaluator().evaluate(translated, policy)
```

`policy_name` comes from `case.expect_per_policy.keys()` in the YAML
suite. Suite keys observed in the current test corpus include
`"blocking"` and `"propagating"`. If B2.3 removed only the `PROPAGATING`
attribute but left the `"propagating"` enum value in place, this code
path keeps working. If B2.3 removed the value too, the
`Policy("propagating")` call raises `ValueError` the first time a
parametrized case hits the propagating regime.

Additionally the file-level tranche ID list (lines 34–45) contains
`"antoniou_ambiguous_attacker_blocks_only_in_propagating"` as a test
case name — those are YAML identifiers, not Policy symbol uses, and
do not affect runtime.

### Summary for B3.2

- **Runtime breakages (guaranteed):** 1 — `tests/test_grounding_grounder.py:661`.
- **Runtime breakages (conditional):** 1 — `tests/test_defeasible_conformance_tranche.py:213` (breaks only if B2.3 removed the `"propagating"` enum value).
- **Docstring drift (cosmetic but should be fixed):** 2 — `tests/test_grounding_grounder.py:640`, `propstore/grounding/grounder.py:131`.
- No other `Policy.PROPAGATING` or `"propagating"` references exist
  in `propstore/` source, `propstore/scripts/`, or `propstore/tests/`
  outside of the files listed above.

---

## Section 5 — `GroundedRulesBundle` and the grounder package surface

### `GroundedRulesBundle` definition

`C:\Users\Q\code\propstore\propstore\grounding\bundle.py` — full verbatim content below (file is 124 lines):

```python
"""Immutable bundle wrapping the grounder pipeline output.

Chunk 1.5b (green) of the Phase-1 grounder workstream. The
``GroundedRulesBundle`` is the single frozen handoff object from
``propstore.grounding.grounder.ground`` to downstream consumers (the
T2.5 bridge, the render layer, sidecar persistence). It stores the
four gunray sections verbatim together with the ``rule_files`` and
``facts`` that produced them, so the full provenance chain stays
intact.

... [module docstring truncated — see original file for references]
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from propstore.aspic import GroundAtom, Scalar
from propstore.rule_documents import LoadedRuleFile


def _build_empty_sections() -> Mapping[str, Mapping[str, frozenset[tuple[Scalar, ...]]]]:
    """Return a read-only four-valued section map with every bucket empty.

    Garcia & Simari 2004 §4 (p.25): the four-valued answer system
    ``{YES, NO, UNDECIDED, UNKNOWN}`` has four always-present section
    names. The non-commitment discipline (project CLAUDE.md) requires
    that every bundle expose all four, even when vacuous. The zero
    element of the bundle monoid is therefore a bundle with all four
    sections present-and-empty, not a bundle with sections omitted.
    """

    return MappingProxyType(
        {
            "definitely": MappingProxyType({}),
            "defeasibly": MappingProxyType({}),
            "not_defeasibly": MappingProxyType({}),
            "undecided": MappingProxyType({}),
        }
    )


@dataclass(frozen=True)
class GroundedRulesBundle:
    """Immutable record of one grounding-pipeline invocation.

    Attributes:
        source_rules: The ``LoadedRuleFile`` envelopes that were fed to
            the grounder, stored verbatim as a tuple. ...
        source_facts: The ground-atom fact base that was fed to the
            grounder, stored verbatim. ...
        sections: The four gunray sections as an immutable
            mapping-of-mappings. Outer key: one of
            ``{"definitely", "defeasibly", "not_defeasibly",
            "undecided"}``. Inner key: predicate id. Inner value:
            ``frozenset`` of argument tuples. ...
    """

    source_rules: tuple[LoadedRuleFile, ...]
    source_facts: tuple[GroundAtom, ...]
    sections: Mapping[str, Mapping[str, frozenset[tuple[Scalar, ...]]]]

    @classmethod
    def empty(cls) -> "GroundedRulesBundle":
        """Return the zero-value bundle: no rules, no facts, all four sections empty.

        Used at call sites that do not exercise grounding (legacy
        claim-graph flows, wrapper delegations, tests that don't care
        about ground rules). This is **not** a compat shim — it is the
        identity element for rule-less argumentation and exists so
        every caller can continue to pass a concrete, typed bundle
        rather than an ``Optional``.
        ...
        """

        return cls(
            source_rules=(),
            source_facts=(),
            sections=_build_empty_sections(),
        )
```

Key properties for the B3.2 coder:

- `@dataclass(frozen=True)` — **frozen**, not slotted. `__setattr__`
  raises `FrozenInstanceError`.
- Three positional fields, in order: `source_rules`, `source_facts`,
  `sections`. Dataclass field order matters for positional args.
- All three fields are currently required. Adding a new optional
  field (`arguments: tuple[Argument, ...] = ()` or similar) must
  place the new field **after** the existing three (dataclass rule)
  and give it a default or `field(default_factory=tuple)` so every
  existing caller that does `GroundedRulesBundle(source_rules=...,
  source_facts=..., sections=...)` keeps working.
- The `empty()` classmethod returns a bundle built via
  `_build_empty_sections()` which returns a `MappingProxyType` over
  four `MappingProxyType({})` inner maps. If the coder adds an
  `arguments` field with a default of `()`, `empty()` does not need
  to change; if the default is `None` or absent, `empty()` must
  pass the empty value explicitly.
- The module has no `__slots__`, no `__post_init__`, no validation
  hooks. Nothing in `bundle.py` touches gunray.
- Only one helper function lives in `bundle.py`:
  `_build_empty_sections()`.

### `ground()` signature

`C:\Users\Q\code\propstore\propstore\grounding\grounder.py`, lines 74–173.

Signature (lines 74–80):
```python
def ground(
    rule_files: Sequence[LoadedRuleFile],
    facts: tuple[GroundAtom, ...],
    registry: PredicateRegistry,
    *,
    policy: Policy = Policy.BLOCKING,
) -> GroundedRulesBundle:
```

Return construction (lines 169–173):
```python
    return GroundedRulesBundle(
        source_rules=tuple(rule_files),
        source_facts=facts,
        sections=normalized_sections,
    )
```

Evaluator invocation (lines 155–156):
```python
    evaluator = GunrayEvaluator()
    raw_model = cast(DefeasibleModel, evaluator.evaluate(theory, policy))
```

The B3.2 coder can add a new keyword after `policy=` (e.g.
`return_arguments: bool = False`) and thread it through to wherever
gunray exposes the argument view. The keyword-only marker `*,` is
already in place so additions do not disturb positional calls.

Module-local helpers in `grounder.py` that the coder needs to know:

- `_FOUR_SECTIONS: tuple[str, ...]` (lines 66–71) — the canonical
  section-name tuple.
- `_normalise_sections(raw_sections: DefeasibleSections)` (lines
  176–226) — immutability normalization; the only thing that touches
  `raw_model.sections`.

`grounder.py` imports from gunray:
```python
from gunray.adapter import GunrayEvaluator
from gunray.schema import DefeasibleModel, DefeasibleSections, Policy
```

No other private helpers in `grounder.py`. The module has no
`__all__`. Nothing else in `propstore.grounding` re-exports
`GroundedRulesBundle` — consumers import it directly from
`propstore.grounding.bundle`.

### `propstore/grounding/__init__.py`

Full content:
```python
"""Grounding pipeline for the rule-based argumentation Datalog backend."""
```

No re-exports. Every import uses fully-qualified module paths like
`from propstore.grounding.grounder import ground` and
`from propstore.grounding.bundle import GroundedRulesBundle`.

---

## Section 6 — Test patterns and propstore venv

### 6A — Test invocation command

Propstore uses `uv run pytest` for all test invocations. There is a
PowerShell wrapper at
`C:\Users\Q\code\propstore\scripts\run_logged_pytest.ps1`:

```powershell
param(
    [string]$Label = "pytest",
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PytestArgs
)

$ErrorActionPreference = "Stop"

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logDir = "logs/test-runs"
$logPath = Join-Path $logDir "$Label-$timestamp.log"

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$uvArgs = @("run", "pytest", "-vv") + $PytestArgs
$quotedArgs = foreach ($arg in $uvArgs) {
    if ($arg -match '[\s"]') {
        '"' + ($arg -replace '"', '\"') + '"'
    }
    else {
        $arg
    }
}
$uvCommand = "uv " + ($quotedArgs -join " ")
cmd.exe /d /c "$uvCommand 2>&1" | Tee-Object -FilePath $logPath
$exitCode = $LASTEXITCODE

Write-Output "LOG_PATH=$logPath"
exit $exitCode
```

Direct invocation from `C:\Users\Q\code\propstore`:
```
uv run pytest tests -q
```
Or via the script (logs to `logs/test-runs/<label>-<ts>.log`):
```
pwsh scripts/run_logged_pytest.ps1 -Label b3 tests
```

### 6B — Pytest configuration

`C:\Users\Q\code\propstore\pyproject.toml`, lines 58–69:
```toml
[tool.pytest.ini_options]
# Hypothesis profiles: HYPOTHESIS_PROFILE=overnight for thorough runs (see tests/conftest.py)
timeout = 300
timeout_method = "thread"
markers = [
    "unit: focused unit-level contract tests",
    "property: property-based or metamorphic tests",
    "differential: differential or oracle-comparison tests",
    "e2e: minimally mocked end-to-end workflow tests",
    "migration: temporary migration or cutover protection tests",
    "slow: intentionally slow tests or suites",
]
```

Timeout is 300 seconds per test (`thread` method).

### 6C — Conftest and shared fixtures

`C:\Users\Q\code\propstore\tests\conftest.py` — file exists but
contains **no grounder, no bundle, no policy fixtures**. Its contents
are SQLite/claim-graph test helpers (`make_claim_identity`,
`attach_claim_version_id`, `make_concept_identity`,
`create_argumentation_schema`, `create_world_model_schema`,
`insert_claim`, `insert_stance`, `insert_conflict`,
`make_parameter_claim`, `make_concept_registry`) — none of which
touch grounding or gunray.

There is also no propstore-root `conftest.py`. Every grounder test
builds its bundles and rule documents **inline in test bodies**. From
`test_grounding_grounder.py` module docstring (lines 75–82):

```python
# ── Local builders (no conftest, no helpers outside this file) ──────
#
# Deferred imports: every helper imports propstore types inside its
# body so test collection succeeds even though
# ``propstore.grounding.grounder`` and ``propstore.grounding.bundle``
# do not exist yet. This mirrors the pattern from
# ``tests/test_grounding_translator.py`` — the prompt explicitly asks
# for inline duplication rather than shared fixtures.
```

`test_gunray_integration.py` module docstring (lines 13–19):
```python
Construction of every input is inline here (no shared fixtures, no
conftest.py, no helper modules — same constraint as
``tests/test_grounding_facts.py`` and
``tests/test_grounding_grounder.py``). Imports of propstore types are
deferred into test bodies so pytest collection does not depend on the
1.8b symbols existing.
```

So the B3.2 coder should follow the same pattern: build
`GroundedRulesBundle` instances inline, no new fixtures, deferred
imports inside test bodies if the target symbols do not yet exist.

### 6D — Tests that string-parse predicate names (would also need updating if the `~`-strip hack dies)

Grep pattern: `removeprefix\("~"\)|startswith\("~"\)`.

```
propstore/aspic_bridge.py:212  if predicate_id.startswith("~"):
propstore/aspic_bridge.py:213      return predicate_id.removeprefix("~"), True

tests/test_defeasible_conformance_tranche.py:103  negated = parsed.predicate.startswith("~")
tests/test_defeasible_conformance_tranche.py:104  predicate = parsed.predicate.removeprefix("~")
tests/test_defeasible_conformance_tranche.py:150      if predicate.startswith("~"):
tests/test_defeasible_conformance_tranche.py:171      if predicate.startswith("~"):
tests/test_defeasible_conformance_tranche.py:177      arities[head.predicate.removeprefix("~")] = head.arity
tests/test_defeasible_conformance_tranche.py:180          arities[body_atom.predicate.removeprefix("~")] = body_atom.arity
```

`test_defeasible_conformance_tranche.py` uses `~`-parsing for
**two independent purposes**:

1. **Converting gunray-parsed atom text back to an `AtomDocument`**
   in `_build_atom_document` (lines 99–109):

   ```python
   def _build_atom_document(atom_text: str):
       from propstore.rule_documents import AtomDocument

       parsed = parse_atom_text(atom_text)
       negated = parsed.predicate.startswith("~")
       predicate = parsed.predicate.removeprefix("~")
       return AtomDocument(
           predicate=predicate,
           terms=tuple(_build_term_document(term) for term in parsed.terms),
           negated=negated,
       )
   ```

   This runs because gunray's `parse_atom_text` still reports the
   `~` as part of `parsed.predicate`; if gunray's argument-level API
   removes that, the helper will silently miscount all atoms as
   unnegated. The B3.2 coder must verify whether gunray still surfaces
   `~`-prefixed predicates from `parse_atom_text`.

2. **Skipping negative-fact rows in the translator tranche**
   (lines 145–157 and 168–181):

   ```python
   def _build_fact_atoms(theory: SuiteTheory):
       from propstore.aspic import GroundAtom

       facts: list[GroundAtom] = []
       for predicate, rows in theory.facts.items():
           if predicate.startswith("~"):
               raise NotImplementedError(
                   "Translator tranche only covers suite cases whose facts stay within "
                   "the current positive-fact propstore surface"
               )
           for row in rows:
               facts.append(GroundAtom(predicate=predicate, arguments=tuple(row)))
       return tuple(facts)


   def _build_registry(theory: SuiteTheory):
       ...
       arities: dict[str, int] = {}
       for predicate, rows in theory.facts.items():
           if predicate.startswith("~"):
               continue
           row_list = list(rows)
           arities[predicate] = len(row_list[0]) if row_list else 0
       for rule in (*theory.strict_rules, *theory.defeasible_rules, *theory.defeaters):
           head = parse_atom_text(rule.head)
           arities[head.predicate.removeprefix("~")] = head.arity
           for atom_text in rule.body:
               body_atom = parse_atom_text(atom_text)
               arities[body_atom.predicate.removeprefix("~")] = body_atom.arity
   ```

The sidecar layer (`propstore/sidecar/rules.py`) does **not**
string-parse predicate names — it stores the token verbatim and
never strips `~`. The only production-code consumer of the `~`-strip
hack is `aspic_bridge.py` at lines 431 and 524.

### 6E — Gunray dependency wiring

`C:\Users\Q\code\propstore\pyproject.toml`, lines 6–21:
```toml
dependencies = [
    "click>=8.0",
    "linkml>=1.8",
    "msgspec>=0.19.0",
    "pyyaml>=6.0",
    "jsonschema>=4.0",
    "lark>=1.2.2",
    "sympy>=1.14.0",
    "z3-solver>=4.12",
    "graphviz>=0.20",
    "ast-equiv @ git+https://github.com/ctoth/ast-equiv",
    "bridgman @ git+https://github.com/ctoth/bridgman",
    "pint>=0.25.3",
    "dulwich>=1.1.0",
    "gunray @ git+https://github.com/ctoth/gunray",
]
```

And, critically:
```toml
[tool.hatch.metadata]
allow-direct-references = true
```

Propstore installs gunray from **GitHub** via a git URL, **not** from
the sibling working tree at `C:\Users\Q\code\gunray`. The installed
version is locked in `uv.lock`:

```
[[package]]
name = "gunray"
version = "0.1.0"
source = { git = "https://github.com/ctoth/gunray#5078df5ee65ae17ee2a614299ba395ed8a7664d9" }
```

Commit `5078df5` is gunray master HEAD as of this scout (matches
`git log` in gunray: `5078df5 fix(defeasible): classify partially
grounded heads`). The B3.2 coder must:

1. Push B2.3's gunray changes to `https://github.com/ctoth/gunray`
   master (or a branch).
2. Run `uv lock --upgrade-package gunray` in
   `C:\Users\Q\code\propstore` to refresh `uv.lock`.
3. Run `uv sync` to install the new revision into `.venv`.

**Exception:** `tests/test_defeasible_conformance_tranche.py` inserts
`C:\Users\Q\code\gunray\src` into `sys.path` at module-import time
(lines 13–19, shown in Section 1B). So that one test file **does**
load gunray from the local working tree. Every other test file loads
gunray through the installed package in `.venv`. The coder should
therefore expect two sets of imports to resolve differently during a
B3.2 test run and avoid cross-contaminating them.

### 6F — Pyright configuration

`pyproject.toml` lines 42–56:
```toml
[tool.pyright]
typeCheckingMode = "basic"
venvPath = "."
venv = ".venv"
strict = [
    "propstore/core/literal_keys.py",
    "propstore/core/labels.py",
    "propstore/core/graph_types.py",
    "propstore/core/results.py",
    "propstore/conflict_detector/models.py",
    "propstore/dung.py",
    "propstore/opinion.py",
    "propstore/aspic.py",
    "propstore/aspic_bridge.py",
]
```

`aspic_bridge.py` is in the **strict** list. Any edit to
`_split_section_predicate` (or its callers) must keep pyright-strict
clean. `grounder.py` and `bundle.py` are in the `basic` set.

Pyright reproduction rule (from B3.1 prompt): harness pyright
diagnostics must reproduce under `uv run pyright <file>` before any
cleanup. Project pyright (in `propstore/.venv`) is the source of
truth.

---

## Red-flag section — unexpected API surface

None found. Every gunray import in propstore goes through one of
these documented public modules:

- `gunray.schema` (types, `Policy`, `DefeasibleModel`, `DefeasibleSections`, `DefeasibleTheory`)
- `gunray.adapter` (`GunrayEvaluator`)
- `gunray.conformance_adapter` (`GunrayConformanceEvaluator`)
- `gunray.parser` (`parse_atom_text`)
- `gunray.types` (`Constant`, `Variable`)

No propstore code reaches into `gunray._private` modules, no
importlib tricks, no monkeypatches of gunray internals, no gunray
imports from test helper modules outside `tests/`. The `sys.path`
injection in `test_defeasible_conformance_tranche.py` is unusual but
it still only imports from documented gunray modules.

No deeply-internal gunray module is imported via a path hack. The
B3.2 coder can proceed from this report without further surface
discovery.
