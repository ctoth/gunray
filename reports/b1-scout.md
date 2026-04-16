# B1.1 — Consolidated scout report for Block 1

Read-only survey of `gunray` for the B1.2 through B1.6 coders. Every
snippet below is verbatim from the source tree at the commit of
dispatch. No paraphrase.

---

## Section 1 — Landing spots

### 1.1 Current dataclass conventions

Two conventions coexist:

- `src/gunray/types.py` uses `@dataclass(frozen=True, slots=True)`
  throughout (immutable, hashable).
- `src/gunray/schema.py` uses `@dataclass(slots=True)` without `frozen=`
  because its fields are mutable lists.

New paper types `Argument`, `DialecticalNode` should follow the
`types.py` frozen convention.

### 1.2 `src/gunray/types.py` (full, 103 lines)

```python
"""Internal immutable syntax and rule-model types for Gunray."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

Scalar: TypeAlias = str | int | float | bool
Binding: TypeAlias = dict[str, Scalar]


@dataclass(frozen=True, slots=True)
class Variable:
    name: str


@dataclass(frozen=True, slots=True)
class Wildcard:
    token: str


@dataclass(frozen=True, slots=True)
class Constant:
    value: Scalar


@dataclass(frozen=True, slots=True)
class AddExpression:
    left: "ValueTerm"
    right: "ValueTerm"


@dataclass(frozen=True, slots=True)
class SubtractExpression:
    left: "ValueTerm"
    right: "ValueTerm"


@dataclass(frozen=True, slots=True)
class Comparison:
    left: "ValueTerm"
    operator: str
    right: "ValueTerm"


PatternTerm: TypeAlias = Variable | Wildcard | Constant
ValueTerm: TypeAlias = Variable | Constant | AddExpression | SubtractExpression
AtomTerm: TypeAlias = PatternTerm | AddExpression | SubtractExpression


@dataclass(frozen=True, slots=True)
class Atom:
    predicate: str
    terms: tuple[AtomTerm, ...]

    @property
    def arity(self) -> int:
        return len(self.terms)


@dataclass(frozen=True, slots=True)
class Rule:
    heads: tuple[Atom, ...]
    positive_body: tuple[Atom, ...]
    negative_body: tuple[Atom, ...]
    constraints: tuple[Comparison, ...]
    source_text: str


@dataclass(frozen=True, slots=True)
class GroundAtom:
    predicate: str
    arguments: tuple[Scalar, ...]

    @property
    def arity(self) -> int:
        return len(self.arguments)


@dataclass(frozen=True, slots=True)
class DefeasibleRule:
    rule_id: str
    kind: str
    head: Atom
    body: tuple[Atom, ...]


@dataclass(frozen=True, slots=True)
class GroundDefeasibleRule:
    rule_id: str
    kind: str
    head: GroundAtom
    body: tuple[GroundAtom, ...]


def variables_in_term(term: AtomTerm) -> set[str]:
    """Return the bound variable names referenced by a term."""

    if isinstance(term, Variable):
        return {term.name}
    if isinstance(term, (AddExpression, SubtractExpression)):
        return variables_in_term(term.left) | variables_in_term(term.right)
    return set()
```

### 1.3 `src/gunray/schema.py` (full, 83 lines)

```python
"""Public Gunray-owned schema and model types."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import TypeAlias

Scalar: TypeAlias = str | int | float | bool
FactTuple: TypeAlias = tuple[Scalar, ...]
PredicateFacts: TypeAlias = Mapping[str, Iterable[FactTuple]]
ModelFacts: TypeAlias = Mapping[str, set[FactTuple]]
DefeasibleSections: TypeAlias = Mapping[str, ModelFacts]


def _predicate_facts_factory() -> PredicateFacts:
    return {}


def _string_list_factory() -> list[str]:
    return []


def _rule_list_factory() -> list["Rule"]:
    return []


def _pair_list_factory() -> list[tuple[str, str]]:
    return []


class Policy(str, Enum):
    """Named evaluation policies supported by Gunray."""

    BLOCKING = "blocking"
    PROPAGATING = "propagating"
    RATIONAL_CLOSURE = "rational_closure"
    LEXICOGRAPHIC_CLOSURE = "lexicographic_closure"
    RELEVANT_CLOSURE = "relevant_closure"


@dataclass(slots=True)
class Program:
    """Core Datalog program."""

    facts: PredicateFacts = field(default_factory=_predicate_facts_factory)
    rules: list[str] = field(default_factory=_string_list_factory)


@dataclass(slots=True)
class Rule:
    """Shared rule structure for strict, defeasible, and defeater rules."""

    id: str
    head: str
    body: list[str] = field(default_factory=_string_list_factory)


@dataclass(slots=True)
class DefeasibleTheory:
    """Defeasible Datalog theory."""

    facts: PredicateFacts = field(default_factory=_predicate_facts_factory)
    strict_rules: list[Rule] = field(default_factory=_rule_list_factory)
    defeasible_rules: list[Rule] = field(default_factory=_rule_list_factory)
    defeaters: list[Rule] = field(default_factory=_rule_list_factory)
    superiority: list[tuple[str, str]] = field(default_factory=_pair_list_factory)
    conflicts: list[tuple[str, str]] = field(default_factory=_pair_list_factory)


@dataclass(slots=True)
class Model:
    """Standard Datalog model returned by evaluators."""

    facts: ModelFacts


@dataclass(slots=True)
class DefeasibleModel:
    """Defeasible model returned by evaluators."""

    sections: DefeasibleSections
```

### 1.4 `src/gunray/__init__.py` (full, 30 lines)

```python
"""Public package surface for Gunray."""

from .adapter import GunrayEvaluator
from .defeasible import DefeasibleEvaluator
from .evaluator import SemiNaiveEvaluator
from .schema import DefeasibleModel, DefeasibleTheory, Model, Policy, Program, Rule
from .trace import (
    ClassificationTrace,
    DatalogTrace,
    DefeasibleTrace,
    ProofAttemptTrace,
    TraceConfig,
)

__all__ = [
    "ClassificationTrace",
    "DefeasibleModel",
    "DatalogTrace",
    "DefeasibleEvaluator",
    "DefeasibleTheory",
    "DefeasibleTrace",
    "GunrayEvaluator",
    "Model",
    "Policy",
    "ProofAttemptTrace",
    "Program",
    "Rule",
    "SemiNaiveEvaluator",
    "TraceConfig",
]
```

### 1.5 Landing directives for new modules

Place each new file alongside existing modules in `src/gunray/` and add
the re-export line to `src/gunray/__init__.py` immediately after
existing imports from the same subject area:

- `src/gunray/arguments.py` (new) — defines `Argument`. Import added
  to `__init__.py` beside `from .defeasible import DefeasibleEvaluator`.
- `src/gunray/answer.py` (new) — defines `Answer` enum. Import added
  next to `from .schema import ...`.
- `src/gunray/preference.py` (new) — defines `PreferenceCriterion`
  protocol and `TrivialPreference`. Import added next to
  `from .adapter import GunrayEvaluator`.
- `src/gunray/disagreement.py` (new) — defines `disagrees()`. Imported
  only from `arguments.py` and `dialectic.py`, does not need a
  package-level re-export unless the coder chooses to.
