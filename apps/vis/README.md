# apps/vis

A browser view of the game data in `data/`: pick a hero and an ability to see
its damage over time as a bar chart (height is the damage, the left edge the
trigger, the right edge the land), the DPS measures with how to check each
in-game, and the model's caveats.

- `server/`: Python, its own uv project. It reads `data/` through the root
  `deadlock` package and answers queries as JSONL.
- `client/`: Vite, React and TypeScript, a pnpm workspace.

The design, including the protocol, is
[`docs/dev/decisions.kb/vis-app.md`](../../docs/dev/decisions.kb/vis-app.md);
the calls made on the way are in [`docs/dev/claims.md`](docs/dev/claims.md).

## Run it

```bash
apps/vis/bin/serve            # PORT=5174 API_PORT=8789 apps/vis/bin/serve for other ports
```

One command, the live loop: it installs the client's packages when the
lockfile is newer, then runs Vite (hot reload) and `vis-server serve
--reload` (restarts on a change to the server or `deadlock` sources), and
prints the one URL to open: <http://localhost:5173/>, which proxies `/api` to
the server on :8788. From WSL2, that URL opens in a Windows browser too.
Ctrl-C stops both. It refuses a port that is already taken. The server reads
`data/`, built by `redo` at the repo root; set `DEADLOCK_DATA_DIR` to read
another checkout's.

## Develop it

`bin/serve` is the development loop. To serve the built client from the one
Python process instead (no reload):

```bash
(cd apps/vis/client && pnpm run build)
(cd apps/vis/server && uv run vis-server serve)   # client and /api on :8787
```

To run the halves yourself: `uv run vis-server serve [--reload]` for the API,
and `pnpm exec vite` for the client, which proxies `/api` to `$VIS_API`
(default `http://localhost:8787`).

Checks:

```bash
(cd apps/vis/server && uv run pytest && uv run basedpyright)
(cd apps/vis/client && pnpm exec tsc --noEmit && pnpm exec vitest run)
```

## Query it from the shell

`vis-server query NAME k=v ...` prints the same lines as `GET /api/NAME?k=v`,
one JSON object each, so `jq` reads them. From `apps/vis/server`:

```bash
uv run vis-server query heroes | jq -r .hero
uv run vis-server query abilities hero=hero_haze | jq -c 'select(.kind)'
uv run vis-server query timeline hero=hero_haze ability=ability_sleep_dagger horizon=20 |
  jq -c 'select(.kind == "measure") | {name, value}'
curl -s 'http://localhost:8787/api/timeline?hero=hero_haze&ability=citadel_weapon_haze_set' |
  jq -s 'map(select(.kind == "hit")) | length'
curl -s http://localhost:8787/api | jq -c .      # the queries and their parameters
```

A bad request answers one `{"error": ...}` line: HTTP 400, or exit status 2
with the line on stderr.
