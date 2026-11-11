# Where it runs: Windows Python, driven from WSL

The DLLs are win64 and must be loaded into a Windows process. The host needs
Windows `uv` on its `PATH` (0.11.26, x86_64-pc-windows-msvc, here), callable
from WSL as `uv.exe` (run from `/mnt/c`: `cmd.exe` can't start in a UNC
cwd). `ctypes` covers `LoadLibraryExW`, `GetProcAddress`,
`ReadProcessMemory` on our own process (a bad pointer guess fails the read
instead of crashing), so no compiler is needed.

On an access violation, Windows Python writes `python_<date>_accessviolation.mdmp`
into its cwd — run it from a scratch directory, not the repo root.

DLL search: add `game/bin/win64` and `game/citadel/bin/win64` with kernel32's
`AddDllDirectory` (through `ctypes.CDLL`, not `os.add_dll_directory`, so pyright
checks `dllscan.win32` off Windows); the install is only read, never written.

`python -m dllscan` prints one document to stdout; the WSL side owns
everything after that (`output-views.md`). It is stdlib-only, so the Windows
side needs no environment of its own.

`bin/winpy` is the one entry point: the pinned interpreter, `src/` on
`PYTHONPATH` via `WSLENV`, stdin
from `/dev/null` (`python.exe` reads its inherited stdin, so under redo it would
eat the caller's), cwd the scratch dir `trash/winpy/`, a timeout (exit 124). A
host without `uv.exe` fails the build loudly: `all.do` never skips the DLL
facets.

The interpreter is part of the scan's input: Python preloads modules,
`vcruntime140.dll` among them, which the game DLLs then bind to instead of
the install's (so `load.tsv` never lists it), and its directory comes first
in the DLL search. The game's own loads depend on it too:
`rendersystemvulkan` loads `rendersystemdx11` (a name in its strings, not
an import) under the install manager's Python 3.14.4 and not under uv's
3.14.4, every time, with identical preloaded modules (6860; cause not
found). So `bin/winpy` pins one exact uv-managed CPython
(`PYTHON`, `cpython-3.14.4-windows-x86_64-none`), which Windows `uv`
installs on first use and reproduces on any host. The pin lives in
`bin/winpy`, which every facet depends on, so bumping it rebuilds them all.
Asserting the version of whatever `python.exe` is on `PATH` would only
detect drift: the Python install manager's copy updates in place. What
would change this: a scan whose output no longer depends on the interpreter.