- `src/gunray/dialectic.py` (new) — defines `DialecticalNode`,
  `build_tree`, `counter_argues`, `proper_defeater`, `blocking_defeater`,
  `mark`, `render_tree`, `answer`. Add these to `__init__.py`.

No other modules import from these by name today (they do not exist),
so landing them is purely additive.

---

## Section 2 — Existing public contract (do not break)

### 2.1 `gunray.adapter.GunrayEvaluator.evaluate`

`src/gunray/adapter.py:30`:

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
        return self._suite_bridge().evaluate(item, policy)  # type: ignore[attr-defined]
```

**Refactor permission**: no, must not change through Block 2.

### 2.2 `gunray.schema.DefeasibleModel.sections`

`src/gunray/schema.py:79`:

```python
@dataclass(slots=True)
class DefeasibleModel:
    """Defeasible model returned by evaluators."""

    sections: DefeasibleSections
```

`DefeasibleSections = Mapping[str, ModelFacts]` and
`ModelFacts = Mapping[str, set[FactTuple]]` at `schema.py:13-14`. The
four contract section keys are `"definitely"`, `"defeasibly"`,
`"not_defeasibly"`, `"undecided"`. Existing construction in
`src/gunray/defeasible.py:228-236`:

```python
        sections = {
            "definitely": _atoms_to_section(definitely),
            "defeasibly": _atoms_to_section(proven),
            "not_defeasibly": _atoms_to_section(not_defeasibly),
            "undecided": _atoms_to_section(undecided),
        }
        return DefeasibleModel(
            sections={name: facts_map for name, facts_map in sections.items() if facts_map}
        ), trace
```

**Refactor permission**: no (Block 3 may revisit polarity handling, but
not Block 1).

### 2.3 `gunray.schema.Policy` enum values

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

**Refactor permission**: no.

### 2.4 `gunray.schema.DefeasibleTheory` constructor shape

`src/gunray/schema.py:60-69`:

```python
@dataclass(slots=True)
class DefeasibleTheory:
    """Defeasible Datalog theory."""

    facts: PredicateFacts = field(default_factory=_predicate_facts_factory)
    strict_rules: list[Rule] = field(default_factory=_rule_list_factory)
    defeasible_rules: list[Rule] = field(default_factory=_rule_list_factory)
    defeaters: list[Rule] = field(default_factory=_rule_list_factory)
    superiority: list[tuple[str, str]] = field(default_factory=_pair_list_factory)
    conflicts: list[tuple[str, str]] = field(default_factory=_pair_list_factory)
```

**Refactor permission**: no.

### 2.5 `gunray.schema.Rule`

`src/gunray/schema.py:51-57`:

```python
@dataclass(slots=True)
class Rule:
    """Shared rule structure for strict, defeasible, and defeater rules."""

    id: str
    head: str
    body: list[str] = field(default_factory=_string_list_factory)
```

**Refactor permission**: no.

### 2.6 `gunray.schema.Program`

`src/gunray/schema.py:43-48`:

```python
@dataclass(slots=True)
class Program:
    """Core Datalog program."""

    facts: PredicateFacts = field(default_factory=_predicate_facts_factory)
    rules: list[str] = field(default_factory=_string_list_factory)
```

**Refactor permission**: no.

### 2.7 `gunray.parser.parse_atom_text`

`src/gunray/parser.py:121`:

```python
def parse_atom_text(text: str) -> Atom:
    """Parse an atom like `p(X, Y)` or `~q`."""
```

Returns `Atom` from `types.py`. **Refactor permission**: no.

### 2.8 `gunray.types.Constant`, `Variable`, `GroundAtom`

See Section 1.2 for the verbatim definitions at `types.py:12`, `23`,
and `70`. **Refactor permission**: no.

### 2.9 `gunray.trace` re-exports

`src/gunray/trace.py` definitions (verbatim heads):

```python
@dataclass(frozen=True, slots=True)
class TraceConfig:
    capture_derived_rows: bool = False
    max_derived_rows_per_rule_fire: int = 10
```

```python
@dataclass(slots=True)
class DatalogTrace:
    config: TraceConfig = field(default_factory=TraceConfig)
    strata: list[StratumTrace] = field(default_factory=_stratum_trace_list_factory)
```

```python
@dataclass(slots=True)
class ProofAttemptTrace:
    atom: GroundAtom
    result: str
    reason: str
    supporter_rule_ids: tuple[str, ...] = ()
    attacker_rule_ids: tuple[str, ...] = ()
    opposing_atoms: tuple[GroundAtom, ...] = ()
```

```python
@dataclass(slots=True)
class ClassificationTrace:
    atom: GroundAtom
    result: str
    reason: str
    supporter_rule_ids: tuple[str, ...] = ()
    attacker_rule_ids: tuple[str, ...] = ()
    opposing_atoms: tuple[GroundAtom, ...] = ()
```

```python
@dataclass(slots=True)
class DefeasibleTrace:
    config: TraceConfig = field(default_factory=TraceConfig)
    definitely: tuple[GroundAtom, ...] = ()
    supported: tuple[GroundAtom, ...] = ()
    strict_trace: DatalogTrace | None = None
    proof_attempts: list[ProofAttemptTrace] = field(
        default_factory=_proof_attempt_trace_list_factory
    )
    classifications: list[ClassificationTrace] = field(
        default_factory=_classification_trace_list_factory
    )
```

**Refactor permission**: no. New evaluator code must continue to
populate `DefeasibleTrace.definitely` / `.supported` / `.proof_attempts`
/ `.classifications` with the same field names.

### 2.10 `src/gunray/conformance_adapter.py` (full, 141 lines)

```python
"""Optional bridge from datalog-conformance-suite inputs to Gunray."""
# pyright: reportMissingTypeStubs=false, reportUnknownVariableType=false

from __future__ import annotations

from typing import Any, cast

from .adapter import GunrayEvaluator
from .schema import DefeasibleTheory, Policy, Program, Rule
from .trace import TraceConfig

_suite_import_error: ImportError | None = None
SuiteDefeasibleTheory: type[Any] | None = None
SuitePolicy: type[Any] | None = None
SuiteProgram: type[Any] | None = None

try:
    from datalog_conformance.schema import DefeasibleTheory as _SuiteDefeasibleTheory
    from datalog_conformance.schema import Policy as _SuitePolicy
    from datalog_conformance.schema import Program as _SuiteProgram

    SuiteDefeasibleTheory = cast(type[Any], _SuiteDefeasibleTheory)
    SuitePolicy = cast(type[Any], _SuitePolicy)
    SuiteProgram = cast(type[Any], _SuiteProgram)
except ImportError as exc:  # pragma: no cover - exercised only without the optional extra
    _suite_import_error = exc


def _require_suite_support() -> None:
    if _suite_import_error is not None:
        raise ModuleNotFoundError(
            "gunray.conformance_adapter requires the datalog-conformance "
            "dependency. Install the dev extra."
        ) from _suite_import_error


def _copy_facts(raw_facts: dict[str, Any]) -> dict[str, list[tuple[Any, ...]]]:
    return {
        predicate: [tuple(row) for row in rows]
        for predicate, rows in raw_facts.items()
    }


def _translate_rule(rule: Any) -> Rule:
    return Rule(id=rule.id, head=rule.head, body=list(rule.body))


def _translate_program(program: Any) -> Program:
    return Program(
        facts=_copy_facts(program.facts),
        rules=list(program.rules),
    )


