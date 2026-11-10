#!/bin/bash
# The files one side's capture (<side>.log) reads, besides its DLLs: each one's
# sha256 (gitignored, like the captures). redo-always + redo-stamp: it rehashes
# every run, and the capture relaunches only when a hash changes. A launch
# rewrites most of these files with the same content (new mtime), so mtimes
# can't serve. The files are read, never written.
# Both sides: the install's gameinfo.gi (its ConVars block). The server reads
# no settings file. The client also reads the Steam account's saved settings,
# under <Steam>/userdata/<account>/1422450/: the archived values in
# local/cfg/machine_convars.vcfg, the per_user ones in remote/user_convars.vcfg
# (loaded through Steam Cloud) and its local copy, local/cfg/
# user_convars_0_slot0.vcfg (written back each launch), video settings in
# local/cfg/video.txt, and the install's cfg/autoexec.cfg (not what it execs).
# docs/dev/game-runtime.kb/cvarlist-capture.md
# redo runs this with cwd = data/cvarlist/; $2 = the side; the repo root is two up.
set -euo pipefail

redo-always
citadel=$(../../.venv/bin/python -m deadlock.paths citadel_dir)
files=("$citadel/gameinfo.gi")
case "$2" in
  server) ;;
  client)
    # The Steam root holds the install's library (<Steam>/steamapps/common/
    # Deadlock) and userdata/; exactly one account there has played Deadlock.
    steam=$(readlink -f "$citadel/../../../../..")
    mapfile -t users < <(find "$steam/userdata" -mindepth 2 -maxdepth 2 -name 1422450)
    if (( ${#users[@]} != 1 )); then
      echo "want one $steam/userdata/*/1422450, found ${#users[@]}" >&2; exit 1
    fi
    files+=("$citadel/cfg/autoexec.cfg"
      "${users[0]}/local/cfg/"{machine_convars.vcfg,user_convars_0_slot0.vcfg,video.txt}
      "${users[0]}/remote/user_convars.vcfg") ;;
  *)
    echo "no such side: $2 (server or client)" >&2; exit 1 ;;
esac

sha256sum -- "${files[@]}" >"$3"
redo-stamp <"$3"
