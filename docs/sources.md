# Sources registry

Policy (ADR-0001): community **documentation** can be used as leads. Third-party **decompiled or
reconstructed code** (D2MOO and similar) is never read, copied or paraphrased. Cite an entry as
`src:<id>`; anything sourced this way stays `[L]` until it is anchored in our binary.

| id | Title / author | URL | What it covers | Notes |
|---|---|---|---|---|
| `siramy-ds1edit` | Diablo II DS1 Editor (ds1edit) and its DS1 format notes, Paul Siramy | https://www.allegro.cc/depot/DiabloIIMapEditor/ | DS1 layout: the version thresholds of the header fields, layer order, object, group and NPC-path lists; names for the cell bytes (main/sub index, orientation). DT1 layout: header, 96-byte tile record, 20-byte block header, isometric/RLE blocks, sub-tile flags | Community editor for 1.09-era data (DS1 files are data, unchanged by patches). Used as a lead for [formats/ds1.md](formats/ds1.md) and [formats/dt1.md](formats/dt1.md) only: layouts recalled from the editor's documentation, then checked against every file by `tools/ds1.py`. Thresholds that fall between the versions present in 1.14d stay `[L]`. |
| `d2s-community-format` | Community `.d2s` save-format notes for version 96 (1.10+), e.g. the "d2s-format" write-up (krisives) | https://github.com/krisives/d2s-format | D2S header offsets, section tags (`Woo!`, `WS`, `w4`, `gf`, `if`, `JM`, `jf`, `kf`), the checksum, the stat and item bitstreams (flag bits, field order, quality-specific fields, grouped stats) | Community documentation of the save format, not game code. Used as a lead for [formats/d2s.md](formats/d2s.md) only: layout recalled, not re-read, then checked against 23 saves written by the pinned game (`tools/d2s.py survey`) and a load test. Branches no sample exercises stay `[L]`. |