def _translate_theory(theory: Any) -> DefeasibleTheory:
    return DefeasibleTheory(
        facts=_copy_facts(theory.facts),
        strict_rules=[_translate_rule(rule) for rule in theory.strict_rules],
        defeasible_rules=[_translate_rule(rule) for rule in theory.defeasible_rules],
        defeaters=[_translate_rule(rule) for rule in theory.defeaters],
        superiority=list(theory.superiority),
        conflicts=list(theory.conflicts),
    )


def _translate_policy(policy: Policy | Any | None) -> Policy | None:
    if policy is None:
        return None
    if isinstance(policy, Policy):
        return policy
    _require_suite_support()
    assert SuitePolicy is not None
    if isinstance(policy, SuitePolicy):
        return Policy(policy.value)
    raise TypeError(f"Unsupported policy type: {type(policy).__name__}")


class GunrayConformanceEvaluator:
    """Bridge evaluator for datalog-conformance-suite runner inputs."""

    def __init__(self) -> None:
        self._core = GunrayEvaluator()

    def evaluate(
        self,
        item: Program | DefeasibleTheory | Any,
        policy: Policy | Any | None = None,
    ) -> object:
        if isinstance(item, Program | DefeasibleTheory):
            return self._core.evaluate(item, _translate_policy(policy))

        _require_suite_support()
        assert SuiteProgram is not None
        assert SuiteDefeasibleTheory is not None
        if isinstance(item, SuiteProgram):
            return self._core.evaluate(_translate_program(item))
        if isinstance(item, SuiteDefeasibleTheory):
            return self._core.evaluate(_translate_theory(item), _translate_policy(policy))
        raise TypeError(f"Unsupported input type: {type(item).__name__}")

    def evaluate_with_trace(
        self,
        item: Program | DefeasibleTheory | Any,
        policy: Policy | Any | None = None,
        trace_config: TraceConfig | None = None,
    ) -> tuple[object, object]:
        if isinstance(item, Program | DefeasibleTheory):
            return self._core.evaluate_with_trace(item, _translate_policy(policy), trace_config)

        _require_suite_support()
        assert SuiteProgram is not None
        assert SuiteDefeasibleTheory is not None
        if isinstance(item, SuiteProgram):
            return self._core.evaluate_with_trace(_translate_program(item), None, trace_config)
        if isinstance(item, SuiteDefeasibleTheory):
            return self._core.evaluate_with_trace(
                _translate_theory(item),
                _translate_policy(policy),
                trace_config,
            )
        raise TypeError(f"Unsupported input type: {type(item).__name__}")

    def satisfies_klm_property(
        self,
        theory: DefeasibleTheory | Any,
        property_name: str,
        policy: Policy | Any,
    ) -> bool:
        if isinstance(theory, DefeasibleTheory):
            return self._core.satisfies_klm_property(
                theory,
                property_name,
                _translate_policy(policy) or Policy.BLOCKING,
            )

        _require_suite_support()
        return self._core.satisfies_klm_property(
            _translate_theory(theory),
            property_name,
            _translate_policy(policy) or Policy.BLOCKING,
        )
```

Note the P0.1.5 wiring at `adapter.py:21-28`:

```python
    def _suite_bridge(self) -> object:
        if self._bridge is None:
            from .conformance_adapter import GunrayConformanceEvaluator

            bridge = GunrayConformanceEvaluator()
            bridge._core = self  # reuse this evaluator's engines
            self._bridge = bridge
        return self._bridge
```

The B1.6 evaluator-wiring coder must not break this round-trip: the
conformance adapter's `_core` is reassigned to the outer
`GunrayEvaluator` instance, so any method B1.6 adds to
`GunrayEvaluator` remains reachable through the bridge.

---

## Section 3 — `closure.py` strict-closure API (what B1.3 can reuse)

### 3.1 Key finding: propositional only

`src/gunray/closure.py:141-143`:

```python
def _ensure_zero_arity_literal(text: str) -> None:
    if "(" in text or ")" in text:
        raise ValueError(f"Closure evaluator expects zero-arity literals, got {text!r}")
```

`closure.py` is locked to the propositional zero-arity fragment at
multiple entry points. Its strict closure helper operates on
`set[str]` literal names, NOT on `GroundAtom`.

### 3.2 `_strict_closure` verbatim

`src/gunray/closure.py:198-209`:

```python
def _strict_closure(facts: set[str], strict_rules: list[Rule]) -> set[str]:
    closure = set(facts)
    changed = True
    while changed:
        changed = False
        for rule in strict_rules:
            if rule.head in closure:
                continue
            if set(rule.body) <= closure:
                closure.add(rule.head)
                changed = True
    return closure
```

Signature: `(facts: set[str], strict_rules: list[schema.Rule]) -> set[str]`.
This takes propositional literal strings (e.g. `"a"`, `"~b"`) and the
`schema.Rule` dataclass (head/body as strings). It is a module-level
function — NOT inside `ClosureEvaluator`.

### 3.3 Complement helpers

`src/gunray/closure.py:692-699`:

```python
def _positive_atom(literal: str) -> str:
    return literal[1:] if literal.startswith("~") else literal


def _complement(literal: str) -> str:
    if literal.startswith("~"):
        return literal[1:]
    return f"~{literal}"
```

`src/gunray/parser.py:281-286`:

```python
def _complement(predicate: str) -> str | None:
    if predicate.startswith("~"):
        return predicate[1:]
    if predicate:
        return f"~{predicate}"
    return None
```

### 3.4 The ground-atom strict closure (scheduled for deletion)

`src/gunray/defeasible.py:647-665` — this is the existing
implementation that DOES operate on ground atoms. Its body must
survive in the B1.3 coder's new `disagrees` implementation:

```python
def _strict_body_closure(
    seeds: frozenset[GroundAtom],
    grounded_strict_rules: tuple[GroundDefeasibleRule, ...],
    cache: dict[frozenset[GroundAtom], set[GroundAtom]],
) -> set[GroundAtom]:
    cached = cache.get(seeds)
    if cached is not None:
        return cached

    closure = set(seeds)
    changed = True
    while changed:
        changed = False
        for rule in grounded_strict_rules:
            if set(rule.body) <= closure and rule.head not in closure:
                closure.add(rule.head)
                changed = True
    cache[seeds] = closure
    return closure
```

### 3.5 Flag to B1.3 coder

`closure.py._strict_closure` **cannot be called cleanly from the new
`disagrees(h1, h2, K)` because its signature is `set[str]` propositional
literals, not `set[GroundAtom]`**. The B1.3 coder should write a new
`strict_closure(seeds: frozenset[GroundAtom], strict_rules:
tuple[GroundDefeasibleRule, ...]) -> set[GroundAtom]` helper — place
it in the new `src/gunray/disagreement.py` module. The `_strict_body_closure`
body above is the reference implementation. Do not try to share code
with `closure.py`; the two live in different type universes.

---

## Section 4 — Grounding internals that `build_arguments` reuses

### 4.1 `parse_defeasible_theory`

`src/gunray/parser.py:53-69`:

```python
def parse_defeasible_theory(
    theory: SchemaDefeasibleTheory,
) -> tuple[dict[str, set[tuple[Scalar, ...]]], list[DefeasibleRule], set[tuple[str, str]]]:
    """Parse a Gunray defeasible theory."""

    facts = normalize_facts(theory.facts)
    rules: list[DefeasibleRule] = []

    for item in theory.strict_rules:
        rules.append(parse_defeasible_rule(item, kind="strict"))
    for item in theory.defeasible_rules:
        rules.append(parse_defeasible_rule(item, kind="defeasible"))
    for item in theory.defeaters:
        rules.append(parse_defeasible_rule(item, kind="defeater"))

    conflicts = _collect_conflicts(theory)
    return facts, rules, conflicts
