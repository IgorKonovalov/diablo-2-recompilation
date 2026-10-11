# MPQ archives: set, names, precedence, merged tree

Owned by `archivist`. Covers Plan 0001 Phase 3. Gameplay data is taken from the **1.14b reference
archives**, not from the 1.14d install's MPQs. Their `data/global/` content is byte-identical,
and this way the install's localisation and its extra `TreasureClass.txt` stay out
([installer.md § MPQ integrity](installer.md#mpq-integrity-comparison-with-the-114b-reference)).

The container itself (header v1, hash and block tables, sector compression) is read with StormLib
through `smpq` 1.7 / StormLib 9.40 (ADR-0001 toolchain). No parser of our own is needed so far.

## Archive set

| name in `workspace/mpq/` | reference file | size | sha256 | entries | named | unnamed |
|---|---|---:|---|---:|---:|---:|
| `d2data` | `1.14b-d2/Common/d2data.mpq` | 267642202 | `99e53768ddb87ca70b54529ff15043aaa71353cc250e757ae20e9c3d002ca431` | 10814 | 10814 | 0 |
| `d2char` | `1.14b-d2/Common/d2char.mpq` | 263369609 | `8b6a08d39f7262912f1e96e21417bc352c684ba4f6f3f4537e290da7f3b5a37d` | 10008 | 10008 | 0 |
| `d2music` | `1.14b-d2/Common/d2music.mpq` | 348433635 | `5c367f95694cd45a60dc0c02ed9d7c349c05b0f701be787c172087544ddd2e65` | 41 | 41 | 0 |
| `d2sfx` | `1.14b-d2/Common/d2sfx.mpq` | 48927126 | `737d128b3e81526c630503a435b56c70bbdaee2e76d39df4efb025e721432aba` | 2328 | 2328 | 0 |
| `d2speech` | `1.14b-d2/Common/d2speech.mpq` | 163021838 | `7a238f808be9fbc74da55c98dc629ab7fac9a4f40c537cec3c1b042fa45d211a` | 1565 | 1565 | 0 |
| `d2video` | `1.14b-d2/Common/d2video.mpq` | 441697807 | `7bf1bbcd6e73a415775444ff78e1bfcce83ca1af75c52b1f33998526e6e186b6` | 16 | 16 | 0 |
| `patch_d2-classic` | `1.14b-d2/Common/patch_d2.mpq` | 8118927 | `67572c2d9a6ea5844fb66f48a1dd017505615600087fe9192b60b23fb9f7e8f1` | 1146 | 1137 | 9 |
| `d2exp` | `1.14b-d2lod/Common/d2exp.mpq` | 250156780 | `04e35bffeae8d9959042832055702f8b5b4567ca5505ff1df0cf3fd6d5beb6c2` | 9851 | 9851 | 0 |
| `d2xmusic` | `1.14b-d2lod/Common/d2xmusic.mpq` | 54691647 | `4aae5a0c456236693226380d062daa3f5cd36a90a9010d036a7da0ba132f71a1` | 10 | 10 | 0 |
| `d2xtalk` | `1.14b-d2lod/Common/d2xtalk.mpq` | 60278192 | `305a35331629e7054c34682774e18398f5cbcbed293ddf0ce3c16e25c3f0463c` | 476 | 476 | 0 |
| `d2xvideo` | `1.14b-d2lod/Common/d2xvideo.mpq` | 110685575 | `209c7a250e2117bac2720e40f0c3687549678cf5e993e5f74a6dbb2914c97591` | 4 | 4 | 0 |
| `patch_d2` | `1.14b-d2lod/Common/patch_d2.mpq` | 3915305 | `81470b762c497a8fcaf9a09990c0e869a4175395ef1fae13bd85cfec7b688ddc` | 209 | 204 | 5 |

- `[C]` The set matches the 11 Blizzard MPQs of the 1.14d install one for one by name. The
  reference set has two `patch_d2.mpq`, one per installer. Installing LoD over classic replaces the
  file, so the LoD one is what a 1.14 LoD install holds (the 1.14d install's `patch_D2.mpq` carries
  the LoD reference's content, installer.md). The classic patch is extracted for completeness
  and **never merged**.
- `[L]` `Game.exe` names more archives than ship: `d2kfixup.mpq` (`0x006DC738`) and `d2delta.mpq`
  (`0x006DC748`) appear in the same string block as `patch_d2.mpq` (`0x006DC728`), `d2data.mpq`
  (`0x006DC770`) and the others. `d2exp.mpq` sits apart at `0x006CD3A0`. Whether the game opens
  the two missing ones when present, and at what priority, is a reverser question.

## File names

- `[C]` Every archive except the two `patch_d2.mpq` carries a complete internal `(listfile)`:
  `smpq -l` names every hash-table entry.
- `[C]` Both `patch_d2.mpq` have **no usable listfile**. Names are recovered with a candidate
  list built by `tools/mpq_dump.py names` from every local archive's own listfile (the reference
  set and the 1.14d install's MPQs), plus two derived sets: each `data\global\excel\` name with
  both `.txt` and `.bin`, and each `data\local\<kind>\<lang>\` name with every language code.
  No community listfile was needed. Recovery: 204/209 (LoD) and 1137/1146 (classic).
- `[C]` **All excel entries in both patches are named.** The 5 unnamed LoD-patch entries are small
  `.dc6` sprites (397–457 bytes, StormLib guesses the extension from content), so no gameplay
  table is missing from the merge.
- `[C]` smpq's `-L` resolves only names written with **backslashes** (`data\global\…`).
  Forward-slash names silently resolve 0 entries. `candidates-listfile.txt` is written that way.
- `[C]` Name case is inconsistent across and within archives (`data/` and `Data/` both occur in
  d2data; `RarePrefix.txt` next to `rareprefix.bin`). MPQ name hashing ignores case, so the merged
  tree lowercases every path and the manifest keeps the original spelling.

## Precedence and the merged tree

`workspace/merged/` is built by copying d2data → d2exp → patch_d2 (LoD) in that order, so a later
archive overwrites an earlier one.

- `[L]` The order itself (patch over expansion over base) is the conventional one and not yet
  anchored in `Game.exe`. The archive name strings above are the entry point for the reverser.
  → backlog. It has a data-behaviour hint (next bullet) but no code anchor, so it stays `[L]`.
- `[C]` The merged tree is internally consistent: every one of its 87 excel `.txt`/`.bin` pairs
  agrees on record count ([tables/README.md](../tables/README.md)). That shows the merge doesn't
  contradict itself. It says nothing about the order the *game* uses.
- `[C]` Result: **20,569 files** (`data/global` 20,053, `data/local` 515, `data/iamexpansion` 1).
  Origins: d2data 10,626, d2exp 9,739, patch_d2 204. **300 overrides**: d2data→d2exp 187,
  d2exp→patch_d2 112, d2data→patch_d2 1. 280 change content and 20 are byte-identical
  re-ships. By area: excel 146, tiles 113, ui 14, items 4, palette 2, sfx 1, `chars_cof.d2` 1,
  `animdata.d2` 1.
- Not merged: d2char, d2sfx, d2speech, d2music, d2video, d2x{music,talk,video} (graphics, audio,
  video, no excel or map data), and patch_d2-classic. They stay extracted under `workspace/mpq/`.

## Regenerate

```bash
R=workspace/reference/extracted
python3 -I tools/mpq_dump.py names workspace/mpq/candidates-listfile.txt $R/*/Common/*.mpq workspace/install/app/*.mpq
python3 -I tools/mpq_dump.py extract workspace/mpq/candidates-listfile.txt workspace/mpq $R   # ~1 min, 3.0 GB
python3 -I tools/mpq_dump.py merge workspace/mpq workspace/merged workspace/logs             # 693 MB
```

Outputs: `workspace/mpq/counts.tsv`, `workspace/logs/merged-manifest.tsv` (path, archive,
original name, size, sha256; sha256 of the manifest itself as of 2026-10-11:
`ea8ea74f212123acd9e4dc68f22f93db2f42773936ddf121c5a0a0ba4dac6c38`), `workspace/logs/overrides.txt`.
A rebuild that gives a different manifest hash means the inputs or the tool changed.

## Open questions

- `[L]` Archive open order and priority in `Game.exe`, including `d2kfixup.mpq` and `d2delta.mpq`. → reverser.
- `[L]` Whether 1.14d's real `patch_d2.mpq` equals 1.14b LoD's (installer.md, *Remaining gap*).
