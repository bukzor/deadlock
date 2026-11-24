#!/bin/bash
# Throughput layout: P background whisper processes at T threads each, every
# one transcribing the same batch REPS times (asr-batch.py), while a foreground
# pytest runs once. Prints the layout's wall, clips/hour, the pytest wall, and
# the 1-minute load average sampled after pytest.
#   docs/dev/probes/asr-layout.sh P T REPS MODEL CLIPDIR LISTFILE [WHISPER_ARG...]
# Run from the repo root.
set -euo pipefail
procs=$1 threads=$2 reps=$3 model=$4 clipdir=$5 list=$6
shift 6
extra=("$@")
out=$(mktemp -d "trash/vo-transcripts/004/layout.XXXX")
clips=$(wc -l <"$list")

worker() {
  for r in $(seq "$reps"); do
    nice -n 19 python3 docs/dev/probes/asr-batch.py "$model" "$clipdir" "$list" \
      "$out/p$1.r$r" -l ja -t "$threads" "${extra[@]}" >"$out/p$1.r$r.tsv"
  done
}

start=$(date +%s.%N)
for p in $(seq "$procs"); do worker "$p" & done
sleep 5
/usr/bin/time -f '%e' -o "$out/pytest.time" ./bin/shell pytest -q -p no:cacheprovider >/dev/null 2>&1
load=$(cut -d' ' -f1 /proc/loadavg)
wait
end=$(date +%s.%N)
python3 - "$start" "$end" "$procs" "$reps" "$clips" "$(cat "$out/pytest.time")" "$load" <<'PY'
import sys
start, end, procs, reps, clips, pytest, load = sys.argv[1:]
wall = float(end) - float(start)
n = int(procs) * int(reps) * int(clips)
print(f"{n} clips in {wall:.0f} s = {n * 3600 / wall:.0f} clips/h; pytest {pytest} s; load1 {load}")
PY