```

Returns a 3-tuple: `(facts dict[str, set[FactTuple]], list[DefeasibleRule],
conflicts set[tuple[str, str]])`. The returned rules have `kind` in
`{"strict", "defeasible", "defeater"}`.

### 4.2 `parse_defeasible_rule`

`src/gunray/parser.py:72-80`:

```python
def parse_defeasible_rule(rule: SchemaRule, *, kind: str) -> DefeasibleRule:
    """Parse a structured defeasible rule entry."""

    return DefeasibleRule(
        rule_id=rule.id,
        kind=kind,
        head=parse_atom_text(rule.head),
        body=tuple(parse_atom_text(item) for item in rule.body),
    )
```

### 4.3 `parse_atom_text`

`src/gunray/parser.py:121-146`:

```python
def parse_atom_text(text: str) -> Atom:
    """Parse an atom like `p(X, Y)` or `~q`."""

    stripped = text.strip()
    if not stripped:
        raise ParseError("Empty atom")

    bounds = _find_atom_argument_bounds(stripped)
    if bounds is None:
        return Atom(predicate=stripped, terms=())

    open_index, close_index = bounds
    if open_index <= 0 or close_index < open_index:
        raise ParseError(f"Unsupported atom syntax: {text}")

    predicate = stripped[:open_index].strip()
    inner = stripped[open_index + 1 : close_index].strip()
    if not predicate:
        raise ParseError(f"Missing predicate name: {text}")
    if not inner:
        return Atom(predicate=predicate, terms=())

    return Atom(
        predicate=predicate,
        terms=tuple(parse_term_text(item) for item in split_top_level(inner)),
    )
```

Strong negation is encoded as a `~` prefix on the **predicate** name:
e.g. `~flies(X)` parses to an `Atom` whose `.predicate == "~flies"` and
whose `.terms` contain the `X` variable. See also the `_complement`
helper at `parser.py:281-286` which adds/removes the `~` prefix at the
predicate level.

### 4.4 `ground_atom`

`src/gunray/parser.py:232-238`:

```python
def ground_atom(atom: Atom, binding: Mapping[str, object]) -> GroundAtom:
    """Instantiate a parsed atom under a binding."""

    return GroundAtom(
        predicate=atom.predicate,
        arguments=tuple(evaluate_term(term, binding) for term in atom.terms),
    )
```

`evaluate_term` at `parser.py:241-255` handles `Constant`, `Variable`,
`Wildcard` (raises on wildcards), and the arithmetic `Add`/`Subtract`
cases.

### 4.5 Strong-negation convention (verbatim from `_collect_conflicts`)

`src/gunray/parser.py:258-286`:

```python
def _collect_conflicts(theory: SchemaDefeasibleTheory) -> set[tuple[str, str]]:
    conflicts: set[tuple[str, str]] = set()
    for left, right in theory.conflicts:
        conflicts.add((left, right))
        conflicts.add((right, left))

    predicates = set(theory.facts)
    for rule in theory.strict_rules:
        predicates.add(parse_atom_text(rule.head).predicate)
    for rule in theory.defeasible_rules:
        predicates.add(parse_atom_text(rule.head).predicate)
    for rule in theory.defeaters:
        predicates.add(parse_atom_text(rule.head).predicate)

    for predicate in predicates:
        complement = _complement(predicate)
        if complement is not None:
            conflicts.add((predicate, complement))
            conflicts.add((complement, predicate))

    return conflicts


def _complement(predicate: str) -> str | None:
    if predicate.startswith("~"):
        return predicate[1:]
    if predicate:
        return f"~{predicate}"
    return None
```

### 4.6 `_positive_closure` (scheduled for deletion)

`src/gunray/defeasible.py:272-290`:

```python
def _positive_closure(
    facts: dict[str, set[FactTuple]],
    rules: list[DefeasibleRule],
) -> dict[str, IndexedRelation]:
    model = {
        predicate: IndexedRelation(rows)
        for predicate, rows in facts.items()
    }
    while True:
        changed = False
        for rule in rules:
            bindings = _match_positive_body(rule.body, model)
            for binding in bindings:
                grounded = ground_atom(rule.head, binding)
                bucket = model.setdefault(grounded.predicate, IndexedRelation())
                if bucket.add(grounded.arguments):
                    changed = True
        if not changed:
            return model
```

Uses `_match_positive_body` from `src/gunray/evaluator.py` (imported
at `defeasible.py:25`: `from .evaluator import SemiNaiveEvaluator,
_match_positive_body`) and `IndexedRelation` from
`src/gunray/relation.py`.

### 4.7 `_ground_rules` (scheduled for deletion)

`src/gunray/defeasible.py:293-325`:

```python
def _ground_rules(
    rules: list[DefeasibleRule],
    support_model: dict[str, IndexedRelation],
) -> tuple[list[GroundDefeasibleRule], set[GroundAtom]]:
    grounded: list[GroundDefeasibleRule] = []
    unsupported_heads: set[GroundAtom] = set()
    constants = _constant_universe(support_model)

    for rule in rules:
        bindings = _match_positive_body(rule.body, support_model)
        grounded_heads_for_rule: set[GroundAtom] = set()
        if not bindings:
            if not _rule_variables(rule):
                grounded_head = ground_atom(rule.head, {})
                unsupported_heads.add(grounded_head)
                grounded_heads_for_rule.add(grounded_head)
        for binding in bindings:
            grounded_head = ground_atom(rule.head, binding)
            grounded_heads_for_rule.add(grounded_head)
            grounded.append(
                GroundDefeasibleRule(
                    rule_id=rule.rule_id,
                    kind=rule.kind,
                    head=grounded_head,
                    body=tuple(ground_atom(atom, binding) for atom in rule.body),
                )
            )
        for binding in _candidate_head_bindings(rule, support_model, constants):
            grounded_head = ground_atom(rule.head, binding)
            if grounded_head not in grounded_heads_for_rule:
                unsupported_heads.add(grounded_head)

    return grounded, unsupported_heads
```

Supporting helpers `_constant_universe` and `_candidate_head_bindings`
at `defeasible.py:328-365`:

```python
def _constant_universe(support_model: dict[str, IndexedRelation]) -> tuple[object, ...]:
    constants = {
        value
        for relation in support_model.values()
        for row in relation
        for value in row
    }
    return tuple(sorted(constants, key=repr))


def _candidate_head_bindings(
    rule: DefeasibleRule,
    support_model: dict[str, IndexedRelation],
    constants: tuple[object, ...],
) -> list[dict[str, object]]:
    variables = sorted(_rule_variables(rule))
    if not variables:
        return [{}]

    available_body = [atom for atom in rule.body if atom.predicate in support_model]
    partial_bindings = _match_positive_body(available_body, support_model) if available_body else [{}]
    if not constants:
        return [binding for binding in partial_bindings if set(variables) <= set(binding)]

    candidate_bindings: list[dict[str, object]] = []
    seen: set[tuple[tuple[str, object], ...]] = set()
    for partial in partial_bindings:
        missing = [name for name in variables if name not in partial]
        for values in product(constants, repeat=len(missing)):
            binding = dict(partial)
            for name, value in zip(missing, values, strict=True):
                binding[name] = value
            key = tuple(sorted(binding.items()))
            if key in seen:
                continue
            seen.add(key)
            candidate_bindings.append(binding)
    return candidate_bindings
