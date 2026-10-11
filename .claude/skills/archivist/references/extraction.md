# Extraction procedure

Inputs live in `workspace/reference/installers/` (gitignored; hashes in `docs/formats/installer.md`):

- `1.14d/`: `setup.exe` (Inno Setup 5.5.6 stub) plus `setup-1.bin`/`setup-2.bin` volumes, 2.6 GB.
  Holds the pinned `game.exe`.
- `1.14b-d2/`, `1.14b-d2lod/`: Blizzard digital-download installers (`Installer.exe` plus an
  `Installer Tome.mpq` payload). The integrity reference for MPQ data.

Docs and commits never say where these files came from. Refer to them only by the names above.

## 1. Try innoextract first

```bash
I=workspace/reference/installers/1.14d/setup.exe
mkdir -p workspace/install workspace/logs
innoextract --info "$I" | tee workspace/logs/inno-info.txt
innoextract -l "$I"   # list first; check that real game files appear (Game.exe, *.mpq)
innoextract -e -d workspace/install "$I"
```

Some Inno packages store a single archive (e.g. `data.bin`, `*.arc`) in the payload and unpack
it at install time with ISDone/unarc.dll (FreeArc, Precomp, srep). If the listing shows only
archives and DLLs like `ISDone.dll`, `unarc.dll` or `english.ini`, innoextract alone won't work.
Go to step 2. (The 1.14d installer is plain; step 1 worked.)

The 1.14b Tomes are ordinary MPQs: `smpq -x` them into `workspace/reference/extracted/<name>/`.

## 2. Fallback: install under wine (isolated prefix)

```bash
export WINEPREFIX="$PWD/workspace/wineprefix" WINEARCH=win32   # or win64 if win32 is unsupported
wine "$I"
```

The user may need to click through the GUI. If so, mark it as a `human` step. Then copy the
installed directory (`$WINEPREFIX/drive_c/...`) to `workspace/install/`. Don't let the installer
register anything outside the prefix.

Record which route worked in `docs/formats/installer.md`, including any non-Blizzard files
(loaders, language switchers, mods). If anything modified `Game.exe`, that matters: check its
Authenticode signature (`tools/pe_authenticode.py`) and tell the architect. A patched binary is
still pinnable, but its differences must be documented.

## 3. Inventory

```bash
python3 -I tools/inventory.py workspace/install > docs/inventory.md   # write this tool
```

Columns: relative path, size, sha256, `file(1)` type. Put the **PINNED** row for `Game.exe` at the top.

## 4. MPQs

Expected in 1.14d: `d2data.mpq`, `d2exp.mpq`, `d2char.mpq`, `d2sfx.mpq`, `d2music.mpq`, `d2xmusic.mpq`,
`d2xtalk.mpq`, `d2xvideo.mpq`, `d2speech.mpq`, `d2video.mpq`, `patch_d2.mpq` `[L]`. Verify the set.

```bash
smpq -l workspace/install/patch_d2.mpq            # list (needs the internal (listfile))
smpq -x -C workspace/mpq/patch_d2 workspace/install/patch_d2.mpq   # extract; check smpq --help for flags
```

- If an archive has no `(listfile)`, use a community listfile (a `docs/sources.md` entry) and
  record how many files were recovered compared to the hash-table entry count.
- Build `workspace/merged/` by copying in ascending precedence (d2data → d2exp → patch_d2, as an
  `[L]` precedence) so later archives overwrite earlier ones. Log every overwritten path to
  `workspace/logs/overrides.txt`. That list feeds `docs/formats/mpq.md`.
- To confirm precedence `[C]`, the reverser can anchor the archive open order in `Game.exe`
  (look for strings `patch_d2.mpq`, `d2exp.mpq`).
