# Installers — what we hold and how the install was obtained

Owned by `archivist`. Covers Plan 0001 Phase 2 and the MPQ integrity check.

## Installer set

All installers are kept under `workspace/reference/installers/` (gitignored):

| path | size | sha256 |
|---|---:|---|
| `1.14d/setup.exe` | 1564520 | `7c22d40bd9adb9bad83f063e22e1b430f2091148f1b946f2288d916ba2ef1d7b` |
| `1.14d/setup-1.bin` | 1398435328 | `65fc2af8ac7eeba79d04492305f01d6974b6607f9b1eae2ba860a91bb7555f09` |
| `1.14d/setup-2.bin` | 1336751760 | `2b5ce0705141fa504850f04b85893fdf04c63acdadb4656464f05631d7ad567a` |
| `1.14b-d2/Installer.exe` | 2664936 | `f845e8bc0ab622989fd25a81b24161ec7abbd1a6cc07e6d771df3962859f5f68` |
| `1.14b-d2/Installer Tome.mpq` | 1551865181 | `1a20e8e53a0c6b458c6ad0be37e873f127ed819c006505c75d181e9f0a9a1378` |
| `1.14b-d2lod/Installer.exe` | 2671080 | `a825d97018f2638d1ef067f3fc199cd3d613fe31748ab5494c61fe3250e7bbe5` |
| `1.14b-d2lod/Installer Tome.mpq` | 490399607 | `c286c74eba99c7905d61178d62527977df710a64b49bf557ea02c2fef90b3071` |

- **1.14d installer**: an Inno Setup package that contains the pinned `game.exe`. It is the source of
  `workspace/install/app/`.
- **1.14b reference installers**: Blizzard's digital-download installers for D2 and LoD. They are
  used to check the integrity of the MPQ data. Their payloads are extracted to
  `workspace/reference/extracted/1.14b-{d2,d2lod}/`.

## 1.14d installer: innoextract route (no wine needed)

```bash
I=workspace/reference/installers/1.14d/setup.exe
innoextract --info "$I"                       # workspace/logs/inno-info.txt
innoextract -l     "$I"                       # workspace/logs/inno-list.txt
innoextract -e -d workspace/install "$I"      # ~110 s, workspace/logs/inno-extract.txt
innoextract -t     "$I"                       # checksum test, workspace/logs/inno-test-reference-copy.txt
```

- `[C]` Inno Setup data version 5.5.6, not passworded, one setup language (`rus`). innoextract 1.9
  reads the two `.bin` volumes directly. The payload is plain files under `app/`: there is no
  FreeArc/ISDone/unarc wrapper, so the wine fallback was not needed. (innoextract exit 0, 2117
  entries listed, and `-t` passes on every file's stored checksum; observed.)
- `[C]` 2117 entries map to 2114 files on disk. The difference is two duplicate destinations,
  `app/DIABLO_II_{ENGLISH,RUSSIAN}.CMD` (70 B variants marked "overwritten" by the 66 B ones),
  plus the empty directory entry `app/save/`. Which setup option selects which `.CMD` variant was
  not checked (only launcher arguments are affected). `game.exe` and every MPQ appear exactly once,
  so no setup option can change them.
- `workspace/install/app/` is the game root. The full hashed list is in `docs/inventory.md`.

## What the 1.14d install contains (observed)

- `[C]` `game.exe` is byte-identical to Blizzard's signed 1.14.3.71 build (Authenticode verified,
  see `docs/inventory.md` § PINNED). Nothing in the install patches the binary on disk.
- `[C]` `ijl11.dll`, `smackw32.dll` and `binkw32.dll` also carry valid signatures (Blizzard,
  Blizzard and Take-Two respectively).
- `[C]` Bundled non-Blizzard software: PlugY (`PlugY.exe/.dll/.ini`, `PlugY/`), D2GL (`d2gl.mpq`,
  `d2gl.ini`), SGD2FreeRes (`.dll/.mpq/.json`), and `ddraw.dll`/`glide3x.dll` wrappers. All are
  class `third-party` in the inventory and are never used for analysis.
- `[C]` A Russian localisation: Russian fonts, UI art and `.tbl` strings inside `d2data`/`d2exp`/
  `patch_D2` under `data/local/` (see *MPQ integrity* below), plus loose `data/local/` overrides
  (2060 `sfx/*.wav`, 7 `video/*.bik`, and the `Use` language-index files).
- `[C]` None of the 13 MPQs carries an MPQ weak or strong signature (StormLib `SFileVerifyArchive`
  returned "no signature" for all; `workspace/logs/mpq-verify.txt`). All are format v0 (v1 header,
  32 bytes) with sector shift 3 (4 KiB sectors), and the header sits at offset 0. Their integrity
  is therefore checked by comparison instead (next section).

## MPQ integrity: comparison with the 1.14b reference

Provenance of the reference:

- `[C]` Both `Installer.exe` and both 1.14b `PC/Game.exe` (FileVersion 1.14.1.68) carry valid
  Blizzard Authenticode signatures (`tools/pe_authenticode.py`). The Tomes are unsigned MPQs
  (format v1, 44-byte header). Their header archive size equals the file size, so both files are complete.
- `InstallerFileList.xml` inside each Tome lists file sizes only, no hashes.

Extracted reference archives (read-only `smpq -x`; nothing was run):

