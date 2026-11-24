# Caption mod (`data/mod/`)

Our captions for the foreign-language and uncaptioned VO lines
(`data/vo/foreign.tsv`), in two forms: a mod VPK players can install, and a
diff per locale for Valve. Both are local (gitignored) and rebuilt by
`redo data/mod/vo-captions.vpk`. The column and file contracts are in
`bukzor_deadlock.vo_mod`. Verified on build 6864 (2026-11-24).

## Layout

- `data/mod/captions.d/tree/resource/localization/citadel_generated_vo/citadel_generated_vo_<locale>.txt`:
  one file per real locale (the 17 game files over 1 KB; the other 12 are
  ~60-byte stubs with an empty `Tokens` block). Each holds **only our
  tokens**, under the game file's own header and closing braces, in the
  game's encoding: UTF-8 with a BOM, CRLF, `\t\t"<token>"\t\t"<caption>"`
  lines (`vo-captions.md`). The `Tokens` block's closing brace is indented
  one tab in 4 real locales (czech, english, koreana, schinese) and two in
  the other 13; each file keeps its own.
- `data/mod/captions.d/diffs/<locale>.diff`: a unified diff from the game's
  file to the game's file with our tokens substituted in place. Valve's
  encoding, BOM, CRLF and token order are kept; a token the locale's file
  lacks is appended at the end of its `Tokens` block. Paths are relative to
  the install root: apply with `patch -p1` from `Deadlock/`.
- `data/mod/vo-captions.vpk`: `tree/` packed as one VPK v2 file.

Every `foreign.tsv` row with a fix-up (a non-empty `translation`) is in all
17 locales: 649 tokens each. A row without one still holds raw ASR text and
is left out. `transcripts/caption-corrections.tsv` (wrong English captions)
is not used. The 81 events with no caption today (whisper's `auto` rows and
empty English captions in `lines.tsv`) are included: the token is the event
name, so adding it makes a caption appear. Many tokens are new to a locale's
file (all 649 for japanese, spanish and indonesian).

The build parses every file it writes back with `vo_captions.tokens`, and
requires each token to be in the English game file or be an uncaptioned
event. The diffs were applied with GNU `patch` to all 17 game files, and
their tokens checked as the game's updated by ours.

## Caption styling

([!@bukzor] 2026-11-24, from the parent plan.) A row's caption in locale
L is the `replacement` (the text as spoken, in its language's own script),
then `<br>`, then the translation in brackets:

    奇怪な生き物だ。<br>[A bizarre creature.]

- `<br>` is the line break the game's other localization uses (1050 uses in
  the English files; no `<cr>` or `\n`). The owner's in-game test confirms
  it renders in captions. It is one constant, `vo_mod.BR`.
- The bracket is dropped when L reads the spoken language: `ja` in
  japanese, `es` in spanish and latam, `fr` in french, English in english.
- It is also dropped when it would only repeat the line (an English line
  in a locale with no translation yet).
- The spoken language is `foreign.tsv`'s `lang`, except: `auto` is English
  (but for the clips `vo_forum.SPOKEN_OTHER` names, such as Ivy's one
  Spanish line), and a `ja` row whose replacement is all ASCII is English
  (9 Yamato lines; the replacement rule writes English speech in Latin
  script).
- The bracketed text is L's row in `transcripts/locale-translations.tsv`
  (`translation locale text by`, keyed by the English `translation`), and
  the English translation where it has none. The mod is valid with the
  ledger absent or partial.
- `"` and `\` are escaped as `\"` and `\\`.

## Packing

The python `vpk` package (1.4.0, already a dependency) writes the file:
`vpk -cv 2 -c tree out.vpk`. It writes VPK v2 with all data inline in the
one file (archive index `0x7fff`) and the 48-byte MD5 section filled in.
deadlock-mod-manager's own writer (`packages/vpkmanager/src/pack.rs`) makes
the same layout with the MD5 section zeroed, and builds its localization
overlay that way, so the game loads this layout (inferred from the manager,
not tested in game here). ValveResourceFormat's CLI (`--vpk_list`) reads
ours. Whether Source 2 loads v1 was not checked; nothing here writes v1.

## How deadlock-mod-manager installs it

Read from its source at commit d0c8f78 (nothing was run), under
`apps/desktop/`:

- **Add Local Mod** (the "Add local mod" menu item) takes one or more
  `.vpk` files, a `.zip`/`.rar`/`.7z`, or a folder. It copies a `.vpk` into
  `game/citadel/addons/` as `<modId>_<name>`, and on enable renames it to
  the lowest free `pakNN_dir.vpk`. It checks only the extension, so the
  file's own name doesn't matter.
- It adds `Game citadel/addons` (or its own shard paths) to `gameinfo.gi`
  ahead of `Game citadel`, after the `Game_UILanguage` entries. A VPK there
  shadows the game's loose caption file wholesale.
- Its localization overlay (`src-tauri/src/mod_manager/localization_overlay.rs`)
  covers every `resource/localization/**.txt`, subdirectories included. For
  each file it seeds the game's tokens (from the loose file, or the first
  `*_dir.vpk` holding it), merges each enabled mod's tokens over them,
  skips tokens equal to the game's, and writes the result into
  `game/citadel/dmm_localization_<profile>/pak01_dir.vpk`. A mod file that
  omits game tokens is logged as a `RestoredGameText` repair, not an error.
  It reads UTF-8 with or without a BOM.
- It shows the notice "Some mods include many game text entries" for any
  mod file with 50 or more changed tokens. It is information only, and
  this mod shows it ("differs in 649 of 649 text entries").

So a tokens-only file is the right shape under the manager. A full copy of
Valve's file would also work today, but after a patch its stale tokens
would differ from the game's new text and win the merge, pinning Valve's
old captions for every hero. It is also 5 MB per locale against 70 KB.
Without the manager (the VPK dropped into `addons/` by hand, which also
needs a `gameinfo.gi` edit), the tokens-only file hides every other
caption in the game.

## Installing locally

1. `redo data/mod/vo-captions.vpk`.
2. In deadlock-mod-manager, "Add local mod", and pick
   `data/mod/vo-captions.vpk` (from Windows:
   `\\wsl.localhost\<distro>\home\...\data\mod\vo-captions.vpk`).
3. Enable it and launch the game.
