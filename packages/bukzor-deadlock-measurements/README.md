# bukzor-deadlock-measurements

Readings the owner records by hand from live sandbox runs, kept as data apart
from the code that checks and reports them.

- `records.py` -- the vocabulary: frozen keyword-only dataclasses whose only
  methods are derived properties. Both the data and the programs import it.
- `experiments/*.py` -- one module per experiment, hand-edited. Each imports
  only `records` and binds one `EXPERIMENT`; its docstring holds the setup and
  procedure. Scenarios are grouped under the dummy they ran against.
- `load.py`, `check.py`, `summary.py` -- collect the experiments, check their
  item lists against the game data, and print the summary table
  (`python -m bukzor_deadlock_measurements`).

`layering_test.py` holds both rules, so the data loads without the game
install. Why the readings are Python: the owner's ruling in
`docs/dev/decisions.kb/small-bukzor-prefixed-packages.md`.
