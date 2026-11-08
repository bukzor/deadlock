# probes

One-off experiment scripts, and their small results, that a knowledge base in
`../` cites as evidence. They are archived as they ran, so a cited run can be
re-read or repeated; they are not maintained, not tested, and never imported
by `src/`. A probe that grows into a tool moves into `src/` and gets tests.

What belongs: a script or result file that a KB sentence cites. A probe
nothing cites stays in `trash/`. Never add Valve data dumps (registry
readbacks, convar lists): regenerate them instead (`../decisions.kb/`).

Most are Windows Python with hardcoded stock-install paths, run by path from a
scratch cwd under `trash/`; siblings import each other by bare module name.
