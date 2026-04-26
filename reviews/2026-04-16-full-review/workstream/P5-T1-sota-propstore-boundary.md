# P5-T1 — SOTA and propstore boundary workstream

Status: active proposal for the next workstream slice.

Date: 2026-04-26

## Context

The SOTA survey found that Gunray is already a strong DeLP + Datalog +
propositional KLM package, but it is not a field-wide SOTA
argumentation platform. The highest-payoff next work is not to add a
fourth engine immediately. It is to make the existing formal core a
clean backend for `../propstore`, then add literature-driven grounding
and query capabilities through that boundary.

This task file converts `notes/sota-survey-2026-04-25.md` and the
2026-04-26 follow-up discussion into executable slices.

## Baseline

Verified from `C:\Users\Q\code\gunray` on 2026-04-26:

```powershell
uv run pytest tests -q
# 207 passed, 293 skipped, 2 deselected

uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.conformance_adapter.GunrayConformanceEvaluator -q
# 284 passed, 9 skipped, 2 deselected
```

Do not use older review counts as current truth.

## Thesis

Gunray should remain the domain-agnostic formal backend for:

- DeLP-style defeasible logic programming;
- stratified Datalog and grounding support;
- propositional KLM closure;
- explanations and traces over those results.

`propstore` should not treat Gunray atoms, predicate strings, or rule
text as propstore identity. It should consume Gunray through typed
projection frames that can map every backend fact, rule, argument, and
explanation back to source assertions.

## Non-goals

These are explicitly out of scope for this workstream unless a later
task file changes ownership:

- Do not move `argumentation.aspic` into Gunray.
- Do not duplicate `propstore.praf` or the probabilistic AF kernel in
  Gunray.
- Do not make Gunray know propstore concepts, claims, contexts,
  opinions, sidecar rows, source documents, or policy objects.
- Do not add compatibility wrappers that preserve the current
  string-scanning boundary as the final API.

## Papers

Primary implementation anchors:

- Diller et al. 2025, *Grounding Rule-Based Argumentation Using
  Datalog* — ground substitutions, non-approximated predicates,
  ASPIC+-specific simplification.
- Garcia and Simari 2004, *Defeasible Logic Programming* — arguments,
  dialectical trees, four-valued answers, explanations.
- Simari and Loui 1992, *A Mathematical Treatment of Defeasible
  Reasoning* — generalized specificity.
- Morris, Ross, and Meyer 2020, *Algorithmic Definitions for
  KLM-style Defeasible Disjunctive Datalog* — KLM closure scope and
  limits.

Important propstore-side anchors:

- Modgil and Prakken 2018 / Modgil 2014 / Prakken 2010 — ASPIC+
  ownership remains with the `argumentation` package and propstore
  adapter.
- Lehtonen et al. 2024 — preferential ASPIC+ algorithms and the
  warning against naive full argument enumeration.
- Odekerken et al. 2025 — incomplete-information stability and
  relevance; this belongs in propstore fragility/query planning unless
  a generic backend kernel is deliberately extracted.
- Popescu and Wallner 2024 — exact PrAF DP; this belongs with the PrAF
  owner, not in Gunray by default.

## Workstream order

Execute these slices in strict order. Do not start Diller-style
grounding before S1 is complete.

### S0 — Current API inventory

Purpose:

- Establish the current public/private seam between Gunray and
  propstore.
- Turn the survey's claims into grep-backed facts.

Files:

- `src/gunray/__init__.py`
- `src/gunray/types.py`
- `src/gunray/parser.py`
- `src/gunray/schema.py`
- `src/gunray/adapter.py`
- `src/gunray/trace.py`
- `../propstore/propstore/grounding/*.py`
- `../propstore/propstore/aspic_bridge/**`
- `../propstore/tests/test_gunray_integration.py`

Red:

- Add an API inventory test or report that fails if propstore imports
  a Gunray symbol not deliberately exported or documented.
