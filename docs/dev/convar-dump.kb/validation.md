# Checks that keep the dump honest

Any dumper that reads engine memory can read garbage after a patch. Trust comes
from checks that fail loudly, not from the dumper's author.

> [!TODO] All of these fail the dump (non-zero exit, no output written):

- **Shape:** `server.dll` yields exactly two multi-block strides, equal to the
  pinned ones (a check target of its own, `capture-approach.kb/queue-shape-scan.md`);
  every DLL has at most one queue of each kind at those strides; every name and help
  pointer lands inside the DLL and is a NUL-terminated printable string; every
  entry's trailing ref lands in the DLL's writable sections; type is a known
  `EConVarType`; has-default / min / max bytes are 0 or 1.
- **Anchors:** names known by other means arrive in the right queue, with the
  right flags — `bot_kick_all` a command (run in-game), `citadel_bot_kick` a
  `developmentonly` command, `citadel_lane_swap_available_duration_prematch` a
  `replicated cheat` convar, `find` a tier0 command. These also decide which
  stride is which. (The first three pass on 6848, `find` on 6851.)
- **Coverage:** every DLL in scope (`dll-coverage.md`) is scanned or on the
  exclusion list; `engine2`, `client` and `server` each yield both queues.
- **Oracle:** the non-`developmentonly` entries equal the engine's own
  `cvarlist` (`capture-approach.kb/runtime-cvarlist.md`) for the same build, on
  name, flags, and default. The only check that catches a DLL whose queue the
  scan missed outright. Too slow for every build, run on demand.
- **Registry readback:** for `server` and `client`, every queue entry is a
  registration call, and each name declared once decodes, from the queue, to
  the type, flags (minus the per-DLL flag) and default tier0's own registry
  holds (`capture-approach.kb/icvar-hook.md`; `scratchpad/hook_probe3.py` does
  the readback). Checks the value decoding against the engine, not against our
  reading of the SDK. Run on demand, and on each new build.