```

### 4.8 `GroundDefeasibleRule` (the existing ground-rule type)

`src/gunray/types.py:88-93`:

```python
@dataclass(frozen=True, slots=True)
class GroundDefeasibleRule:
    rule_id: str
    kind: str
    head: GroundAtom
    body: tuple[GroundAtom, ...]
```

`Argument.rules` in B1.2 should hold a `frozenset[GroundDefeasibleRule]`.
The fields are `rule_id: str`, `kind: str` (one of
`"strict" | "defeasible" | "defeater"`), `head: GroundAtom`, and
`body: tuple[GroundAtom, ...]`.

### 4.9 `_rule_variables` helper

`src/gunray/defeasible.py:575-582`:

```python
def _rule_variables(rule: DefeasibleRule) -> set[str]:
    variables: set[str] = set()
    for term in rule.head.terms:
        variables |= variables_in_term(term)
    for atom in rule.body:
        for term in atom.terms:
            variables |= variables_in_term(term)
    return variables
```

---

## Section 5 — Canonical paper examples (verbatim)

### 5.1 Tweety (README.md:8-23, Garcia & Simari 2004 §3)

Verbatim from `README.md:8-23`:

```python
from gunray import DefeasibleTheory, GunrayEvaluator, Policy, Rule

theory = DefeasibleTheory(
    facts={"bird": {("tweety",), ("opus",)}, "penguin": {("opus",)}},
    strict_rules=[Rule(id="s1", head="bird(X)", body=["penguin(X)"])],
    defeasible_rules=[
        Rule(id="r1", head="flies(X)",  body=["bird(X)"]),
        Rule(id="r2", head="~flies(X)", body=["penguin(X)"]),
    ],
    defeaters=[], superiority=[], conflicts=[],
)

model = GunrayEvaluator().evaluate(theory, Policy.BLOCKING)
# model.sections["defeasibly"] contains flies(tweety) and ~flies(opus).
```

Expected under B1 with `TrivialPreference`:

- `answer(theory, flies(tweety)) == YES` — Tweety is a bird, flies
  defeasibly, no opposing argument.
- `answer(theory, flies(opus))` — this is the classical specificity case.
  Under `TrivialPreference` (no preference) and **blocking** semantics
  the existing evaluator currently returns `flies(opus)` as
  `not_defeasibly` (see the `depysible_flies_tweety` expectation
  analogue in Section 5.5). With `TrivialPreference`, the competing
  arguments `{r1 via bird(opus)}` and `{r2 via penguin(opus)}` are
  peers. Under the paper's Def 5.3 that makes `flies(opus) ==
  UNDECIDED`. Block 2's `GeneralizedSpecificity` will change this to
  `NO`.
- `answer(theory, ~flies(opus))` — same, `UNDECIDED` under
  `TrivialPreference`.

**Note for B1.6 wiring coder**: the README narrative (`model.sections
["defeasibly"] contains flies(tweety) and ~flies(opus)`) is a Block-2
target, not a Block-1 target. Block 1 must document the expected
drift.

### 5.2 Nixon Diamond (Goldszmidt 1992 Example 1 / Simari 1992 §5 p.30)

From
`.venv/Lib/site-packages/datalog_conformance/_tests/defeasible/basic/goldszmidt_example1_nixon.yaml:89-115`
(the `goldszmidt_example1_pacifist_conflict` case):

```yaml
- name: goldszmidt_example1_pacifist_conflict
  description: >
    Adapted from Goldszmidt and Pearl 1992 Example 1 as recorded in local notes. The pacifist
    query is unresolved in the supported blocking implementation because the opposing defaults
    remain in conflict.
  tags: [nixon, pacifist, conflict]
  theory:
    facts:
      nixonian: [[nixon]]
      quaker: [[nixon]]
    strict_rules: []
    defeasible_rules:
      - id: r1
        head: "republican(X)"
        body: ["nixonian(X)"]
      - id: r2
        head: "pacifist(X)"
        body: ["quaker(X)"]
      - id: r3
        head: "~pacifist(X)"
        body: ["republican(X)"]
    defeaters: []
    superiority: []
  expect:
    undecided:
      pacifist: [[nixon]]
      "~pacifist": [[nixon]]
```

Python literal equivalent:

```python
from gunray import DefeasibleTheory, Rule

nixon_theory = DefeasibleTheory(
    facts={"nixonian": [("nixon",)], "quaker": [("nixon",)]},
    strict_rules=[],
    defeasible_rules=[
        Rule(id="r1", head="republican(X)", body=["nixonian(X)"]),
        Rule(id="r2", head="pacifist(X)",   body=["quaker(X)"]),
        Rule(id="r3", head="~pacifist(X)",  body=["republican(X)"]),
    ],
    defeaters=[], superiority=[], conflicts=[],
)
# Expected answer(nixon_theory, pacifist(nixon)) == UNDECIDED
# Expected answer(nixon_theory, ~pacifist(nixon)) == UNDECIDED
```

The prompt's simpler Nixon form (without the `nixonian` indirection) is
also a valid test:

```python
direct_nixon_theory = DefeasibleTheory(
    facts={"republican": [("nixon",)], "quaker": [("nixon",)]},
    strict_rules=[],
    defeasible_rules=[
        Rule(id="r1", head="~pacifist(X)", body=["republican(X)"]),
        Rule(id="r2", head="pacifist(X)",  body=["quaker(X)"]),
    ],
    defeaters=[], superiority=[], conflicts=[],
)
# Expected answer(direct_nixon_theory, pacifist(nixon)) == UNDECIDED
```

### 5.3 Opus / Penguin (Simari 1992 §5 p.29)

Same shape as Tweety in Section 5.1. Under `TrivialPreference` the
Opus query yields `UNDECIDED` because the two arguments — `flies(opus)
via r1 from bird(opus)` and `~flies(opus) via r2 from penguin(opus)` —
are peers with no ordering. Under Block 2's `GeneralizedSpecificity`
the `r2` argument uses a strictly more-specific activation
(`penguin(opus)` strictly entails `bird(opus)` via `s1`) and wins,
giving `flies(opus) == NO` and `~flies(opus) == YES`.

Python literal (subset of Section 5.1):

```python
opus_theory = DefeasibleTheory(
    facts={"bird": [("opus",)], "penguin": [("opus",)]},
    strict_rules=[Rule(id="s1", head="bird(X)", body=["penguin(X)"])],
    defeasible_rules=[
        Rule(id="r1", head="flies(X)",  body=["bird(X)"]),
        Rule(id="r2", head="~flies(X)", body=["penguin(X)"]),
    ],
    defeaters=[], superiority=[], conflicts=[],
)
# Block 1 with TrivialPreference:
#   answer(opus_theory, flies(opus))  == UNDECIDED
#   answer(opus_theory, ~flies(opus)) == UNDECIDED
# Block 2 with GeneralizedSpecificity:
#   answer(opus_theory, flies(opus))  == NO
#   answer(opus_theory, ~flies(opus)) == YES
```

### 5.4 Royal African Elephants (Simari 1992 §5 p.32-33)

On-path / off-path preemption. Classical specificity test case.
Required theory (reconstructed from the paper narrative the prompt
cites):

```python
elephant_theory = DefeasibleTheory(
    facts={"royal_elephant": [("clyde",)]},
    strict_rules=[
        Rule(id="s1", head="elephant(X)",        body=["royal_elephant(X)"]),
        Rule(id="s2", head="african_elephant(X)", body=["royal_elephant(X)"]),
    ],
    defeasible_rules=[
        Rule(id="d1", head="gray(X)",          body=["elephant(X)"]),
        Rule(id="d2", head="~gray(X)",         body=["african_elephant(X)"]),
        Rule(id="d3", head="gray(X)",          body=["royal_elephant(X)"]),
    ],
    defeaters=[], superiority=[], conflicts=[],
)
# Block 1 under TrivialPreference: UNDECIDED (expected-to-fail gate).
# Block 2 under GeneralizedSpecificity:
#   answer(elephant_theory, gray(clyde)) == YES
#   (the d3 argument preempts d2 via royal-elephant specificity).
```

**Gate for B1.6**: this case is marked expected-to-fail under
`TrivialPreference`. It will not pass until Block 2's
`GeneralizedSpecificity` is wired. The wiring coder should add it as an
xfail unit test and annotate it `# Block 2 gate`.