- The first red target is the known leakage: `parse_atom_text`,
  `GroundAtom`, `Constant`, `Variable`, and `DefeasibleSections`.

Green:

- Do not fix the exports in S0 unless the red test itself requires a
  minimal helper. The output is the inventory and the failing gate.

Acceptance:

```powershell
uv run pytest tests/test_public_api.py -q
uv run pytest tests -q
```

Commit shape:

```text
test(api): inventory propstore-facing public seam (workstream P5-T1 S0 red)
```

### S1 — Public term and parser surface

Purpose:

- Pick one typed boundary instead of letting propstore scan predicate
  strings and import internal Gunray modules.

Target outcome:

- `GroundAtom`, `Constant`, `Variable`, `Scalar`, `FactTuple`,
  `DefeasibleSections`, and `parse_atom_text` are public if propstore
  is expected to use them.
- `types.py` no longer presents these exported values as internal-only.
- `evaluate_with_trace` has a useful public return type instead of
  forcing propstore to cast from `object`.

Red:

- `tests/test_public_api.py` asserts the promoted symbols are exported
  from `gunray`.
- A type-focused test or pyright fixture shows `evaluate_with_trace`
  can be consumed without `cast(DefeasibleTrace, ...)` for a
  `DefeasibleTheory`.

Green:

- Promote only the symbols already consumed or needed for the typed
  seam.
- Do not invent a second atom type.
- Keep backwards-compatible module imports working.

Acceptance:

```powershell
uv run pytest tests/test_public_api.py -q
uv run pyright src/gunray
uv run pytest tests -q
uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.conformance_adapter.GunrayConformanceEvaluator -q
```

Commit shape:

```text
test(api): pin propstore-facing term exports (workstream P5-T1 S1 red)
feat(api): promote typed propstore boundary (workstream P5-T1 S1 green)
```

### S2 — Trace/query boundary

Purpose:

- Make explanations and local queries consume typed atoms directly.
- Avoid propstore-side manual scans over `trace.trees.items()`.

Target outcome:

- `DefeasibleTrace.tree_for`, `marking_for`, and
  `arguments_for_conclusion` are enough for propstore explanations.
- Add ergonomic overloads or helpers only if they remove real
  cross-package friction, for example construction from public atom
  text or public `GroundAtom`.

Red:

- A test reproduces the propstore pattern currently found in
  `propstore/grounding/explanations.py`: given a requested atom, find
  the matching tree without hand-walking predicate strings.

Green:

- Add the minimal query helper in Gunray or adjust public types so the
  existing helpers work from propstore.
- Keep rendering ownership in Gunray: `explain`, `render_tree`, and
  `render_tree_mermaid` remain the renderer for Gunray trees.

Acceptance:

```powershell
uv run pytest tests/test_trace.py tests/test_explain.py -q
uv run pyright src/gunray
uv run pytest tests -q
```

Commit shape:

```text
test(trace): reproduce typed tree lookup need (workstream P5-T1 S2 red)
feat(trace): expose typed query helpers for explanations (workstream P5-T1 S2 green)
```

### S3 — Grounded substitution bundle

Purpose:

- Add the Diller 2025-shaped object propstore actually needs:
  grounded substitutions and grounded rule instances with provenance
  enough to map back to authored rules.

Target outcome:

- A Gunray-owned typed result can answer:
  - which source rule grounded;
  - what substitution was used;
  - what grounded head/body atoms were produced;
  - whether the instance is strict, defeasible, defeater, or
    presumption;
  - which facts/rules supported the grounding, when cheaply available.

Red:

- Add a Diller-style birds example showing two facts produce two
  grounded rule instances with stable substitutions.
- Add a negative case where an unsatisfied body produces no grounded
  instance.

Green:

- Expose a grounding inspection API from the same grounding machinery
  already used by `build_arguments`.
- Do not reimplement a parallel parser or grounder.
- Do not require propstore to reconstruct substitutions from rule
  names such as `rule_id#...`.

Acceptance:

