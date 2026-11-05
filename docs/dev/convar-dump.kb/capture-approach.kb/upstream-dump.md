# Use DumpSource2's output (declined as source; usable as a second opinion)

Run `DumpSource2-DEADLOCK` (CI artifacts only, no releases), or fetch
SteamTracking/GameTracking-Deadlock's `DumpSource2/convars.txt` and
`commands.txt`, whose commit messages start with the build number.

Declined: the user doesn't trust a special-purpose third-party dumper as the
source (2026-11-05). Not abandonware, for the record: pushed 2026-10-23, and
GameTracking used it on 6848 the day after release.

Still useful as a second opinion: diffing our dump against GameTracking's for the
same build should be empty modulo formatting.
