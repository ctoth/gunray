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

## 2026-04-17

**GOAL**: Third pass. Q critique: previous README was a thesis defense, not a README. Cut virtue claims, collapse 5-example showcase to one, fix "two engines / three evaluators" contradiction, position without comparing, spoil the Donald Nute pun, move internals to `ARCHITECTURE.md`, papers to `CITATIONS.md`.

**DONE**:
- `README.md` rewritten — 212 lines (was 504). Opens with Nute gloss + tagline, Tweety hook, Nixon/UNDECIDED as the selling point, pip-from-git install, three-evaluator dispatcher, `explain()` with real Mermaid (reviewer waiver), `SAFE`/`NEMO`, tests, links to the two new docs.
- `ARCHITECTURE.md` — 200 lines. Subagent-written. DeLP pipeline at definition granularity, preference composition, strict-only fast path, closure, out-of-contract, module layout, "exists because X was broken once" pitfalls.
- `CITATIONS.md` — 113 lines. Subagent-written. Classified by `src/` grep: load-bearing (García 04, Simari 92, Morris 20, KLM, Apt-Blair-Walker, Nemo), contextual (Darwiche, Goldszmidt, Diller, Deagustini, Bozzato, Maher), out-of-contract (Antoniou 07).
- Caught and fixed a story-break: original `explain()` snippet pointed at the Nixon diamond, where `mark(tree)=D` and `explain` says "is NO" — contradicts the `UNDECIDED` narrative two paragraphs above. Switched to `flies(opus)` on the Tweety theory: clean defeater chain, `D` mark, "defeated by… strictly more specific" prose. Verified via `uv run python -c`.

**FILES**:
- `README.md` — rewritten
- `ARCHITECTURE.md` — new
- `CITATIONS.md` — new

**STUCK**: Not stuck. Waiting for Q review before commit.

**NEXT**: Q reads all three. If green → one commit per file or one bundled commit per Q's call. Install path uses `git+https://github.com/ctoth/gunray.git` — honest, since package is not on PyPI.
