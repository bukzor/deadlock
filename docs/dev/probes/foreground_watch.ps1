# usage: powershell.exe -File foreground_watch.ps1 SECONDS
# Print, on each change, the foreground window (handle, pid, process, title),
# the user-idle time (GetLastInputInfo), and the visible deadlock.exe windows on
# this desktop (:min = minimized). Run beside a bin/cvarlist-capture launch.
param([double]$Seconds = 15)
Add-Type @"
using System; using System.Runtime.InteropServices; using System.Text;
public static class U {
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [StructLayout(LayoutKind.Sequential)] public struct LII { public uint cb; public uint t; }
  [DllImport("user32.dll")] public static extern bool GetLastInputInfo(ref LII i);
  public delegate bool EP(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EP f, IntPtr l);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
  public static string Wins(uint[] pids) { var sb = new StringBuilder();
    EnumWindows((h, l) => { uint p; GetWindowThreadProcessId(h, out p);
      if (Array.IndexOf(pids, p) >= 0 && IsWindowVisible(h)) sb.Append(" " + h + (IsIconic(h) ? ":min" : ":shown")); return true; }, IntPtr.Zero);
    return sb.ToString(); }
  public static uint Idle() { var i = new LII(); i.cb = 8; GetLastInputInfo(ref i); return (uint)Environment.TickCount - i.t; }
}
"@
$end = (Get-Date).AddSeconds($Seconds); $last = ""
while ((Get-Date) -lt $end) {
  $h = [U]::GetForegroundWindow(); $p = 0; [void][U]::GetWindowThreadProcessId($h, [ref]$p)
  $sb = New-Object Text.StringBuilder 256; [void][U]::GetWindowText($h, $sb, 256)
  $n = (Get-Process -Id $p -ErrorAction SilentlyContinue).ProcessName
  $dl = [uint32[]]@(Get-Process deadlock -ErrorAction SilentlyContinue | % Id)
  $cur = "$h $p $n '$sb' deadlock_windows=[" + [U]::Wins($dl) + " ]"
  if ($cur -ne $last) { "{0:HH:mm:ss.fff} idle={1}ms fg={2}" -f (Get-Date), [U]::Idle(), $cur; $last = $cur }
  Start-Sleep -Milliseconds 50
}
"{0:HH:mm:ss.fff} idle={1}ms end" -f (Get-Date), [U]::Idle()
