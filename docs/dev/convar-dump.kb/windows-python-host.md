# Where it runs: Windows Python, driven from WSL

The DLLs are win64 and must be loaded into a Windows process. This box has
Windows Python 3.14.4 and `uv` 0.11.26 (x86_64-pc-windows-msvc) on the Windows
`PATH`, callable from WSL (`cmd.exe /c …`; `cmd.exe` can't start in a UNC cwd,
so `cd /mnt/c` first). `ctypes` covers `LoadLibraryExW`, `GetProcAddress`,
`ReadProcessMemory` on our own process (a bad pointer guess fails the read
instead of crashing), so no compiler is needed.

On an access violation, Windows Python writes `python_<date>_accessviolation.mdmp`
into its cwd — run it from a scratch directory, not the repo root.

DLL search: add `game/bin/win64` and `game/citadel/bin/win64` with
`os.add_dll_directory`; the install is only read, never written.

The script prints its dump to stdout; the WSL side owns everything after that
(`output-views.md`).
