# bukzor-deadlock-measurements

Readings the owner records by hand from live sandbox runs, kept as data apart
from the code that loads them.

- `data/*.yaml` -- one file per experiment, hand-edited. Each starts with a
  `yaml-language-server` comment pointing at `data/readings.schema.json`, so an
  editor checks an edit as it is typed. Scenarios are grouped under the dummy
  they ran against.
- `src/bukzor_deadlock_measurements/` -- typed records, a loader that
  validates each file, and the summary table
  (`python -m bukzor_deadlock_measurements`).

Why `data/` is here and outside `src/`: the repo's own `data/` is generated
output (rebuilt by `redo`), and these readings are hand-authored
observations that cannot be regenerated. Outside `src/` keeps them out of the
import tree; the loader finds them relative to the package, so it reads them
from a checkout or editable install, not from a built wheel.

The schema is enforced two ways: by the editor, and by the loader's own
structural checks (no schema library is a dependency).
