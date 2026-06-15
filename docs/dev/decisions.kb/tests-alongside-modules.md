---
status: accepted
date: "2026-06-15"
---

# Tests alongside modules, doctest enabled

Unit tests live next to their module as `{module}_test.py` (e.g.
`binary.py` ↔ `binary_test.py`), using `Describe*/When*` classes and `it_*`
methods. Doctests run automatically (`--doctest-modules`), and `pytest` scans
both `src/` and `tests/`.

## Why

- Co-location keeps a module and its spec together and makes the test name read
  as a specification.
- Doctests double as verified documentation for small, pure helpers
  (e.g. `BinaryReader.cstring`), so examples can't rot.
- `tests/` is reserved for integration tests that exercise the real game
  install rather than a single module.

## Discipline

Observe every new assertion fail at least once (mutate the source, see red,
revert). A test that has only ever passed proves nothing. No `-> None` on test
methods; pyright infers them.