### 5.5 `depysible_nests_in_trees_*` (lives in the suite fixtures)

Fixture path:
`.venv/Lib/site-packages/datalog_conformance/_tests/defeasible/basic/depysible_birds.yaml`

Three `nests_in_trees` tests live in that file. Verbatim from
`depysible_birds.yaml:273-344`:

```yaml
- name: depysible_nests_in_trees_tina
  description: Tina's nesting query is blocked along with Tweety's.
  tags: [tina, flies, trees]
  theory:
    facts:
      chicken: [[tina]]
      penguin: [[tweety]]
      scared: [[tina]]
    strict_rules:
      - id: r1
        head: "bird(X)"
        body: ["chicken(X)"]
      - id: r2
        head: "bird(X)"
        body: ["penguin(X)"]
      - id: r3
        head: "~flies(X)"
        body: ["penguin(X)"]
    defeasible_rules:
      - id: r4
        head: "flies(X)"
        body: ["bird(X)"]
      - id: r5
        head: "flies(X)"
        body: ["chicken(X)", "scared(X)"]
      - id: r6
        head: "~flies(X)"
        body: ["chicken(X)"]
      - id: r7
        head: "nests_in_trees(X)"
        body: ["flies(X)"]
    defeaters: []
    superiority: []
  expect:
    undecided:
      nests_in_trees: [[tweety]]
- name: depysible_nests_in_trees_tweety
  description: Tweety's nesting conclusion stays undecided because flying is blocked.
  tags: [penguin, tweety, trees, undecided]
  theory:
    facts:
      chicken: [[tina]]
      penguin: [[tweety]]
      scared: [[tina]]
    strict_rules:
      - id: r1
        head: "bird(X)"
        body: ["chicken(X)"]
      - id: r2
        head: "bird(X)"
        body: ["penguin(X)"]
      - id: r3
        head: "~flies(X)"
        body: ["penguin(X)"]
    defeasible_rules:
      - id: r4
        head: "flies(X)"
        body: ["bird(X)"]
      - id: r5
        head: "flies(X)"
        body: ["chicken(X)", "scared(X)"]
      - id: r6
        head: "~flies(X)"
        body: ["chicken(X)"]
      - id: r7
        head: "nests_in_trees(X)"
        body: ["flies(X)"]
    defeaters: []
    superiority: []
  expect:
    undecided:
      nests_in_trees: [[tweety]]
```

And `depysible_nests_in_trees_henrietta` at
`depysible_birds.yaml:475-501`:

```yaml
- name: depysible_nests_in_trees_henrietta
  description: Henrietta nests in trees defeasibly once flying is derived.
  tags: [henrietta, flies, trees]
  source: depysible/README.md (derived positive-chicken variant)
  theory:
    facts:
      chicken: [[henrietta]]
      scared: [[henrietta]]
    strict_rules:
      - id: r1
        head: "bird(X)"
        body: ["chicken(X)"]
    defeasible_rules:
      - id: r2
        head: "flies(X)"
        body: ["bird(X)"]
      - id: r3
        head: "flies(X)"
        body: ["chicken(X)", "scared(X)"]
      - id: r4
        head: "nests_in_trees(X)"
        body: ["flies(X)"]
    defeaters: []
    superiority: []
  expect:
    defeasibly:
      nests_in_trees: [[henrietta]]
```

Status on master (per P0.1.5 surprise note): these tests **pass
today**. Block 1 must verify they still pass after the refactor. B1.6
wiring coder should re-run the full conformance suite after the
evaluator rewire.

Python literal (tina case):

```python
tina_theory = DefeasibleTheory(
    facts={
        "chicken": [("tina",)],
        "penguin": [("tweety",)],
        "scared":  [("tina",)],
    },
    strict_rules=[
        Rule(id="r1", head="bird(X)",    body=["chicken(X)"]),
        Rule(id="r2", head="bird(X)",    body=["penguin(X)"]),
        Rule(id="r3", head="~flies(X)",  body=["penguin(X)"]),
    ],
    defeasible_rules=[
        Rule(id="r4", head="flies(X)",          body=["bird(X)"]),
        Rule(id="r5", head="flies(X)",          body=["chicken(X)", "scared(X)"]),
        Rule(id="r6", head="~flies(X)",         body=["chicken(X)"]),
        Rule(id="r7", head="nests_in_trees(X)", body=["flies(X)"]),
    ],
    defeaters=[], superiority=[], conflicts=[],
)
# Expect model.sections["undecided"]["nests_in_trees"] contains ("tweety",)
```

### 5.6 Minimal strict-only case

Fixture path:
`.venv/Lib/site-packages/datalog_conformance/_tests/defeasible/strict_only/strict_only_basic_facts.yaml`

Verbatim:

```yaml
source: derived/strict-only/basic/facts.yaml
tags:
- defeasible
- strict-only
- basic
- facts
tests:
- name: strict_only_facts_only
  description: Strict-only defeasible form of facts_only.
  source: manual/scaffold
  tags:
  - basic
  - defeasible
  - facts
  - strict-only
  theory:
    facts:
      edge:
      - - a
        - b
      - - b
        - c
    strict_rules: []
    defeasible_rules: []
    defeaters: []
    superiority: []
  expect:
    definitely: &id001
      edge:
      - - a
        - b
      - - b
        - c
    defeasibly: *id001
```

Python literal:

```python
strict_only_theory = DefeasibleTheory(
    facts={"edge": [("a", "b"), ("b", "c")]},
    strict_rules=[],
    defeasible_rules=[],
    defeaters=[], superiority=[], conflicts=[],
)
# Expected:
#   model.sections["definitely"]["edge"] == {("a","b"), ("b","c")}
#   model.sections["defeasibly"]["edge"] == {("a","b"), ("b","c")}
#   answer(strict_only_theory, edge(a, b)) == YES
#   answer(strict_only_theory, edge(a, c)) == NO   (no strict rule derives it)
```

