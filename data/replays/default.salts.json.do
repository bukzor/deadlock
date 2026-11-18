#!/bin/bash
# Replay salts for public match $2, from deadlock-api.com
# (GET /v1/matches/{match_id}/salts): cluster_id, replay_salt, metadata_salt,
# and the Valve replay-CDN URLs they form, e.g.
# http://replay{cluster_id}.valve.net/1422450/{match_id}_{replay_salt}.dem.bz2
# Salts never change once known, so there is no clock dependency.
# disable_steam=true: only matches whose salts the API already holds (most
# recent public matches); its Steam fallback is rate-limited to 3 req/h per IP.
# jq -e fails the build when the record has no demo_url.
# redo runs this with cwd = data/replays/.
set -euo pipefail
if [[ "${REDO:-}" ]]; then exec > >(tee >(redo-stamp)); fi

curl -fsS --retry 3 "https://api.deadlock-api.com/v1/matches/$2/salts?disable_steam=true" |
  jq -e 'select(.demo_url != null)' \
;
