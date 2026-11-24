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

## Caption fidelity

Measured on Vyper (`viper`), build 6864: whether her English audio says
what its caption says.

- **Method:** all 1717 clips with a real English caption, transcribed by
  whisper `small` pinned to `-l en` (`vo_asr --english`, ledger
  `transcripts/asr/viper.tsv`). Each text is scored against its caption by
  word-level similarity (difflib's ratio over the word lists) after
  lowercasing, dropping punctuation and `<...>`/`(...)` stage directions,
  and expanding contractions and spoken spellings (`'s`, `gonna`, `outta`,
  `-in'`, digits) the same way on both sides. Every clip scoring below 1.0
  (702) was judged by hand; the doubtful ones were rerun alone on
  large-v3-turbo f16 (24 clips, rows in the same ledger).
- **Result:** 1015 clips match word for word. Of the 702 others, 413 are
  ASR errors, 284 are minor wording differences, 5 are material
  differences, and none is a different take. So **0.3% (5 of 1717) of
  captions misstate the line.** If "differs" means any word, 17% of all
  clips and 33% of her 801 non-ping clips differ, almost all by ad-libbed
  fillers and openers the caption leaves out ("You know what, I'll take
  it.", "Oh, you think I'm done?"); 235 of the 284 minor clips are longer
  than their caption.
- **The material ones:** three `ally_*_killed_in_lane_01` lines where she
  uses a nickname and the caption the hero's name ("They took out Grey
  Talon!" is heard as "...the old man.", Dynamo as "the professor", Ivy as
  "the gargoyle"; other heroes' captions in the same set do use her
  nicknames, e.g. "the Pigeon Lady"); one added sentence
  (`close_call_05`: "...I feel like that's the problem."); and one
  `can`/`can't` (`ping_can_heal_drifter`, heard "I can't heal you" by both
  models, the least certain of the five).
- **ASR errors cluster in pings,** not in a score band: 263 of the 282
  flagged ping clips are misheard hero or ability names (Hayes, Inferness,
  alt for ult). Scores of 0.4 to 0.8 are mostly ASR errors and
  0.9 and above mostly fillers, but one material clip scored 0.91, so no
  threshold below 1.0 is safe.
- **Caveats:** one hero, one judge (an agent, no listening). Turbo
  overturned 1 of 5 material calls made on `small` alone and confirmed all
  6 ad-libbed additions it rechecked, so the estimated false-positive rate
  is 20% for material calls (the `can't`) and near 0 for the filler
  differences. A real difference hidden under an "ASR error" call is
  possible where a mishearing overlaps it; turbo found such cases in 4 of
  the 10 doubtful ASR calls it rechecked (3 minor, 1 material), so the
  material rate could be up to about 0.6%.
- **"Calvin" is said, not misheard.** The owner (2026-11-24): characters
  getting Kelvin's name wrong is a running gag. Whisper agrees: in the same
  voice and model it hears "Calvin" in 12 of Vyper's 23 Kelvin clips
  (every kill, convo and zipline line, plus some pings) and "Kelvin" in 10
  (`careful_kelvin_*`, `see_kelvin_01` and other pings). A mishearing
  wouldn't split like that. Those 12 were judged ASR errors above. Counted
  as material, they raise the rate to **1.0% (17 of 1717)**, and the
  agent judge's other "misheard name" calls are suspect in the same way.