This is a **strict-only** theory so the existing
`_is_strict_only_theory` shortcut (defeasible.py:239-240) short-circuits
it through `SemiNaiveEvaluator`. The shortcut must survive B1.2.

---

## Section 6 — Module-level dependency graph of what will be deleted

### 6.1 Full inventory of `src/gunray/defeasible.py`

Every function/class in `defeasible.py` from top to bottom with its
disposition for B1.2.

| # | Name | Line | What it does | B1.2 disposition |
|---|------|------|--------------|------------------|
| 1 | `class DefeasibleEvaluator` | 41 | The public evaluator entry point with `evaluate` and `evaluate_with_trace`. | **KEEP SHELL, BODY → NotImplementedError stub** (per plan). B1.6 rewires it onto the paper pipeline. |
| 2 | `DefeasibleEvaluator.evaluate` | 44 | Delegates to `evaluate_with_trace`. | Keep thin delegator. |
| 3 | `DefeasibleEvaluator.evaluate_with_trace` | 48-236 | Current atom-level pipeline: strict-only shortcut, closure, grounding, fixed-point `_can_prove` loop, classification. | **Body deleted in B1.2**, stubbed `NotImplementedError`. B1.6 rewrites it to call `build_arguments` → `build_tree` → `mark` → populate sections from `answer(...)` results. |
| 4 | `_is_strict_only_theory` | 239-240 | Returns True when a theory has only strict rules (no defeasible, defeater, or superiority entries). | **KEEP** unchanged. The B1.6 pipeline needs it to keep routing strict-only theories through `SemiNaiveEvaluator`. |
| 5 | `_evaluate_strict_only_theory` | 243-245 | Untrace'd wrapper around `_evaluate_strict_only_theory_with_trace`. | **KEEP** unchanged. |
| 6 | `_evaluate_strict_only_theory_with_trace` | 248-263 | Builds a `SchemaProgram` from `theory.strict_rules` and runs it through `SemiNaiveEvaluator`, emitting a `DefeasibleModel` whose `definitely` and `defeasibly` sections equal the strict model. | **KEEP** unchanged. |
| 7 | `_strict_rule_to_program_text` | 266-269 | Renders `head` and `body` as Datalog text like `"path(X, Y) :- edge(X, Y)."`. | **KEEP** (used by #6). |
| 8 | `_positive_closure` | 272-290 | Semi-naive positive closure over `DefeasibleRule` inputs, returning `dict[str, IndexedRelation]`. | **DELETE in B1.2**. No caller outside this file (confirmed — only called from `DefeasibleEvaluator.evaluate_with_trace`). B1.3 recreates its logic inside `build_arguments`. |
| 9 | `_ground_rules` | 293-325 | Grounds a `list[DefeasibleRule]` against a `support_model`, returning `(grounded, unsupported_heads)`. Uses `_constant_universe`, `_candidate_head_bindings`, `_rule_variables`. | **DELETE in B1.2**. No caller outside this file. B1.3 recreates its logic inside `build_arguments`. |
| 10 | `_constant_universe` | 328-335 | Collects the set of scalars from a support model and returns them as a sorted tuple. | **DELETE in B1.2**. Only called by `_ground_rules`. |
| 11 | `_candidate_head_bindings` | 338-365 | Enumerates candidate head bindings from partial body bindings crossed with the constant universe. | **DELETE in B1.2**. Only called by `_ground_rules`. |
| 12 | `_can_prove` | 368-492 | The atom-level proof fixed-point: checks for live attackers, handles specificity, records trace entries. | **DELETE in B1.2** (explicit plan item). |
| 13 | `_supporter_survives` | 495-536 | Determines if a `supporter` rule survives all live attackers via specificity or superiority. | **DELETE in B1.2** (explicit plan item). |
| 14 | `_facts_to_atoms` | 539-544 | Flattens a `dict[str, IndexedRelation]` to `set[GroundAtom]`. | **DELETE in B1.2**. Only called by the fixed-point path that is being deleted. |
| 15 | `_atoms_to_section` | 547-551 | Groups a `set[GroundAtom]` into a `dict[predicate, set[arguments]]` section. | **MOVE to B1.6 evaluator wiring** — the new paper evaluator will still need to emit the four-key section shape. Candidate location: the new `DefeasibleEvaluator.evaluate_with_trace` body. |
| 16 | `_section_to_atoms` | 554-559 | Inverse of `_atoms_to_section`; used by the strict-only shortcut trace. | **KEEP** — referenced at `defeasible.py:63` inside the strict-only trace path (`_section_to_atoms(model.sections.get("definitely", {}))`). |
| 17 | `_expand_candidate_atoms` | 562-572 | For each atom, adds complement atoms based on the conflicts set. | **DELETE in B1.2** (explicit plan item). |
| 18 | `_rule_variables` | 575-582 | Collects variable names from a `DefeasibleRule`'s head and body. | **DELETE in B1.2** — only called by `_ground_rules` and `_candidate_head_bindings`. If B1.3 needs it inside `build_arguments`, copy it into the new module rather than importing. |
| 19 | `_atom_sort_key` | 585-586 | `(predicate, arguments)` key for stable sorting of `GroundAtom`. | **MOVE** — B1.4/B1.5 will need stable ordering for tree construction and `render_tree`. Suggested landing: the new `dialectic.py` module. |
| 20 | `_record_proof_attempt` | 589-609 | Appends a `ProofAttemptTrace` entry to a `DefeasibleTrace`. | **DELETE in B1.2**. B1.6 decides whether the new pipeline emits `proof_attempts` or only `classifications`. |
| 21 | `_rule_body_available` | 612-620 | Returns True when all body atoms of a `GroundDefeasibleRule` are in `proven` (or `definitely` for strict rules). | **DELETE in B1.2** (explicit plan item). |
| 22 | `_attacker_body_available` | 623-631 | Same as above but with `supported` instead of `proven`. | **DELETE in B1.2** (explicit plan item). |
| 23 | `_is_more_specific` | 634-644 | Current specificity heuristic: compares strict-body closures of two rules. | **DELETE in B1.2** (explicit plan item). Block 2's `GeneralizedSpecificity` replaces it at a different layer. |
| 24 | `_strict_body_closure` | 647-665 | Ground-atom strict closure with memoization. **Used as the reference implementation for B1.3's new `strict_closure` helper inside `disagreement.py`.** | **DELETE in B1.2** (explicit plan item). Its body must be recreated in `disagreement.py`. |
| 25 | `_find_blocking_peer` | 668-722 | Scans `rules_by_head` for an attacker/supporter pair that blocks with neither side more specific. | **DELETE in B1.2** (explicit plan item). |
| 26 | `_has_live_opposition` | 725-753 | Checks whether any non-strict attacking rule has its body in `attacker_basis`. | **DELETE in B1.2** (explicit plan item). |
| 27 | `_has_blocking_peer` | 756-784 | Boolean wrapper around `_find_blocking_peer`. | **DELETE in B1.2** (explicit plan item). |

### 6.2 Imports inside `defeasible.py` that B1.2 can cull

`defeasible.py:18-38`:

```python
from collections import defaultdict
from itertools import product
from typing import cast

from .ambiguity import AmbiguityPolicy, attacker_basis_atoms, resolve_ambiguity_policy
from .evaluator import SemiNaiveEvaluator, _match_positive_body
from .parser import ground_atom, parse_defeasible_theory
from .relation import IndexedRelation
from .schema import DefeasibleModel, FactTuple, ModelFacts, Policy
from .schema import DefeasibleTheory as SchemaDefeasibleTheory
from .schema import Program as SchemaProgram
from .trace import (
    ClassificationTrace,
    DatalogTrace,
    DefeasibleTrace,
    ProofAttemptTrace,
    TraceConfig,
)
from .types import DefeasibleRule, GroundAtom, GroundDefeasibleRule, variables_in_term
```

After B1.2 scorched earth, the surviving imports needed for the
strict-only shortcut are:
- `from .evaluator import SemiNaiveEvaluator`
- `from .parser import ... ` (maybe nothing)
- `from .schema import DefeasibleModel, ModelFacts, Policy, DefeasibleTheory, Program`
- `from .trace import DatalogTrace, DefeasibleTrace, TraceConfig`
- `from .types import GroundAtom`

The `.ambiguity` import goes away (whole module deleted), along with
`itertools.product`, `typing.cast`, `IndexedRelation`,
`ClassificationTrace`, `ProofAttemptTrace`, `DefeasibleRule`,
`GroundDefeasibleRule`, `variables_in_term`, `_match_positive_body`,
`ground_atom`, `parse_defeasible_theory`, `FactTuple`.

### 6.3 `src/gunray/ambiguity.py` (full, 39 lines) — DELETE

```python
"""Ambiguity-policy helpers for defeasible evaluation."""

from __future__ import annotations

from dataclasses import dataclass

from .schema import Policy
from .types import GroundAtom


@dataclass(frozen=True, slots=True)
class AmbiguityPolicy:
    """Operational ambiguity-policy switches for the current evaluator."""

    name: Policy
    attacker_basis: str


def resolve_ambiguity_policy(policy: Policy) -> AmbiguityPolicy:
    """Map a Gunray policy to the evaluator's attacker basis."""

    if policy is Policy.BLOCKING:
        return AmbiguityPolicy(name=policy, attacker_basis="proved")
    if policy is Policy.PROPAGATING:
        return AmbiguityPolicy(name=policy, attacker_basis="supported")
    raise ValueError(f"Unsupported ambiguity policy: {policy.value}")


def attacker_basis_atoms(
    policy: AmbiguityPolicy,
    *,
    proven: set[GroundAtom],
    supported: set[GroundAtom],
) -> set[GroundAtom]:
    """Return the atoms that may activate attacking rules under the chosen policy."""

    if policy.attacker_basis == "proved":
        return proven
    return supported
```

### 6.4 Consumers of `gunray.ambiguity`

`grep` for `from gunray.ambiguity|import gunray.ambiguity|from \.ambiguity|from \.\.ambiguity` yields **exactly two** source matches:

- `src/gunray/defeasible.py:24` —
  `from .ambiguity import AmbiguityPolicy, attacker_basis_atoms, resolve_ambiguity_policy`
  (deleted with defeasible's body)
- `tests/test_defeasible_core.py:6` —
  `from gunray.ambiguity import resolve_ambiguity_policy`
  (the whole test file is deleted; see 6.5)

No other consumer. Safe to delete the whole module.

### 6.5 `tests/test_defeasible_core.py` — DELETE

Six tests total (full file 176 lines):

1. `test_readme_discloses_reduced_specificity_and_defeat_contract`
   (lines 17-22) — asserts that `README.md` contains the phrases
   `"strict-body specificity heuristic"` and
   `"not full DeLP/ASPIC-style dialectical argument comparison"`.
   **Coverage dropped**: the README disclosure test. This test
   becomes OBSOLETE because Block 1 deletes the reduced specificity
   heuristic entirely; the README will be rewritten in Block 3 to
   describe the paper pipeline. **Do not preserve.**

2. `test_expand_candidate_atoms_adds_conflicting_complements`
   (25-37) — exercises `_expand_candidate_atoms`. Coverage dropped:
   conflict-based complement expansion. **Do not preserve** — the
   paper pipeline builds arguments for both polarities directly via
   `disagrees`, not via a complement-expansion pass.

3. `test_is_more_specific_uses_strict_body_closure` (40-65) —
   exercises `_is_more_specific` on the PhD/department case. Coverage
   dropped: strict-body specificity between a narrower and broader
   supporter. **Do not preserve** — specificity is a Block 2 concern
   and the new machinery is `GeneralizedSpecificity`, not
   `_is_more_specific`.

4. `test_equally_specific_defeasible_attacker_blocks_supporter`
   (68-97) — exercises `_supporter_survives` on Nixon. Coverage
   dropped: peer-blocking of an equally specific attacker. **Partial
   preserve**: B1.4 coder's `counter_argues` / `proper_defeater` unit
   test should re-prove this with the Nixon theory from Section 5.2;
   the paper-level assertion is that the Nixon case yields `UNDECIDED`.

5. `test_equal_strength_opponents_are_classified_as_blocking_peers`
   (100-138) — exercises `_has_blocking_peer` with
   `Policy.PROPAGATING`. Coverage dropped: propagating-ambiguity
   peer detection. **Do not preserve** — propagating semantics are
   not part of Block 1's TrivialPreference path.

6. `test_blocking_fixed_point_leaves_nixon_conflict_undecided`
   (141-159) — integration test that `DefeasibleEvaluator().evaluate`
   classifies Nixon's pacifist as `undecided` under blocking.
   **Preserve** as a B1.6 integration test against the new
   evaluator: `answer(nixon_theory, pacifist(nixon)) == UNDECIDED`.

7. `test_missing_body_literal_still_classifies_head_as_not_defeasibly`
   (162-175) — integration test: `flies(X) :- bird(X), injured(X)`
   with `bird(tweety)` but no `injured(tweety)` should classify
   `flies(tweety)` as `not_defeasibly`. **Preserve** as a B1.6
   integration test: `answer(..., flies(tweety)) == NO`. The paper
   pipeline must still reject arguments whose body cannot be
   grounded.

Private helpers the file imports from `gunray.defeasible`:
`_expand_candidate_atoms`, `_has_blocking_peer`, `_is_more_specific`,
`_supporter_survives`. All four are among the functions B1.2 deletes.

### 6.6 Summary for B1.2 coder

**DELETE**: `src/gunray/ambiguity.py`, `tests/test_defeasible_core.py`,
and every item in the inventory above marked DELETE.

**KEEP** in `defeasible.py`: `_is_strict_only_theory`,
`_evaluate_strict_only_theory`,
`_evaluate_strict_only_theory_with_trace`,
`_strict_rule_to_program_text`, `_section_to_atoms`. `DefeasibleEvaluator`
class stays but `evaluate_with_trace` body becomes
`raise NotImplementedError("rewired in B1.6")`.

**MOVE** to new modules: `_atoms_to_section` (→ keep in
`defeasible.py` for B1.6's pipeline to reuse, or inline it),
`_atom_sort_key` (→ `dialectic.py`).

**RECREATE** elsewhere (knowledge preserved in this report, code
deleted): `_strict_body_closure` body → `disagreement.py`;
`_positive_closure` + `_ground_rules` logic → `arguments.py`
(`build_arguments`).

---

## End of report

Every code snippet above is verbatim from the source tree at the
commit of dispatch. If the downstream coder needs a byte-identical
copy they can trust this report rather than reopening the files.
