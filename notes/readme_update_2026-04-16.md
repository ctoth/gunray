# README + CLAUDE.md update — 2026-04-16

## GOAL
Update README to match current code truth after the full workstream
(P0-P4) landed. Q also flagged that CLAUDE.md "may/does need updates" —
but there is no project-level `CLAUDE.md` at repo root or anywhere under
the repo (verified via Glob `**/CLAUDE.md`, empty result). Q likely wants
a project-level one created; needs confirmation before writing.

## DONE (observations only)
- Read `README.md` (226 lines) and repo top-level.
- Confirmed no project CLAUDE.md exists.
- Read `reviews/2026-04-16-full-review/SUMMARY.md` and
  `workstream/README.md` + `EXIT_CRITERIA.md`.
- Read `src/gunray/__init__.py`, `schema.py`, `errors.py`, and the
  relevant section of `trace.py`.

## CURRENT README vs CURRENT CODE — gaps identified
1. **README omits `NegationSemantics`** entirely. `schema.py:65-79` now
   defines `SAFE` and `NEMO` with a real Nemo 2024 citation; exported
   from `gunray`. README still silently describes Nemo behavior via
   conftest hand-wave.
2. **README omits trace upgrade.** `trace.DefeasibleTrace` now carries
   `arguments`, `trees`, `markings` + helpers `tree_for`,
   `marking_for`, `arguments_for_conclusion` (trace.py:129-146). README
   "Traces" section is still pre-upgrade wording.
3. **README does not mention `ContradictoryStrictTheoryError`** —
   errors.py:42 added by P1-T1; the strict-only path now enforces Π
   consistency.
4. **README import claim works** — `__init__.py` now exports
   `GeneralizedSpecificity`, `SuperiorityPreference`,
   `CompositePreference`. The README's longer example is correct.
5. **Conformance numbers** — README does not give numbers. SUMMARY says
   282/0/10/3. P4-T2 was supposed to re-activate
   `spindle_racket_query_long_chain`; need to verify current numbers
   before quoting any.
6. **"Where things live"** list is missing: `answer.py`, `arguments.py`,
   `dialectic.py`, `disagreement.py`, `errors.py`, `preference.py`,
   `schema.py`, `types.py`, `_internal.py`, `stratify.py`,
   `relation.py`, `compiled.py`, `parser.py` — post-refactor the
   surface is much bigger than the six files currently listed.
7. **Frozen dataclasses** — Rule/DefeasibleTheory are now
   `frozen=True, slots=True` with `__post_init__` validation; worth a
   mention so callers know construction can raise.
8. **Schema validation** — superiority pairs referencing unknown rule
   ids now raise at construction (schema.py:116-127).

## NOT YET DONE
- Haven't run tests to verify current numbers (139+ unit, 282+
  conformance).
- Haven't inspected `defeasible.py` to confirm the strict-only fast
  path behaviour mentioned by README paragraph 2 is still accurate.
- Haven't looked at `papers/` contents to understand what citations
  should appear in README.
- Haven't drafted the README rewrite or a project CLAUDE.md.

## BLOCKER
Need Q's answer on: **create a project-level `CLAUDE.md`?** and what it
should cover (principles, protocol notes, test commands, pointers into
`reviews/`). Plus confirmation of README scope: "total rewrite vs
targeted patch".

## NEXT
1. Report current state to Q with the gap list above.
2. Await scope confirmation (rewrite vs patch, and CLAUDE.md
   create-or-skip).
3. Then run the suite to capture live numbers, and proceed.

## FILES touched this session
- `README.md` — full rewrite. New sections: "What Gunray implements",
  "What Gunray does *not* implement", "Negation semantics", "Input
  types are frozen and validated", expanded trace section with
  `arguments`/`tree_for`/`marking_for`/`arguments_for_conclusion`,
  expanded "Where things live" list covering all 20 source files,
  "Citations" section. Qualitative (no test numbers quoted).
- `CLAUDE.md` — new file, project-level. Covers: what this repo is,
  where truth lives (papers + reviews + notes), core commands, the
  three out-of-contract fixture families, SAFE vs NEMO, gotchas that
  bit prior agents, style/tooling, and "when in doubt ask Q".

## STATUS
Done, pending Q review. No tests run — Q asked for qualitative so no
numbers are in the README to verify. Static analysis not run on the
two markdown files (ruff/pyright don't touch them).
