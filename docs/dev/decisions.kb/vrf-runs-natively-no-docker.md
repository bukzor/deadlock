---
status: accepted
date: "2026-06-15"
---

# Run Source2Viewer-CLI natively (no Docker)

`s2v.py` invokes the vendored `Source2Viewer-CLI` binary directly as a
subprocess. No container, no daemon.

## Why

The host is Alpine/musl, and VRF ships a **glibc** self-contained Linux build
(`cli-linux-x64`, interpreter `/lib64/ld-linux-x86-64.so.2`). Docker was
considered to provide glibc, but it was only ever a means to run the binary —
and it turned out unnecessary: `gcompat` and the glibc loader are already
installed, so the glibc binary runs natively (`--version` → `19.2.6339`, and
`--vpk_list` works against the real VPK).

Docker was rejected as added complexity: the daemon isn't running, there's no
init system (boot is `runsvdir /etc/service`), and Docker Desktop integration is
dead. None of that is worth fighting when the binary just runs.

## What would change this

If a future VRF release dropped the glibc build or required libs `gcompat` can't
satisfy, revisit: prefer a native musl build via Alpine's `dotnet10-sdk`
(`-r linux-musl-x64`) over reintroducing Docker.
