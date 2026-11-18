# pyright: basic
# (a claim witness: polars' own signatures carry Unknown, which "all" rejects)
"""Cut one demo into fight episodes from hero-on-hero damage; sweep gap x radius.

Usage: python -I segmentation-from-events.py DEMO

Clustering is boon.teamfights' sweep (stats.py) with min_players=1, kept here
because boon does not expose per-event fight labels, which the two-sided check
needs. Each setting's count is cross-checked against boon.teamfights itself.
Prints one TSV row per (gap_s, radius): episodes, median duration, kills inside
an episode, episodes with damage from both teams, kills inside those, and
the 90th-percentile episode spread (farthest event from its centroid, units).
"""

import math
import sys

import boon
import polars as pl

GAPS = (5.0, 10.0, 15.0)
RADII = (1500.0, 3000.0, math.inf)


def hero_damage(demo: boon.Demo) -> pl.DataFrame:
    """Opposing-team hero damage at the victim's (else attacker's) position."""
    teams = demo.players.select("hero_id", "team_num")
    pos = demo.player_ticks.select("tick", "hero_id", "x", "y")
    dmg = (
        demo.damage.filter(
            (pl.col("attacker_hero_id") != 0)
            & (pl.col("victim_hero_id") != 0)
            & (pl.col("attacker_hero_id") != pl.col("victim_hero_id"))
        )
        .join(teams.rename({"hero_id": "attacker_hero_id", "team_num": "at"}), on="attacker_hero_id")
        .join(teams.rename({"hero_id": "victim_hero_id", "team_num": "vt"}), on="victim_hero_id")
        .filter(pl.col("at") != pl.col("vt"))
    )
    dmg = (
        dmg.join(pos.rename({"hero_id": "victim_hero_id", "x": "vx", "y": "vy"}), on=["tick", "victim_hero_id"], how="left")
        .join(pos.rename({"hero_id": "attacker_hero_id", "x": "ax", "y": "ay"}), on=["tick", "attacker_hero_id"], how="left")
        .with_columns(x=pl.coalesce("vx", "ax"), y=pl.coalesce("vy", "ay"))
        .filter(pl.col("x").is_not_null())
        .sort("tick", maintain_order=True)
    )
    return dmg.select("tick", "at", "x", "y")


def label(dmg: pl.DataFrame, gap_ticks: int, radius: float) -> list[int]:
    """boon.teamfights' sweep: join the nearest live fight within radius, else start one."""
    r2 = radius * radius
    active: list[list[float]] = []  # last_tick, cx, cy, n, label
    labels: list[int] = []
    fresh = 0
    for t, x, y in zip(dmg["tick"], dmg["x"], dmg["y"], strict=True):
        active = [f for f in active if t - f[0] <= gap_ticks]
        best, best_d = None, r2
        for f in active:
            d = (x - f[1]) ** 2 + (y - f[2]) ** 2
            if d <= best_d:
                best, best_d = f, d
        if best is None:
            best = [float(t), float(x), float(y), 0.0, float(fresh)]
            fresh += 1
            active.append(best)
        n = best[3] + 1
        best[0], best[3] = t, n
        best[1] += (x - best[1]) / n
        best[2] += (y - best[2]) / n
        labels.append(int(best[4]))
    return labels


def main(path: str) -> None:
    demo = boon.Demo(path, preload=False)
    demo.load("damage", "kills", "player_ticks", "world_ticks")
    rate = demo.tick_rate
    dmg = hero_damage(demo)
    kills = demo.kills["tick"].to_list()
    print(f"# map x {dmg['x'].min():.0f}..{dmg['x'].max():.0f}, y {dmg['y'].min():.0f}..{dmg['y'].max():.0f}")
    print(f"# hero-on-hero damage events {dmg.height}; kills {len(kills)}; tick_rate {rate}")
    print("gap_s\tradius\tepisodes\tboon_teamfights\tmedian_s\tkills_in\tkills_in_pct\ttwo_sided\ttwo_sided_pct\tkills_in_two_sided\tspread_p90")
    for gap in GAPS:
        for radius in RADII:
            lab = dmg.with_columns(ep=pl.Series(label(dmg, max(1, round(gap * rate)), radius)))
            eps = lab.group_by("ep").agg(
                start=pl.col("tick").min(),
                end=pl.col("tick").max(),
                teams=pl.col("at").n_unique(),
                spread=((pl.col("x") - pl.col("x").mean()) ** 2 + (pl.col("y") - pl.col("y").mean()) ** 2)
                .sqrt()
                .max(),
            )
            starts, ends = eps["start"].to_list(), eps["end"].to_list()
            inside = sum(any(s <= k <= e for s, e in zip(starts, ends)) for k in kills)
            two = int((eps["teams"] == 2).sum())
            both = eps.filter(pl.col("teams") == 2)
            in_two = sum(any(s <= k <= e for s, e in zip(both["start"], both["end"])) for k in kills)
            spread = eps["spread"].quantile(0.9)
            ref = demo.teamfights(gap_seconds=gap, radius=radius, min_players=1).height
            med = ((eps["end"] - eps["start"]) / rate).median()
            r = "none" if math.isinf(radius) else f"{radius:.0f}"
            n = eps.height
            print(f"{gap:.0f}\t{r}\t{n}\t{ref}\t{med:.1f}\t{inside}\t{100*inside/len(kills):.0f}\t{two}\t{100*two/n:.0f}\t{in_two}\t{spread:.0f}")


if __name__ == "__main__":
    main(sys.argv[1])
