"""Windows Python: time LoadLibrary of one DLL, then exit hard (no detach)."""
import ctypes, os, sys, time

GAME = r"C:\Program Files (x86)\Steam\steamapps\common\Deadlock\game"
BIN, CIT = GAME + r"\bin\win64", GAME + r"\citadel\bin\win64"
os.add_dll_directory(BIN); os.add_dll_directory(CIT)
name = sys.argv[1]
path = next(d + "\\" + name for d in (CIT, BIN) if os.path.exists(d + "\\" + name))
t = time.perf_counter()
ctypes.WinDLL(path)
print(f"{name}: LoadLibrary {time.perf_counter() - t:.2f}s", flush=True)
k32 = ctypes.WinDLL("kernel32")
k32.GetCurrentProcess.restype = ctypes.c_void_p
k32.TerminateProcess(ctypes.c_void_p(k32.GetCurrentProcess()), 0)
