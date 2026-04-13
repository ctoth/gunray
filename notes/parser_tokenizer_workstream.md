# Parser Tokenizer Refactor Workstream
## 2026-04-12

**GOAL:** Replace the duplicated parser scanning logic with one tokenizer-backed implementation, using `pytest` + Hypothesis as the control surface, while preserving the existing AST and evaluator behavior exactly.

**DECISION:** Do **not** replace the parser with Lark in this workstream. The target architecture is:
- keep `src/gunray/types.py` unchanged
- keep `src/gunray/evaluator.py` and `src/gunray/compiled.py` consuming the same AST dataclasses
- refactor `src/gunray/parser.py` so all quote tracking, escape handling, parenthesis depth, top-level comma splitting, and operator discovery flow through one tokenizer / scanner implementation

**WHY THIS AND NOT LARK:**
- The grammar is still narrow.
- The main defect source is duplicated scan state, not missing grammar power.
- A Lark migration would still have to recreate the exact current AST and preserve all evaluator assumptions.
- The cheaper and safer change is to centralize scanning and prove behavior with property tests.

## Scope

**In scope:**
- `src/gunray/parser.py`
- parser-focused tests
- targeted evaluator/compiler tests that depend on parser output shape
- optional small helper module only if `parser.py` becomes materially clearer

**Out of scope:**
- Lark or any parser generator
- AST redesign
- evaluator semantics changes
- compiled matcher redesign
- language expansion

## Current Constraints

**Files coupled to parser output:**
- `src/gunray/types.py`
- `src/gunray/evaluator.py`
- `src/gunray/compiled.py`
- `src/gunray/defeasible.py`

**Current parser hotspots:**
- `split_top_level`
- `_find_top_level_binary`
- `_find_rightmost_top_level_binary`
- `_find_top_level_operator`

These each re-implement quote state, escape handling, and parenthesis depth independently.

**Current verified parser behavior that must stay true:**
- quoted strings remain strings, even when they look numeric or boolean
- additive chains are left-associative
- rules split on top-level commas only
- comparisons are detected only at top level
- `not ` in rule bodies is parsed as negation-as-failure
- wildcard tokens parse as `Wildcard`

## Deliverables

1. Expanded parser contract tests using `pytest` + Hypothesis.
2. A single tokenizer / scanner implementation for parser boundary detection.
3. Refactored parser entrypoints consuming that tokenizer.
4. Deletion of redundant scan helpers.
5. Verification notes captured by test output and representative example cases.

## Phase 0: Test Harness Baseline

**Goal:** Ensure parser-focused verification is deterministic before refactoring.

**Observed current state:**
- `uv run pytest tests -q` does not collect cleanly in the current environment.
- Targeted runs work with `PYTHONPATH=src`.

**Canonical local commands for this workstream:**

```powershell
$env:PYTHONPATH='src'
uv run pytest tests\test_parser_review_v2.py -q
```

```powershell
$env:PYTHONPATH='src'
uv run pytest tests\test_parser_review_v2.py tests\test_evaluator_review_v2.py tests\test_compiled_matcher.py -q
```

**Exit criteria:**
- parser-focused test command is stable and repeatable
- the workstream uses one canonical command family consistently

## Phase 1: Lock Down the Parser Contract

**Goal:** Make current behavior explicit before touching implementation.

### 1A. Example tests

Add direct example tests for:
- top-level comma splitting with nested atoms
- top-level comma splitting with quoted commas
- escaped quotes inside quoted strings
- empty / malformed atom and rule errors
- comparison parsing for each operator: `<=`, `>=`, `==`, `!=`, `<`, `>`
- `not` parsing in bodies with mixed positive, negative, and constraint items
- arithmetic nesting such as `1+2-3`, `1-2-3`, `X+1`, `X-1+2`
- defeasible rule head/body parsing via `parse_defeasible_rule`

### 1B. Hypothesis strategies

Add parser-specific strategies for:
- identifiers valid under current parser assumptions
- safe quoted strings without unbalanced delimiters
- scalar literals:
  - ints
  - finite floats
  - booleans
  - quoted strings
- wildcard tokens:
  - `_`
  - `_name`
- value terms:
  - constants
  - variables
  - additive/subtractive trees
- atom terms:
  - wildcard plus value terms
