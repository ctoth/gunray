# E2 — Legal reasoning examples — report

## Files

- `examples/innocent_until_proven_guilty.py` — zero-arity
  presumption (`innocent -< true`) plus evidence and confession
  defeasible rules plus a coerced-confession blocking defeater.
  Uses `superiority=[("d1","df1")]` so the evidence rule is
  not blocked by coercion.
- `examples/gdpr_lawful_basis.py` — strict
  `processing_lawful :- lawful_basis` over two defeasible paths
  (consent, contractual necessity). `consent_given` is defeasibly
  supported so withdrawal can undermine it. Explicit
  `superiority=[("d2","d0")]` — withdrawal beats consent.

## Gate

- pytest: 200 passed, 293 skipped, 2 deselected.
- conformance (GunrayConformanceEvaluator): 284 passed,
  9 skipped, 2 deselected.
- pyright: 0 errors.
- ruff check + ruff format --check: clean.

## Commit

(see below — filled after `git commit`)

## Abbreviated stdout

innocent_until_proven_guilty.py:

```
Scenario A — evidence_against only.
  answer(innocent) = NO
Scenario B — evidence + confession + coerced_confession.
  answer(innocent) = NO
```

gdpr_lawful_basis.py:

```
Scenario A — consent signed then withdrawn.
  answer(lawful_basis(acme)) = UNDECIDED
Scenario B — same + contractual_necessity(acme).
  answer(lawful_basis(acme)) = YES
```
