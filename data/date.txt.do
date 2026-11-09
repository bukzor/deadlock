#!/bin/bash
# Today's date: a clock for targets that should refresh at most daily.
# redo-always reruns this on every build; redo-stamp invalidates dependents
# only when the date rolls over. Depend on it via `redo-ifchange data/date.txt`.
# redo runs this with cwd = data/.
set -euo pipefail
redo-always
if [[ "${REDO:-}" ]]; then exec > >(tee >(redo-stamp)); fi

date -I