| file | size | sha256 |
|---|---:|---|
| `1.14b-d2/Common/d2data.mpq` | 267642202 | `99e53768ddb87ca70b54529ff15043aaa71353cc250e757ae20e9c3d002ca431` |
| `1.14b-d2/Common/patch_d2.mpq` | 8118927 | `67572c2d9a6ea5844fb66f48a1dd017505615600087fe9192b60b23fb9f7e8f1` |
| `1.14b-d2lod/Common/d2exp.mpq` | 250156780 | `04e35bffeae8d9959042832055702f8b5b4567ca5505ff1df0cf3fd6d5beb6c2` |
| `1.14b-d2lod/Common/patch_d2.mpq` | 3915305 | `81470b762c497a8fcaf9a09990c0e869a4175395ef1fae13bd85cfec7b688ddc` |
| `1.14b-d2lod/PC/Game.exe` (1.14b) | 3590120 | `0680e266b1fbbc8e7815b0a7c4f67267de38fd9063fceeae2da0306389a52178` |

Content comparison (`tools/tree_diff.py`, sha256 per extracted file, paths matched
case-insensitively; A = 1.14d install, B = 1.14b reference):

| archive | identical | differ | A only | B only |
|---|---:|---:|---:|---:|
| `d2data.mpq` | 10811 | 1 (`data/local/use`) | 270 (all `data/local/{font,ui,lng,cmd}`) | 2 (`data/local/macui`) |
| `d2exp.mpq` | 9767 | 0 | 50 (all `data/local/{ui,lng,cmd}`) | 84 (`data/local/lng` other languages, `macui`) |
| `patch_d2.mpq` (vs LoD 1.14b) | 156 named + 0 unnamed-by-hash | 0 | 6 (see below) | 12 unnamed (sizes match other-language `patchstring.tbl` / `A5L28-31.dc6`) |

- `[C]` **Every `data/global/` file in the 1.14d install's `d2data`, `d2exp` and `patch_D2` is
  byte-identical to Blizzard's 1.14b payload.** That covers excel 56 + 145 + 129 files, plus
  monsters, objects, tiles, items, missiles and animdata. The archives themselves differ (they were
  rebuilt with the localisation), but their gameplay content does not.
- `[C]` `d2speech.mpq` and `d2xtalk.mpq` are whole-archive identical to the reference.
- `[C]` The 1.14d install's only additions to Blizzard archives are localisation under `data/local/`
  **and one gameplay file: `patch_D2.mpq:data/global/excel/TreasureClass.txt`** (721 lines, sha256
  `a109de6a…`). It is absent from both Blizzard patches and differs from `d2exp`'s
  `TreasureClass.txt` in 269 diff lines (e.g. `jew` weight 1→2, reweighted `Hpotion 2-5`). It must
  never enter `workspace/merged/`. Whether 1.14d reads `TreasureClass.txt` at all (versus
  `treasureclassex`) is a reverser question.
- Listfile gotcha: the reference `patch_d2.mpq` has no usable internal listfile, and smpq's `-L`
  only resolves names written with backslashes (`data\global\…`). Forward-slash names silently
  resolve 0 entries.

**Remaining gap (`[L]`):** the reference is **1.14b**, our pinned binary is **1.14d**. The 1.14d
install's `patch_D2.mpq` holds exactly the 1.14b LoD patch content for every shared path. Either
1.14c/1.14d changed no data files (only the exe), or this install pairs a 1.14b patch archive with
the 1.14d exe. Settling it needs Blizzard's signed 1.14d patch executable or a Battle.net-updated
install.

**Data source for Phase 3:** build `workspace/merged/` from the 1.14b reference archives (`d2data`,
`d2exp`, LoD `patch_d2`). Their `data/global/` content equals the 1.14d install's, and this way
none of the install's additions can come in.

## Launch path in the 1.14d install (not used by us)

- `DIABLO_II_{ENGLISH,RUSSIAN}.CMD` copy `data\local\Use_eng|Use_rus` over `data\local\Use`, then run
  `PlugY.exe -direct`. PlugY injects `PlugY.dll` into `game.exe` at run time, and D2GL/SGD2FreeRes
  load as `ddraw.dll`/`glide3x.dll` wrappers. The binary on disk stays unpatched.
- `data\local\Use` is one byte: `0x00` in `Use` (current) and `Use_eng`, `0x0B` in `Use_rus`.
  `game.exe` contains the string `data\local\use` and also `D2.LNG`. What the game does with them
  is left to the reverser.
- For runtime experiments, run `game.exe` directly (no PlugY, no wrapper DLLs) so we observe stock
  behaviour. A clean experiment prefix should copy only `game`/`game-unverified` class files plus
  the reference MPQs.

## Open questions

- `[L]` Whether 1.14d's `patch_d2.mpq` content equals 1.14b's (see *Remaining gap*).
- Answered `[I]`: `game.exe` reads loose files under `data/` only with `-direct` (then before every
  MPQ), so the install's on-disk `data/local/` overrides apply only to `-direct` runs
  ([data/0002](../findings/data/0002-mpq-precedence.md#answer-summary)).
- Answered `[I]`: the `data\local\use` byte is a language id (0 `ENG` … 11 `RUS`, > 13 → 0) that
  selects the `data\local\lng\<code>\` string tables and fonts; it touches nothing under
  `data\global\` ([data/0002](../findings/data/0002-mpq-precedence.md#answer-summary)).
