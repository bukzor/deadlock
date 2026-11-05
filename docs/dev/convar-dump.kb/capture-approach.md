# How to capture the registrations

Question: at which point in `registration-flow.md` do we read the convars, so
that the result is complete (dev-only included), deterministic, and the
version-specific knowledge we depend on is as small, and as self-checking, as
possible?

Leading answer: `capture-approach.kb/queue-shape-scan.md` — load each DLL and
find its reg-list queues by their data shape, with no code signatures and no
engine startup. The two entry strides were learned from `server.dll`'s
multi-block queues; the tool pins them, with a check that re-learns them, and
scans every DLL that imports tier0 (`dll-coverage.md`) at those strides, tier0
included, each DLL on its own (`output-views.md`). Prototyped on 6848 (strides, three DLLs; heads match
DumpSource2's signature-found ones, flags and help match upstream) and 6851
(all DLLs).

The queue is lossless: every one of `server.dll`'s 2008 `RegisterConVar` calls
on 6854 is a queue entry, duplicates included. The hook
(`capture-approach.kb/icvar-hook.md`) works (`Init` runs the replay) but adds no
declarations; it is the instrument for the engine's side, checking the derived
merged view and the value decoding against tier0's registry.

> [!QUESTION] Not closed until the value fields decode and the one owner-check
> exception in the scan is understood.

The candidates, chosen and declined alike, are in `capture-approach.kb/`.
