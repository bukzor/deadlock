# usage: powershell.exe -File on-hidden-desktop.ps1 EXE ARGS...
# Run EXE on a new desktop that is never shown, so none of its windows can take
# the foreground; wait, and exit with its exit code. Run from EXE's directory.
# docs/dev/game-runtime.kb/cvarlist-capture.md (Focus)
Add-Type @"
using System; using System.ComponentModel; using System.Runtime.InteropServices;
public static class D {
  [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
  static extern IntPtr CreateDesktop(string n, IntPtr d, IntPtr m, uint f, uint a, IntPtr s);
  [DllImport("user32.dll")] static extern bool CloseDesktop(IntPtr h);
  [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)] struct SI {
    public int cb; public string r; public string desk; public string title; public int x, y, w, h, cx, cy, fill, flags;
    public short show, r2; public IntPtr r3, i, o, e; }
  [StructLayout(LayoutKind.Sequential)] struct PI { public IntPtr hp, ht; public int pid, tid; }
  [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
  static extern bool CreateProcess(string app, string cmd, IntPtr pa, IntPtr ta, bool inh, uint f, IntPtr env, string cwd, ref SI si, out PI pi);
  [DllImport("kernel32.dll")] static extern uint WaitForSingleObject(IntPtr h, uint ms);
  [DllImport("kernel32.dll")] static extern bool GetExitCodeProcess(IntPtr h, out uint c);
  public static uint Run(string name, string line) {
    const uint GENERIC_ALL = 0x10000000, CREATE_NEW_CONSOLE = 0x10;
    IntPtr d = CreateDesktop(name, IntPtr.Zero, IntPtr.Zero, 0, GENERIC_ALL, IntPtr.Zero);
    if (d == IntPtr.Zero) throw new Win32Exception(Marshal.GetLastWin32Error(), "CreateDesktop");
    SI si = new SI(); si.cb = Marshal.SizeOf(typeof(SI)); si.desk = "WinSta0\\" + name;
    PI pi;
    if (!CreateProcess(null, line, IntPtr.Zero, IntPtr.Zero, false, CREATE_NEW_CONSOLE, IntPtr.Zero, null, ref si, out pi))
      throw new Win32Exception(Marshal.GetLastWin32Error(), "CreateProcess " + line);
    WaitForSingleObject(pi.hp, 0xFFFFFFFF); uint c; GetExitCodeProcess(pi.hp, out c); CloseDesktop(d); return c;
  }
}
"@
$args[0] = (Resolve-Path $args[0]).Path
$line = ($args | % { if ($_ -match '[\s"]') { '"' + ($_ -replace '"', '\"') + '"' } else { $_ } }) -join ' '
[Environment]::CurrentDirectory = (Get-Location).Path
exit [D]::Run("hidden-$PID", $line)