- atoms:
  - zero-arity predicate
  - predicate with generated argument lists
- top-level comma-separated sequences with nested parentheses and quoted strings
- comparisons built from generated value terms

### 1C. Hypothesis properties

Use property tests for these invariants:

**Top-level splitting**
- joining generated items with `", "` and then `split_top_level` returns the original items
- commas inside quotes do not split
- commas inside nested parentheses do not split

**Scalar identity**
- if generated as quoted string, parse result is `Constant(str)` and never coerced to `int`, `float`, or `bool`
- unquoted `true`/`false` map to booleans
- numeric literals map to numeric constants when valid under current parser behavior

**Associativity**
- for generated additive/subtractive chains without parentheses, parsed evaluation matches Python's left-associative arithmetic over the same values
- this property should be restricted to numeric-only generated terms and finite results

**Comparison detection**
- generated expressions containing comparison operators nested inside parentheses are not treated as top-level comparisons by `_is_constraint`
- generated top-level comparisons are treated as constraints

**Rule body partitioning**
- generated rule bodies made of positive atoms, negated atoms, and comparisons end up in the correct `positive_body`, `negative_body`, and `constraints` slots

**Parse/evaluate compatibility**
- for generated constant-only additive expressions, `parse_value_term` then `evaluate_term` matches expected arithmetic

### 1D. Negative tests

Add explicit regression tests for malformed inputs:
- empty atom
- empty term
- missing predicate name
- unterminated string
- mismatched parentheses
- unsupported comparison literal

**Exit criteria:**
- parser behavior is materially specified by tests, not by reading implementation
- the recent quoted-string and left-associativity bugs are both covered by unit and property tests

## Phase 2: Design the Tokenizer Surface

**Goal:** Define one scanning abstraction before rewriting parser entrypoints.

### Required tokenizer capabilities

The tokenizer / scanner must provide enough structure to support:
- top-level comma splitting
- leftmost and rightmost top-level operator discovery
- top-level comparison operator discovery for multi-character operators
- awareness of:
  - current depth
  - whether inside quoted string
  - whether current quote character is escaped

### Recommended shape

Keep this minimal. One of these two forms is acceptable:

**Option A: event scanner**
- one function walks text once
- caller provides predicate / collection logic for interesting top-level positions

**Option B: token stream**
- scanner emits a lightweight sequence of tokens / boundaries
- parser helpers query that sequence for commas and operators

For this repo, Option A is probably smaller and enough.

### Non-goals for tokenizer

Do not turn this into:
- a full lexer with token classes for all grammar items
- a second AST
- a generic parsing framework

**Exit criteria:**
- one scanner concept is sufficient to replace all four duplicated scan helpers
- the design still supports current left-associative arithmetic behavior

## Phase 3: Refactor Parser Entrypoints

**Goal:** Move all parser entrypoints onto the shared scanner.

### 3A. Refactor order

Do this in this order:

1. `split_top_level`
2. `_find_top_level_operator`
3. `_find_rightmost_top_level_binary`
4. `_find_top_level_binary`
5. `parse_constraint_text`
6. `parse_value_term`
7. `parse_term_text`
8. `parse_atom_text`
9. `parse_rule_text`

The early steps replace helpers while preserving interfaces. The later steps shift the parser to depend on the new implementation.

### 3B. Keep AST exact

These outputs must remain byte-for-byte equivalent in structure:
- `Variable`
- `Wildcard`
- `Constant`
- `AddExpression`
- `SubtractExpression`
- `Comparison`
- `Atom`
- `Rule`
- `DefeasibleRule`

No wrapper nodes. No subclasses. No field changes.

### 3C. Preserve parser semantics

Must preserve:
- quoted string parsing via `literal_eval` or equivalent exact behavior
- unquoted bool/int/float recognition order
- current handling of zero-arity atoms
- current body splitting semantics
- current `not ` handling contract

### 3D. Improve error clarity only when behavior stays compatible

If malformed input messages become clearer, that is acceptable. But do not broaden accepted grammar in this workstream.

**Exit criteria:**
- all parser entrypoints use the shared scanner path
- parser AST output remains identical for existing tests and representative cases

## Phase 4: Delete Redundant Logic

**Goal:** Remove the duplicate scan implementations after migration.

Delete old helpers only after Phase 3 passes:
- old depth/quote tracking loops
- any helper that no longer owns unique logic

