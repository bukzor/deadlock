# Host: Alpine/musl with glibc compat

This box is **Alpine Linux 3.23, musl libc, x86_64**, under WSL2.

Relevant quirks:

- **glibc binaries run** despite musl, because `gcompat` and the glibc loader
  (`/lib64/ld-linux-x86-64.so.2`) are installed. This is why the VRF glibc CLI
  runs without a container.
- **No init system** in the usual sense: boot runs `runsvdir /etc/service`
  (daemontools-style, per `/etc/wsl.conf`). There's no `systemctl`/`rc-service`;
  services are `sv`-managed runit dirs under `/etc/service`.
- Docker is installed but the daemon is not running (and Docker Desktop
  integration is dead). We don't use it — see
  `../decisions.kb/vrf-runs-natively-no-docker.md`.

Implication: prefer host-native execution. If a native musl build is ever
needed, Alpine has `dotnet10-sdk` in its repos.

## Disk: the Linux disk lives on C:

`/` is a growable virtual disk, `.../AlpineWSL_.../LocalState/ext4.vhdx`
on the Windows C: drive, so `df /` overstates the room: the real limit is `df /mnt/c`. Filling C:
crashes WSL and everything in it (2026-11-24, a 26 GB VPK explode), and
deleting files inside does not shrink the vhdx back. `localhost.env`
sets `DEADLOCK_FREE_SPACE_DIR=/mnt/c` so bulk writes check C:
(`../decisions.kb/explode-vpks-to-plain-files.md`).