```powershell
uv run pytest tests/test_grounding_inspection.py -q
uv run pytest tests/test_arguments_basics.py tests/test_build_arguments.py -q
uv run pyright src/gunray
uv run pytest tests -q
```

Commit shape:

```text
test(grounding): pin grounded substitution bundle (workstream P5-T1 S3 red)
feat(grounding): expose grounded rule instances (workstream P5-T1 S3 green)
```

### S4 — Diller simplification gate

Purpose:

- Decide whether to implement Diller 2025 non-approximated predicate
  simplification in Gunray.

Gate:

- Before writing code, read the Diller page images or the paper PDF
  directly. Notes are not enough for this slice.

Red:

- Add a tiny theory where strict/fact-only predicates can be resolved
  without generating useless argumentative ground rules.
- Add a correctness oracle that the simplified and unsimplified
  outputs produce the same relevant conclusions for the tested
  fragment.

Green:

- Implement conservative simplification only.
- If a predicate cannot be proven non-approximated by the implemented
  analysis, leave it approximated.
- Return an explicit explanation of which rules were eliminated or
  resolved in Datalog.

Acceptance:

```powershell
uv run pytest tests/test_grounding_simplification.py -q
uv run pytest tests/test_conformance.py --datalog-evaluator=gunray.conformance_adapter.GunrayConformanceEvaluator -q
uv run pyright src/gunray
```

Commit shape:

```text
test(grounding): pin Diller simplification invariant (workstream P5-T1 S4 red)
feat(grounding): add conservative non-approximated predicate analysis (workstream P5-T1 S4 green)
```

### S5 — Propstore consumer update

Purpose:

- Make `../propstore` consume the new public Gunray surface.

Propstore target files:

- `propstore/grounding/translator.py`
- `propstore/grounding/grounder.py`
- `propstore/grounding/explanations.py`
- `propstore/grounding/inspection.py`
- `propstore/grounding/gunray_complement.py`
- `tests/test_gunray_integration.py`
- `tests/test_grounding_grounder.py`

Red:

- In propstore, add tests that fail if the bridge rebuilds substitutions
  from stringified rule names instead of using Gunray's typed grounded
  rule instance API.
- Add a test that explanations call the typed trace query path rather
  than walking trace dictionaries by predicate string.

Green:

- Replace internal Gunray imports with public exports.
- Remove propstore-side substitution-name parsing where the typed
  Gunray result now owns it.
- Preserve sidecar section semantics: all four sections remain present
  in `GroundedRulesBundle`.

Acceptance from `C:\Users\Q\code\propstore`:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label gunray-boundary `
  tests/test_gunray_integration.py `
  tests/test_grounding_grounder.py `
  tests/test_grounding_inspection.py
uv run pyright propstore
git diff --check
```

Commit shape:

```text
test(grounding): require typed gunray boundary (workstream P5-T1 S5 red)
fix(grounding): consume public gunray term and grounding APIs (workstream P5-T1 S5 green)
```

## Exit gate

The workstream is complete only when:

- Gunray exposes every symbol propstore imports from Gunray-owned
  modules, or propstore no longer imports it.
- Propstore explanations use typed trace/query APIs rather than manual
  string scans.
- Propstore no longer reconstructs grounded substitutions from
  synthesized rule-name strings when Gunray can provide them.
- Gunray unit suite passes.
- Gunray conformance suite passes with no new unexpected skips.
- Propstore targeted Gunray integration tests pass.
- `uv run pyright src/gunray` and `uv run pyright propstore` pass for
  touched surfaces.

## Stop conditions

Stop and write a blocker if:

- Diller simplification requires ASPIC+ ownership decisions that belong
  in the `argumentation` package rather than Gunray.
- The proposed public term surface conflicts with `argumentation.aspic`
  in a way that would require a three-repo migration.
- A propstore caller needs source-assertion identity that cannot be
  represented in Gunray without importing propstore concepts.
- Two consecutive implementation slices fail to reduce private-surface
  leakage or string-based boundary code.
