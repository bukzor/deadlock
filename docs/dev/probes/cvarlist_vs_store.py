"""Compare an engine `cvarlist` capture with the store's TSVs (6860).

usage (WSL, repo root): python docs/dev/probes/cvarlist_vs_store.py LOG

LOG is a console log from `bin/cvarlist-capture`. Prints: per-DLL coverage,
the classes of non-`developmentonly` declarations the listing omits, which
store flag each printed flag word tracks, whether help matches after the
listing's normalization, and printed values against the store's defaults.
Cited by docs/dev/game-runtime.kb/cvarlist-capture.md.
"""

import collections
import csv
import re
import sys
from pathlib import Path

PREFIX = re.compile(r"^\d\d/\d\d \d\d:\d\d:\d\d (\[[^]]*\] )?")
ROW = re.compile(r"^(\S+) +: (.*?) *: (.*?) *: (.*)$")


def listing(path):
    """{name: (value, {flag words}, help)} from the `cvar list` block."""
    text = Path(path).read_text(encoding="utf-8-sig").replace("\r", "")
    lines = [PREFIX.sub("", line) for line in text.split("\n")]
    start = lines.index("cvar list") + 2
    out = {}
    for line in lines[start:]:
        if line.startswith("--------------"):
            break
        m = ROW.match(line)
        assert m, f"unparsed listing line: {line!r}"
        name, value, flags, help_ = m.groups()
        out[name] = (value, {f.strip() for f in flags.split(",") if f.strip()}, help_)
    return out


def store():
    """{name: [row, ...]} over convars.tsv and concommands.tsv."""
    out = collections.defaultdict(list)
    for kind in ("convars", "concommands"):
        with open(f"data/dlls/{kind}.tsv", newline="") as f:
            for row in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
                row["kind"] = kind
                row["flagset"] = set(row["flags"].split())
                out[row["name"]].append(row)
    return out


def coverage(got, decls):
    print(f"listed {len(got)}; listed but not in the store:", [n for n in got if n not in decls])
    alldev = [n for n in got if all("developmentonly" in r["flagset"] for r in decls[n])]
    print("listed, every declaration developmentonly:", alldev)
    hidden = [n for n in got if any("hidden" in r["flagset"] for r in decls[n])]
    print("listed, some declaration hidden:", hidden)
    print(f"{'dll':24} {'decls':>6} {'listed':>6} {'dev':>6} {'other unlisted':>14}")
    per = collections.defaultdict(collections.Counter)
    for name, rows in decls.items():
        for r in rows:
            c = per[r["dll"]]
            dev = "developmentonly" in r["flagset"]
            c["decls"] += 1
            c["listed"] += name in got
            c["dev"] += dev
            c["other"] += not dev and name not in got
    for dll, c in sorted(per.items(), key=lambda kv: -kv[1]["decls"]):
        print(f"{dll:24} {c['decls']:6} {c['listed']:6} {c['dev']:6} {c['other']:14}")
    print("unlisted, not developmentonly:")
    for name, rows in sorted(decls.items()):
        for r in rows:
            if name not in got and "developmentonly" not in r["flagset"]:
                cls = "hidden" if "hidden" in r["flagset"] else "minus" if name[0] == "-" else "?"
                print(f"  {cls:7} {r['dll']:22} {name:52} {r['flags']}")


def flags(got, decls):
    print("printed word -> store flags on every listed name carrying it:")
    for word in sorted({w for _, ws, _ in got.values() for w in ws}):
        names = [n for n in got if word in got[n][1]]
        common = set.intersection(*(set().union(*(r["flagset"] for r in decls[n])) for n in names))
        dlls = collections.Counter(r["dll"] for n in names for r in decls[n])
        print(f"  {word:22} n={len(names):5} always={sorted(common)} dlls={dict(dlls.most_common(2))}")
    shown = {f for n in got for r in decls[n] for f in r["flagset"]}
    printed = collections.defaultdict(collections.Counter)
    for n in got:
        for f in set().union(*(r["flagset"] for r in decls[n])):
            printed[f].update(got[n][1])
    for f in sorted(shown):
        top = printed[f].most_common(1)[0]
        print(f"  store {f:26} on {sum(1 for n in got if any(f in r['flagset'] for r in decls[n])):5}; commonest word {top}")


def norm(text):
    return text.replace("\\n", " ").replace("\\t", " ").replace('"', "'")


def helps(got, decls):
    raw = norm_ = 0
    for name, (_, _, h) in got.items():
        cands = {"" if r["help"] == r"\N" else r["help"] for r in decls[name]}
        raw += h in cands
        norm_ += h in {norm(c) for c in cands}
        if h not in {norm(c) for c in cands}:
            print(f"  help mismatch {name}: {h!r} vs {sorted(cands)}")
    print(f"help equal: raw {raw}/{len(got)}, after \\n,\\t->space and \"->' {norm_}/{len(got)}")


def same_value(printed, default, type_):
    if default in (printed, r"\N") or (printed == "0" and default == "" and type_ == "string"):
        return True
    try:
        a, b = [float(x) for x in printed.split()], [float(x) for x in default.split()]
    except ValueError:
        return False
    return a == b or (type_ == "color" and a == b[:3])


def values(got, decls):
    eq = collections.Counter()
    for name, (value, _, _) in sorted(got.items()):
        rows = [r for r in decls[name] if r["kind"] == "convars"]
        if not rows:
            eq["cmd" if value == "cmd" else "?"] += 1
            continue
        if any(same_value(value, r["default"], r["type"]) for r in rows):
            eq["equal"] += 1
        else:
            eq["differs"] += 1
            print(f"  differs {name:50} printed {value[:40]!r} default {sorted({r['default'] for r in rows})}")
    print("values:", dict(eq))


def main(path):
    got, decls = listing(path), store()
    for part in (coverage, flags, helps, values):
        print(f"== {part.__name__}")
        part(got, decls)


if __name__ == "__main__":
    main(sys.argv[1])
