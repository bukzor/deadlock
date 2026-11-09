"""The Windows-side DLL scanner: loads a game DLL and dumps facets of it.

Stdlib only (`stdlib_only_test.py` enforces it) and 3.12-compatible, since it
runs under whatever `python.exe` the host has. Every module but `win32` is pure
over a `read(addr, n)` callable (`memory.Read`), so WSL pytest drives it with a
fake (`memory.Segments`).
"""
