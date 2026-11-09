"""The scanner's only Windows-only module: load a DLL into this process, list
the loaded modules, read this process's memory, and exit without teardown.

Importing it is safe anywhere: `kernel32` binds on first use. It goes through
`ctypes.CDLL` (x64 has one calling convention) and kernel32 itself, never the
stdlib's Windows-only names (`ctypes.WinDLL`, `os.add_dll_directory`): pyright
skips those as unreachable off Windows, so this module stays type-checked on
any platform. `_Kernel32` states each function's signature for pyright;
`_kernel32` sets the same on the `ctypes` side.
"""

import array
import ctypes
import sys
from collections.abc import Callable, Iterable
from ctypes import wintypes
from functools import cache
from types import SimpleNamespace
from typing import NoReturn, Protocol, cast

_SEARCH = 0x1000 | 0x100
"""`LoadLibraryExW` flags `LOAD_LIBRARY_SEARCH_DEFAULT_DIRS | _DLL_LOAD_DIR`:
the DLL's own dir, then the defaults, which include every `AddDllDirectory`
dir (what `ctypes.CDLL` passes)."""

_ADDRESSES = 1 << 64
_NAME_MAX = 32768
"""Longest Windows path, in UTF-16 units: a base name can't exceed it."""


class Win32Error(Exception):
    """A kernel32 call failed. args: the function, the Win32 error code, its input."""

    def __init__(self, function: str, code: int, arg: object = None) -> None:
        super().__init__(function, code, arg)
        self.function: str = function
        self.code: int = code


class _Kernel32(Protocol):
    # Handles and addresses are `int | None`: ctypes reads a NULL `c_void_p` as None.
    def AddDllDirectory(self, path: str, /) -> int | None: ...
    def LoadLibraryExW(self, path: str, file: None, flags: int, /) -> int | None: ...
    def GetCurrentProcess(self) -> int: ...
    def ReadProcessMemory(self, process: int, addr: int, buf: ctypes.Array[ctypes.c_char], n: int, got: object, /) -> int: ...
    def K32EnumProcessModules(self, process: int, out: ctypes.Array[ctypes.c_char], size: int, need: object, /) -> int: ...
    def K32GetModuleBaseNameW(self, process: int, module: int, out: ctypes.Array[ctypes.c_wchar], n: int, /) -> int: ...
    def TerminateProcess(self, process: int, code: int, /) -> int: ...


@cache
def _kernel32() -> _Kernel32:
    k32 = ctypes.CDLL("kernel32", use_last_error=True)
    ptr, size, ok, dword = ctypes.c_void_p, ctypes.c_size_t, wintypes.BOOL, wintypes.DWORD
    signatures: dict[str, tuple[type, tuple[type, ...]]] = {
        "AddDllDirectory": (ptr, (wintypes.LPCWSTR,)),
        "LoadLibraryExW": (ptr, (wintypes.LPCWSTR, ptr, dword)),
        "GetCurrentProcess": (ptr, ()),
        "ReadProcessMemory": (ok, (ptr, ptr, ptr, size, ctypes.POINTER(size))),
        "K32EnumProcessModules": (ok, (ptr, ptr, dword, ctypes.POINTER(dword))),
        "K32GetModuleBaseNameW": (dword, (ptr, ptr, wintypes.LPWSTR, dword)),
        "TerminateProcess": (ok, (ptr, wintypes.UINT)),
    }
    functions: dict[str, object] = {}
    for name, (restype, argtypes) in signatures.items():
        fn = functions[name] = k32[name]  # a new function object per `[name]`
        fn.restype, fn.argtypes = restype, argtypes
    return cast(_Kernel32, cast(object, SimpleNamespace(**functions)))


def _last_error() -> int:
    """The Win32 error `ctypes` saved after this thread's last kernel32 call.
    Reached by `getattr`: the stubs declare `ctypes.get_last_error` on Windows only."""
    return cast(Callable[[], int], getattr(ctypes, "get_last_error"))()


def add_dll_directories(dirs: Iterable[str]) -> None:
    """Add each Windows-form dir to this process's DLL search path, for good."""
    for path in dirs:
        if not _kernel32().AddDllDirectory(path):
            raise Win32Error("AddDllDirectory", _last_error(), path)


def load_library(path: str) -> int:
    """Load the DLL at the Windows-form `path`; its base address."""
    base = _kernel32().LoadLibraryExW(path, None, _SEARCH)
    if not base:
        raise Win32Error("LoadLibraryExW", _last_error(), path)
    return base


def module_names() -> list[str]:
    """Every module this process holds, as lowercased basenames, sorted."""
    k32 = _kernel32()
    process = k32.GetCurrentProcess()
    out = ctypes.create_string_buffer(0)
    need = wintypes.DWORD()
    while need.value >= len(out):
        out = ctypes.create_string_buffer(need.value + 0x200)
        if not k32.K32EnumProcessModules(process, out, len(out), ctypes.byref(need)):
            raise Win32Error("K32EnumProcessModules", _last_error())
    handles = array.array("Q", out.raw[: need.value])
    return sorted(_base_name(process, handle).lower() for handle in handles)


def _base_name(process: int, module: int) -> str:
    out = ctypes.create_unicode_buffer(_NAME_MAX)
    n = _kernel32().K32GetModuleBaseNameW(process, module, out, len(out))
    if not n:
        raise Win32Error("K32GetModuleBaseNameW", _last_error(), module)
    return ctypes.wstring_at(out, n)


def read(addr: int, n: int) -> bytes | None:
    """This process's `n` bytes at `addr`, or None if any is unreadable: a
    `memory.Read`. A bad address fails the read; it never faults.

    >>> read(-1, 8) is None, read(_ADDRESSES - 4, 8) is None
    (True, True)
    """
    if addr < 0 or addr + n > _ADDRESSES:
        return None
    k32 = _kernel32()
    out = ctypes.create_string_buffer(n)
    got = ctypes.c_size_t()
    if not k32.ReadProcessMemory(k32.GetCurrentProcess(), addr, out, n, ctypes.byref(got)) or got.value != n:
        return None
    return out.raw


def hard_exit(code: int) -> NoReturn:
    """Flush stdout and stderr, then end this process with `code` at once,
    skipping DLL detach and static destructors (they can hang)."""
    for stream in sys.stdout, sys.stderr:
        print(end="", file=stream, flush=True)
    k32 = _kernel32()
    ok = k32.TerminateProcess(k32.GetCurrentProcess(), code)
    raise AssertionError("TerminateProcess returned", ok, _last_error())
