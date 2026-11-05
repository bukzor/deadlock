# Recover registrations without running the DLLs (declined)

Disassemble or emulate (e.g. Unicorn) each static initializer and
constant-propagate the arguments into `SetupConVar`; or pair name/help strings
by their adjacency in `.rdata`.

Declined: values are built by code (`../registration-flow.md`), so this is a
partial x64 emulator plus Windows loader to reproduce what `LoadLibrary` does
for free. The string-adjacency shortcut yields names and help only — no flags,
no defaults — and drifts silently.
