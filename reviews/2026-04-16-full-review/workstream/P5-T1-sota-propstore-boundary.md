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

## Propstore control surface

`../propstore/plans/epistemic-os-workstreams-2026-04-25.md` is the
active control surface for propstore-side semantic refactoring. This
Gunray workstream is subordinate to that plan.

The propstore trunk is:

```text
relation concepts -> situated assertions -> context lifting -> projection
round trips -> import-ready provenance -> epistemic state machinery
```

The key consequence is that current propstore predicate strings,
grounding source kinds, and direct runtime bundle rebuilds are
transitional surfaces. They are useful for inventory and regression
tests, but they must not become the target architecture.

The propstore phases that own this boundary are:

- **WS6 Projection Boundary V2.** Backend atoms, Z3 terms, ASPIC
  arguments, SQL rows, and Gunray atoms are not propstore identity.
  Projection frames must carry source assertion ids or explicit loss
  witnesses, and backend results lift back into situated assertions
  with projection provenance.
- **WS7 Grounding Completion.** Grounding must cover relation concepts,
  role bindings, claim attributes, claim conditions, contextual facts,
  provenance-aware derived facts, and four-status rule output. Sidecar
  materialization becomes the runtime source; runtime must not silently
  rebuild a parallel bundle from repository files.

Therefore S0-S4 below are Gunray-side enabling work that can proceed in
this repo. S5 is not an instruction to mutate current propstore
grounding immediately. S5 runs only when propstore's active plan opens
the corresponding WS6/WS7 slice, or when that plan is amended to link
this workstream as a child artifact.

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

Gunray's job is to make that possible by exposing stable typed backend
objects and traces. Propstore's semantic OS owns relation concepts,
situated assertion identity, projection-frame identity, policy,
sidecar materialization, provenance, and lifting results back into the
epistemic state.

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
- Do not update propstore in a way that bypasses or competes with
  `../propstore/plans/epistemic-os-workstreams-2026-04-25.md`.
- Do not fossilize current propstore `concept.relation`,
  `claim.attribute`, or `claim.condition` source-kind projection as the
  final architecture; the semantic OS plan says WS6 replaces that with
  assertion projection.

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

Each slice has two readings:

- **Gunray-side reading:** what can be implemented in this repo without
  depending on propstore's ongoing semantic migration.
- **Propstore-side reading:** how the result should eventually be
  consumed under WS6/WS7. Current propstore files are evidence and
  regression fixtures, not the final identity model.

### S0 — Current API inventory

Purpose:

- Establish the current public/private seam between Gunray and
  propstore.
- Turn the survey's claims into grep-backed facts.
- Distinguish current transitional propstore consumers from the
  semantic OS target surface.

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
- The inventory must classify each propstore call site as one of:
  current transitional grounding surface, WS6 projection-boundary
  candidate, WS7 grounding-completion candidate, or historical/test
  only.

Green:

- Do not fix the exports in S0 unless the red test itself requires a
  minimal helper. The output is the inventory and the failing gate.
- Do not write propstore production code in S0.

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
- Provide backend term objects suitable for propstore projection-frame
  mapping without making them propstore identity.

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
- Keep the semantics explicit: `GroundAtom` is a Gunray/backend atom,
  not a propstore situated assertion, relation concept, or source
  identity.

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
- Give propstore WS6 a backend-result query surface that can be lifted
  through projection provenance.

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
- Do not add propstore assertion ids to Gunray trace objects. If a
  caller needs assertion identity, it belongs in the propstore
  projection frame that maps assertion ids to backend atoms/rules.

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
- Provide a backend artifact that propstore WS6/WS7 can attach to
  projection-frame rows, sidecar materialization, and lifted
  situated-assertion results.

Target outcome:

- A Gunray-owned typed result can answer:
  - which source rule grounded;
  - what substitution was used;
  - what grounded head/body atoms were produced;
  - whether the instance is strict, defeasible, defeater, or
    presumption;
  - which facts/rules supported the grounding, when cheaply available.
- The result is backend-local. It may carry stable source rule ids and
  backend substitutions, but it must not import propstore assertion,
  relation, context, provenance, or sidecar types.

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
- Include enough stable backend identifiers for propstore to maintain
  its own projection-frame mapping outside Gunray.

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
- Keep the simplification generic. It optimizes/backend-documents
  grounding; it does not choose propstore's assertion identity or
  sidecar storage shape.

Gate:

- Before writing code, read the Diller page images or the paper PDF
  directly. Notes are not enough for this slice.
- If this slice touches propstore projection design, stop and switch to
  propstore WS6/WS7 instead of continuing inside Gunray.

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

- Align `../propstore` consumption with the new Gunray public surface
  when the active semantic OS plan reaches the relevant projection and
  grounding slices.

Status:

- Deferred until propstore WS6 Projection Boundary V2 or WS7 Grounding
  Completion opens a slice that names this workstream as a dependency.
- Current propstore files listed below are evidence of the existing
  consumer surface, not an instruction to harden that surface as final.

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
- Add or reuse semantic OS projection tests proving that Gunray atoms
  and grounded rules are projected from situated assertions with source
  assertion ids or explicit loss witnesses.
- Add or reuse runtime-path gates proving the final runtime path reads
  sidecar materialization when WS7 owns the compiled grounding
  substrate, rather than rebuilding a parallel bundle from repository
  files.

Green:

- Replace internal Gunray imports with public exports.
- Remove propstore-side substitution-name parsing where the typed
  Gunray result now owns it.
- Preserve sidecar section semantics: all four sections remain present
  in `GroundedRulesBundle`.
- Preserve the semantic OS ownership rule: propstore identity remains a
  situated assertion / projection-frame identity, not a Gunray
  `GroundAtom`.
- If the current `GroundedRulesBundle` is still transitional during the
  propstore slice, name that explicitly in the propstore workstream
  ledger and do not present it as the final runtime source.

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
- Gunray provides a typed backend term, trace, and grounded-instance
  surface suitable for propstore WS6 projection frames.
- If S5 has run, propstore explanations use typed trace/query APIs
  rather than manual string scans.
- If S5 has run, propstore no longer reconstructs grounded
  substitutions from synthesized rule-name strings when Gunray can
  provide them.
- If S5 has run, propstore projection tests show Gunray atoms/rules are
  backend artifacts mapped from situated assertions, not source
  identity.
- Gunray unit suite passes.
- Gunray conformance suite passes with no new unexpected skips.
- Propstore targeted Gunray integration tests pass if a propstore slice
  was part of the workstream.
- `uv run pyright src/gunray` and `uv run pyright propstore` pass for
  touched surfaces. If propstore was not touched, the propstore pyright
  gate is deferred to the owning WS6/WS7 slice.

## Stop conditions

Stop and write a blocker if:

- Diller simplification requires ASPIC+ ownership decisions that belong
  in the `argumentation` package rather than Gunray.
- The proposed public term surface conflicts with `argumentation.aspic`
  in a way that would require a three-repo migration.
- A propstore caller needs source-assertion identity that cannot be
  represented in Gunray without importing propstore concepts.
- Any implementation step would modify propstore outside the active
  semantic OS workstream gate.
- A propstore test would lock in predicate-string or
  `GroundedRulesBundle` identity as final architecture instead of
  asserting projection-frame/situated-assertion identity.
- Two consecutive implementation slices fail to reduce private-surface
  leakage or string-based boundary code.
