#!/bin/bash
# Compile one dense TSV view (every column, local only) from the local JSON
# game data; ../gamedata.tsv/ commits it split into a sparse view plus its
# defaults (see deadlock.sparse). What each view shows is documented in its
# deadlock.<view> module docstring. The case table maps each view to its stdin
# source and extra sources; anything unlisted fails loudly rather than being
# silently captured by this default rule.
# redo runs this with cwd = data/gamedata.dense.tsv/; the repo root is two levels up.
set -euo pipefail
if [[ "${REDO:-}" ]]; then exec > >(tee >(redo-stamp)); fi

root=$(cd ../.. && pwd)
py="$root/.venv/bin/python"
json=../gamedata.json/scripts

deps=()
case "$2" in
  heroes)
    stdin=heroes; args=("$("$py" -m deadlock.paths hero_names_loc)")
    deps=("$root/src/deadlock/loc.py") ;;
  levels)
    stdin=heroes; args=() ;;
  item_bonuses)
    stdin=abilities; args=() ;;
  abilities)
    stdin=heroes; args=("$json/abilities.json") ;;
  ability_profiles)
    stdin=heroes; args=("$json/abilities.json")
    deps=("$root/src/deadlock/abilities.py") ;;
  items)
    stdin=abilities; args=("$json/generic_data.json") ;;
  ability_upgrades)
    stdin=abilities; args=("$json/heroes.json")
    deps=("$root/src/deadlock/abilities.py") ;;
  *)
    echo "no such view: $2 (add it to default.tsv.do's table)" >&2; exit 1 ;;
esac

redo-ifchange \
  "$root/src/deadlock/$2.py" \
  "$root/src/deadlock/gamedata.py" \
  "$root/data/deadlock-version.json" \
  "${deps[@]}" \
  "$json/$stdin.json" \
  "${args[@]}"

"$py" -m "deadlock.$2" "${args[@]}" <"$json/$stdin.json"
