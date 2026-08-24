#!/bin/bash
# Recompile one TSV view from the committed, flattened game data. Build-local,
# not committed: every view derives entirely from gamedata.flat/ (what each
# view shows is documented in its deadlock.<view> module docstring). The case
# table maps each view to its stdin source and extra sources; anything unlisted
# fails loudly rather than being silently captured by this default rule.
# redo runs this with cwd = data/gamedata.tsv/; the repo root is two levels up.
set -euo pipefail
if [[ "${REDO:-}" ]]; then exec > >(tee >(redo-stamp)); fi

root=$(cd ../.. && pwd)
py="$root/.venv/bin/python"
flat=../gamedata.flat/scripts

deps=()
case "$2" in
  heroes | levels)
    stdin=heroes; args=() ;;
  item_bonuses)
    stdin=abilities; args=() ;;
  abilities | weapons)
    stdin=heroes; args=("$flat/abilities.jsonl") ;;
  items)
    stdin=abilities; args=("$flat/generic_data.jsonl") ;;
  ability_upgrades)
    stdin=abilities; args=("$flat/heroes.jsonl")
    deps=("$root/src/deadlock/abilities.py") ;;
  *)
    echo "no such view: $2 (add it to default.tsv.do's table)" >&2; exit 1 ;;
esac

redo-ifchange \
  "$root/src/deadlock/$2.py" \
  "${deps[@]}" \
  "$flat/$stdin.jsonl" \
  "${args[@]}"

"$py" -m "deadlock.$2" "${args[@]}" <"$flat/$stdin.jsonl"
