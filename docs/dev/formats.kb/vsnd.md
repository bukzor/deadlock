# `vsnd_c` (sound clip)

A Source 2 compiled resource (see `source2-compiled-resource.md`) of type
Sound, resource version 5, header version 12. Verified on build 6864 with VRF
21.1, on Yamato and Haze voice clips (1806 and 1942 clips).

## Layout

- Blocks: `RED2` (build dependencies), an empty `DATA`, and `CTRL` (KV3
  sound description). The audio bytes follow the header, unwrapped: the
  decompiled `.mp3` is byte-identical to the tail of the `vsnd_c`
  (`size - header`), so the compressed audio is stored as shipped, never
  re-encoded.
- `CTRL` holds `CVoiceContainerDefault`: `m_vSound` (below) and
  `m_pEnvelopeAnalyzer`, a loudness spline sampled every 0.05 s.
- `RED2` records the build inputs only: `sounds/**/encoding.txt` (optional),
  optional `<name>.{mp3,rts,txt,vsnd}` and a required `<name>.wav`
  with its CRC. The `.txt` slot is the Source 1 sentence-file analogue; none
  of them ship, and the source `.wav` is not in the paks.

`m_vSound` fields: `m_nRate`, `m_nFormat`, `m_nChannels`, `m_nSampleCount`,
`m_flDuration` (seconds), `m_Sentences`, `m_nStreamingSize` (audio bytes),
`m_nSeekTable`, `m_nLoopStart`/`m_nLoopEnd`, `m_encodedHeader`.

## Text, phonemes, lip-sync: none

`m_Sentences` is the only text-bearing field, and it is empty (`[  ]`) in
every voice clip checked: 1806 of 1806 Yamato clips and 1942 of 1942 Haze
clips (the English-speaking comparison hero). A raw string scan of the
file shows only field names and the `RED2` filenames; the MP3 carries no ID3
tag (starts `FF FB 90`). No transcript exists in the sound resources.

Nor do the neighbouring types carry one. A choreography scene
(`scenes/conversations/*.vcd_c`) lists `speak` events by soundevent name
and time only, and `resource/localization/` has no VO caption file in the
paks (only a 41-byte `items_english.txt`). Transcripts need ASR.

## Codec

Every clip checked, both heroes: MP3, 44100 Hz, mono (`m_nFormat = "MP3"`,
128 kbps CBR by `file`). VRF's `-d` writes the audio as `.mp3` (a copy, not
a decode) plus a `.vsnd` KV3 text of `CTRL`. The asset-extensions note
`vsnd_c -> wav` does not hold for these clips. Decode with an MP3 decoder
(e.g. `ffmpeg`, 44.1 kHz mono) for ASR.

## Yamato inventory (build 6864, live `--vpk_list`)

- `sounds/vo/yamato/` holds 1806 clips: 950 in `ping/`, 46 in `emote/`, 810
  at the top level (`data/manifest.jsonl` as built earlier lists 1648;
  it predates the live pak. Use the live listing).
- Total duration 2912 s = 48.5 min (header `m_flDuration`, sum over all
  1806); mean 1.61 s, median 1.39 s, max 7.8 s.
- All Yamato-named `vsnd_c` paths: 3322 live (3163 in the manifest); the
  rest are other heroes' lines about Yamato (`sounds/vo/<hero>/...yamato...`)
  and her weapon/ability sounds, not her voice.

Bulk extraction is fast: `Source2Viewer-CLI -i pak01_dir.vpk -f
sounds/vo/yamato/ -e vsnd_c -o OUT -d -q --threads 4` wrote all 1806 clips
(3612 files) in 2.5 s.

Evidence: `docs/dev/probes/vsnd-survey.py` (histograms, sentence count,
duration sum over the decompiled `.vsnd` files).
