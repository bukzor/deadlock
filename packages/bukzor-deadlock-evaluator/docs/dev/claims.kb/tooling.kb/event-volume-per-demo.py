# pyright: basic
# (a claim witness: polars' own signatures carry Unknown, which "all" rejects)
"""Measure one Deadlock demo: duration, ticks, rows per boon dataset grouped by
event kind, the three demo-kind facts (roster size, heroes in player_ticks,
damage rows joining a same-tick victim position), and the parsed size on disk
as JSON lines and Parquet. The witness for `event-volume-per-demo.md`.

Usage: data/tools/boon.d/bin/python -I event-volume-per-demo.py DEMO.dem [OUT_DIR]

Prints one TSV block per section to stdout. With OUT_DIR, also writes one
`<dataset>.jsonl` and `<dataset>.parquet` per dataset and reports their sizes;
without it the size section is skipped (the JSON lines run to gigabytes).
"""

import sys
import time
from pathlib import Path

import polars as pl
from boon import Demo

KIND_OF = {
    "player_ticks": "positions",
    "damage": "damage",
    "item_purchases": "purchases",
    "ability_ticks": "casts",
    "abilities": "casts",
}
SKIP = {"street_brawl_ticks", "street_brawl_rounds"}  # Street Brawl only


def load_each(demo: Demo) -> dict[str, tuple[pl.DataFrame, float]]:
    """Every regular dataset, with its load time; a failing dataset is reported
    on stderr and omitted rather than aborting the survey."""
    out: dict[str, tuple[pl.DataFrame, float]] = {}
    for name in Demo.available_datasets():
        if name in SKIP:
            continue
        t = time.time()
        try:
            df = getattr(demo, name)
        except Exception as e:  # survey: record the failure, keep going
            print(f"{name}\tERROR\t{type(e).__name__}: {e}"[:300], file=sys.stderr)
            continue
        out[name] = (df, time.time() - t)
    return out


def souls_changes(player_ticks: pl.DataFrame) -> int:
    """Rows where a hero's souls or net worth differ from its previous recorded
    tick (a client-side bot demo records souls as 0 throughout, so net worth
    is the fallback signal)."""
    changed = (
        player_ticks.sort("hero_id", "tick")
        .with_columns(
            prev_souls=pl.col("souls").shift(1).over("hero_id"),
            prev_worth=pl.col("gold_net_worth").shift(1).over("hero_id"),
        )
        .filter(
            (pl.col("souls") != pl.col("prev_souls"))
            | (pl.col("gold_net_worth") != pl.col("prev_worth"))
        )
    )
    return changed.height


def damage_joined(damage: pl.DataFrame, player_ticks: pl.DataFrame) -> tuple[int, int]:
    """(hero-victim damage rows, those with a victim position at their tick)."""
    hero = damage.filter(pl.col("victim_class") == 1)
    j = hero.join(
        player_ticks.select("tick", "hero_id", "x"),
        left_on=["tick", "victim_hero_id"],
        right_on=["tick", "hero_id"],
        how="left",
    )
    return hero.height, j.filter(pl.col("x").is_not_null()).height


def write_both(df: pl.DataFrame, stem: Path | None) -> tuple[int, int]:
    """Write JSONL and Parquet beside `stem`; return their byte sizes (0, 0
    when there is nowhere to write)."""
    if stem is None:
        return 0, 0
    else:
        jl, pq = stem.with_suffix(".jsonl"), stem.with_suffix(".parquet")
        df.write_ndjson(jl)
        df.write_parquet(pq)
        return jl.stat().st_size, pq.stat().st_size


def main() -> None:
    demo_path = Path(sys.argv[1])
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
    demo = Demo(str(demo_path), preload=False)
    print("section\tkey\tvalue")
    print(f"demo\tpath\t{demo_path}")
    print(f"demo\tsize_bytes\t{demo_path.stat().st_size}")
    print(f"demo\tbuild\t{demo.build}")
    print(f"demo\tmatch_id\t{demo.match_id}")
    print(f"demo\ttick_rate\t{demo.tick_rate}")
    print(f"demo\ttotal_ticks\t{demo.total_ticks}")
    print(f"demo\ttotal_clock_time\t{demo.total_clock_time}")
    print(f"demo\tregulation_clock_time\t{demo.regulation_clock_time}")
    print(f"demo\tgame_start_tick\t{demo.game_start_tick}")
    print(f"demo\tgame_over_tick\t{demo.game_over_tick}")
    print(f"kind\troster_players\t{demo.players.height}")

    loaded = load_each(demo)
    print("\ndataset\tkind\trows\tload_s\tjsonl_bytes\tparquet_bytes")
    totals: dict[str, int] = {}
    jl_total = pq_total = 0
    for name, (df, secs) in loaded.items():
        kind = KIND_OF.get(name, "other")
        jl, pq = write_both(df, None if out_dir is None else out_dir / name)
        jl_total += jl
        pq_total += pq
        totals[kind] = totals.get(kind, 0) + df.height
        print(f"{name}\t{kind}\t{df.height}\t{secs:.1f}\t{jl}\t{pq}")

    pt = loaded["player_ticks"][0]
    totals["souls (player_ticks rows where souls/net worth changed)"] = souls_changes(
        pt
    )
    print("\nkind\trows")
    for kind, n in totals.items():
        print(f"{kind}\t{n}")
    print(f"all datasets\t{sum(df.height for df, _ in loaded.values())}")
    if out_dir is not None:
        print(f"\nsize\tjsonl_bytes\t{jl_total}")
        print(f"size\tparquet_bytes\t{pq_total}")

    hero_rows, joined = damage_joined(loaded["damage"][0], pt)
    print(f"\nkind\tplayer_ticks_heroes\t{pt['hero_id'].n_unique()}")
    print(f"kind\tplayer_ticks_ticks\t{pt['tick'].n_unique()}")
    print(f"kind\thero_victim_damage_rows\t{hero_rows}")
    print(f"kind\tjoined_to_same_tick_position\t{joined}")
    print(f"kind\tabilities_rows\t{loaded['abilities'][0].height}")


if __name__ == "__main__":
    main()