**Acceptance condition:**
- there is exactly one implementation that tracks quote state + escape handling + parenthesis depth for delimiter/operator discovery

## Phase 5: Verification Matrix

**Goal:** Prove the refactor kept behavior and reduced risk.

### 5A. Fast loop during development

```powershell
$env:PYTHONPATH='src'
uv run pytest tests\test_parser_review_v2.py -q
```

### 5B. Parser-adjacent validation

```powershell
$env:PYTHONPATH='src'
uv run pytest tests\test_parser_review_v2.py tests\test_evaluator_review_v2.py tests\test_compiled_matcher.py -q
```

### 5C. Broader local suite if environment permits

```powershell
$env:PYTHONPATH='src'
uv run pytest tests\test_trace.py tests\test_defeasible_core.py tests\test_closure.py -q
```

### 5D. Representative manual sanity cases

Check exact parsing for:
- `p("1")`
- `p("true")`
- `p("1,2")`
- `ok(X) :- person(X), not banned(X, Y).`
- `score(X+1) :- base(X).`
- `a(X) :- b(X), (X <= 3).`
- `path(X, Z) :- edge(X, Y), path(Y, Z).`

### 5E. Keep/revert rule

If a slice does not produce a kept simplification or a passing test delta, revert that slice instead of carrying dead refactor churn forward.

**Exit criteria:**
- parser tests pass
- parser-adjacent evaluator/compiler tests pass
- representative parse outputs are unchanged in substance
- duplicate scan logic is gone

## Risk Register

### Risk 1: Hidden AST drift

**Failure mode:** tokenizer refactor changes node shape or term nesting.

**Mitigation:**
- assert exact dataclass types in tests
- compare representative parsed structures directly, not only evaluated outcomes

### Risk 2: Changed arithmetic associativity

**Failure mode:** `1-2-3` becomes right-associative.

**Mitigation:**
- example tests
- Hypothesis property comparing parser evaluation against left-associative expectation

### Risk 3: Quoted-string coercion regression

**Failure mode:** `"1"` or `"true"` becomes numeric or boolean.

**Mitigation:**
- dedicated regression tests
- generated quoted-string property tests

### Risk 4: Accidental grammar broadening

**Failure mode:** tokenizer starts accepting syntax the evaluator path does not really support.

**Mitigation:**
- keep tests centered on current contract
- treat acceptance changes as out of scope unless explicitly requested

### Risk 5: Silent compiler fast-path regression

**Failure mode:** parser still passes evaluator tests but changes term structures enough to reduce `compiled.py` fast-path eligibility.

**Mitigation:**
- keep `tests/test_compiled_matcher.py` in the required validation set
- add parser-driven cases that still produce plain `Variable` / `Constant` terms where expected

## Suggested File Changes

**Primary:**
- `src/gunray/parser.py`
- `tests/test_parser_review_v2.py`

**Possible additions if clarity demands it:**
- `tests/test_parser_hypothesis.py`
- `src/gunray/parser_scanner.py`

Default preference: keep it in `parser.py` unless extraction clearly reduces complexity.

## Sequence of Execution

1. Expand parser example tests.
2. Add Hypothesis strategies and properties.
3. Verify tests fail when expected against injected bad behavior if needed to confirm they are meaningful.
4. Implement shared scanner.
5. Migrate helper functions onto scanner.
6. Migrate parser entrypoints onto scanner.
7. Delete old helpers.
8. Run required validation matrix.
9. Stop only when the redundant scan family is fully removed or a concrete blocker is found.

## Completion Standard

This workstream is complete only when all of the following are true:
- the parser has one scanner implementation for top-level delimiter/operator discovery
- parser behavior is covered by example tests plus Hypothesis properties
- additive associativity and quoted-string identity are both locked by tests
- evaluator/compiler compatibility is preserved
- no old duplicate scanner path remains in production code

**NOT complete:**
- "tests pass but old scanner helpers still exist"
- "tokenizer added but parser still uses mixed old/new paths"
- "parser simplified but property coverage not added"

## Final Recommendation

Execute this as a single-target convergence effort on the parser surface only. Do not widen into evaluator cleanup, grammar expansion, or Lark experimentation during the refactor. The value here is exact behavior preservation plus removal of the duplicated scanner bug farm.
