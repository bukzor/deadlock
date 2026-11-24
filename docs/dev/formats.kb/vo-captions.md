# VO captions (`citadel_generated_vo_<lang>.txt`)

The subtitle text of every voice line, one file per locale. Verified on
build 6864.

## Location

Loose files in the install, not in any pak:
`game/citadel/resource/localization/citadel_generated_vo/citadel_generated_vo_<lang>.txt`.
The paks hold none of them (the `.dat` an older `data/manifest.jsonl` lists
came from an earlier build).

## Encoding

KeyValues1 text, UTF-8 with a BOM, CRLF line ends:
`"lang" { "Language" "<Name>" "Tokens" { "<token>" "<caption>" ... } }`.
No comments. The only escape in use is `\"` (1290 of them across all
locales). One English caption (`punkgoat_kill_necro_04_hero_3d`) holds a
raw newline inside its quotes. No token repeats within a file. The `vdf`
library parses them (`bukzor_deadlock.vo_captions`); `bukzor_deadlock.loc`'s
quoted-pair regex does not, because it drops every line holding a `\"`.

## Tokens

A token is exactly the name of its sound event in
`soundevents/vo/*.vsndevts_c` (for example `yamato_ally_astro_bounce_pad_01_hero_3d`).
Every token in every locale names an existing event. Over the 79,936 events
in `generated_vo_hero_*.vsndevts_c`:

- 4,186 hero events have no caption in any locale (57 of them Yamato's).
- 2,687 tokens name no hero event. They belong to `generated_vo_misc`
  (`patron_*` 1748, `shopkeeper_*` 478, `spirit_*` 336, `newscaster_*` 103,
  and a few others).

## Per-locale coverage

Tokens per file, and how many of them name hero events:

| lang | tokens | hero events |
|---|---|---|
| english | 78437 | 75750 |
| schinese | 76537 | 73851 |
| brazilian | 75086 | 72626 |
| koreana | 71267 | 68590 |
| czech | 70826 | 68974 |
| italian | 62214 | 60274 |
| french | 58885 | 57020 |
| ukrainian | 56188 | 54325 |
| german | 53330 | 51464 |
| latam | 53018 | 51102 |
| thai | 49964 | 48104 |
| russian | 41334 | 39764 |
| spanish | 32749 | 31193 |
| indonesian | 27453 | 25189 |
| turkish | 11593 | 10329 |
| polish | 11588 | 9815 |
| japanese | 6253 | 6099 |

Stubs of about 60 bytes with an empty `Tokens` block: bulgarian, danish,
dutch, finnish, greek, hungarian, norwegian, portuguese, romanian, swedish,
tchinese, vietnamese.

## Yamato's Japanese lines

Of Yamato's 1806 events, 532 are captioned `Speaks Japanese` in English,
1217 carry a real English caption, and 57 have none. No locale translates
any of the 532: each one that covers them repeats its own marker, e.g.
`Parle en japonais.` (french, 532), `[Spricht Japanisch]` (german, 512),
`[日语]` (schinese, 532), `일본어로 말함` (koreana, 470), `&lt;japonština&gt;`
(czech, 69). The japanese locale covers 159 Yamato events, all from the
1217 with English captions, and none of the 532. So the 1217 are probably
English-language audio (inferred, not checked against the audio).

## Built tables

`data/vo/lines.tsv` (committed) joins each hero clip to its audio CRC32 and
English caption; `data/vo/captions.tsv` (local) holds every locale, long,
joined on `event`. The column contracts are in `bukzor_deadlock.vo_lines`
and `bukzor_deadlock.vo_captions`.
