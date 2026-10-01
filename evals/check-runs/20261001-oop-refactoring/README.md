# OOP refactoring verification

Baseline production code: `bbd0a8d`; plan commit: `d5a1cde`.
All checks use offline providers and temporary storage. No user library, secrets,
model settings or historical evaluation artifacts are modified.

## Baseline

- `baseline`: 854 passed, 1 explicitly opt-in live test skipped.
- `freeze-contracts`: first successful snapshot, retained unchanged.
- `freeze-contracts-v2`: 1 passed; tightened identity normalization so 64-character
  source hashes remain exact. `behavior-before-v2.json` is the comparison baseline.
- `tests/test_oop_contracts.py` freezes one TXT corpus, single/planned requests,
  planned streaming, follow-up resolution, missing scope, deletion/history and
  empty-library behavior. Provider responses are fixed by the recorded test fixture.
  Stored observations include chunks, sources, ranks, budgets, model payloads,
  event order, answer snapshots and nine schemas.
- Normalization excludes keys ending in `_seconds`, `seconds`, `created_at` and
  `updated_at`; generated 32-hex identities are consistently renamed. Timing is
  not compared and mocked outputs do not establish live quality or performance.

Every command has an append-only JSON/log pair containing the full metric inventory,
code hashes, command, duration, result counts and any failure output.

Implementation and final comparison remain pending.
