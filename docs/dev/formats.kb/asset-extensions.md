# Asset-type inventory

The compiled file types found in Deadlock's `pak01` set, as a glossary. Counts
are approximate and drift per patch (snapshot: client build 6583); treat the
generated manifest under `data/` as authoritative for any given version.

| ext (`*_c`) | what it is | order of magnitude |
|-------------|------------|--------------------|
| `vsnd_c`    | sound (audio clip) | ~79k |
| `vpcf_c`    | particle system | ~15k |
| `vtex_c`    | texture | ~13k |
| `vnmclip_c` | animation clip (NM) | ~9k |
| `vmdl_c`    | model | ~5k |
| `vmat_c`    | material | ~4k |
| `vnmgraph_c`| animation graph | ~1.5k |
| `vcd_c`     | choreography scene | ~700 |
| `vsvg_c`    | vector graphic | ~560 |
| `vcss_c` / `vxml_c` | Panorama UI styles / markup | ~400 each |
| `vsmart_c`  | smartprop | ~230 |
| `vsndevts_c`| sound events | ~150 |
| `vrr_c`     | response rules | ~110 |
| `vsnap_c`   | particle snapshot | ~90 |
| `vdata_c`   | **game data (KV3)** — heroes, abilities, etc. | ~84 |
| `vnmskel_c` / `vnmvar_c` | animation skeleton / variables | ~50 each |

`vdata_c` is the highest-value target for understanding mechanics. Asset viewing
targets `vtex_c` (→png), `vmdl_c` (→glTF), `vsnd_c` (→wav).
