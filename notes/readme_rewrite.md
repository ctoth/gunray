# README rewrite

## 2026-04-11

**GOAL**: Replace Codex-written README with a good one (not just de-slopped).

**DONE**:
- First pass (commit `2bbf8f5`, "Cut AI slop from README") removed bullet festivals and AI-tell headers but kept the same boring shape. Q called it out — the ask was a *good* README, not a de-slopped one.
- Second pass written to `README.md` (uncommitted). Opens with the Tweety/Opus defeasible example as a hook, then explains what defeasible logic buys you, then the conformance-suite framing, then install/usage/traces/layout.
- Both code examples verified by running them: Tweety example produces `flies(tweety)` and `~flies(opus)` in `model.sections["defeasibly"]`; Datalog example produces `path` closure `{(a,b),(b,c),(a,c)}`.

**FILES**:
- `README.md` — new draft on disk, not yet committed
- `src/gunray/__init__.py` — exports confirmed: `GunrayEvaluator`, `SemiNaiveEvaluator`, `DefeasibleEvaluator`, `TraceConfig`, trace types

**STUCK**: Not stuck. Waiting for Q to react to the new draft before committing.

**NEXT**: If Q approves → new commit (separate from `2bbf8f5`, not amend). If Q wants changes → iterate on disk.
