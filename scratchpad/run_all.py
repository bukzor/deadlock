"""Windows-side driver: one scan process per DLL, bounded time, results streamed."""
import concurrent.futures as cf, json, os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
TIMEOUT = 900
dlls = [l.strip() for l in open(os.path.join(HERE, "dlls.txt")) if l.strip()]
def run(name):
    t = time.monotonic()
    try:
        r = subprocess.run([sys.executable, os.path.join(HERE, "fixed_stride_scan.py"), name],
                           capture_output=True, text=True, timeout=TIMEOUT, cwd=HERE)
        out = r.stdout.strip()
        rec = json.loads(out) if r.returncode == 0 and out else dict(dll=name, rc=r.returncode, err=r.stderr.strip()[-400:])
    except subprocess.TimeoutExpired:
        rec = dict(dll=name, timeout=TIMEOUT)
    rec["secs"] = round(time.monotonic() - t, 1)
    return rec
with cf.ThreadPoolExecutor(max(2, os.cpu_count() // 2)) as ex, open(os.path.join(HERE, "results.jsonl"), "w") as f:
    for fut in cf.as_completed([ex.submit(run, d) for d in dlls]):
        line = json.dumps(fut.result()); f.write(line + "\n"); f.flush(); print(line[:160], flush=True)
