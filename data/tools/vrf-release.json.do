#!/bin/bash
# The latest ValveResourceFormat release: version, publish date, and sha256 of
# the cli-linux-x64.zip asset. Rechecked at most daily (via date.txt);
# redo-stamp invalidates dependents only when the release actually changes.
# redo runs this with cwd = data/tools/.
set -euo pipefail
if [[ "${REDO:-}" ]]; then exec > >(tee >(redo-stamp)); fi

redo-ifchange ../date.txt

# jq -e: a digest that doesn't match the capture yields no output; fail on it
gh api repos/ValveResourceFormat/ValveResourceFormat/releases/latest |
  jq -e --arg asset cli-linux-x64.zip '
    (.assets | map(select(.name == $asset))) as [$zip] |
    {
      version: .tag_name,
      published_at,
      sha256: ($zip.digest | capture("^sha256:(?<hex>[0-9a-f]{64})$").hex)
    }
  ' \
;
