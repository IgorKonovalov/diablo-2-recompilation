# Format experiments

Owned by `archivist`. Runs whose claim is about a file format's bytes: a save written and reloaded, a
parser-edited file loaded in the game (evidence-rules § Experiments). Runs about game code go in
`docs/findings/<subsystem>/experiments.md`. Each record follows ADR-0003: exact command lines, the
steps, and the raw-log path or a statement that none was kept.

Common setup for every run here: the plan 0003 harness (`.claude/skills/reverser/references/tooling.md`
§ Runtime harness). wine 11 (new wow64), prefix `workspace/wineprefix`, rootful Xwayland `:7`, pinned
`game.exe` in `workspace/runtime/game/`. Saves are written to
`workspace/wineprefix/drive_c/users/$USER/Saved Games/Diablo II/`. No debugger and no breakpoints.
Input goes through `tools/xdrive.py --display :7 --window "Diablo II"` (window-relative clicks on
the 800×600 window).

## run:2026-10-11-d2s-samples

- **Question:** what does the pinned game write for a new character, for a fresh character after
  *Save and Exit*, and for items of every quality? These are the samples for
  [d2s.md](d2s.md#samples).
- **Setup:**
  - Stock saves: game dir `workspace/runtime/game/`, unmodified data.
  - Item saves: game dir `workspace/runtime/game-mod/`. Every entry is symlinked from `game/`, plus a
    real `data/global/excel/` that holds the two edited tables:
    `python3 -I tools/d2s_samples.py workspace/merged/data/global/excel workspace/runtime/game-mod/data/global/excel <variant>`.
    The variant per sample is in [d2s.md § Samples](d2s.md#samples) (`lvl1` for `qit1ama`, `a`
    for `qitnec` and `qitbar`, `b` for the rest). The `b` output is byte-identical to the tables now
    in `game-mod`.
  - Launch, as `tools/d2run.py` starts the game (its step 2), from the game dir:
    `WINEPREFIX=workspace/wineprefix DISPLAY=:7 wine game.exe -w -ns`, with `-direct -txt` added for
    `game-mod`. Whether a `-seed N` switch was also given was not recorded. The seed changes item
    seeds and rolls, not the layout.
- **Procedure:**
  1. Character: main menu → *Single Player* (`click 400 307`) → *Create New Character* → class →
     type the name (`type <name>`) → *OK*. The game writes the 335-byte stub at this point.
  2. In Act I town: `key Escape` → *Save and Exit Game*. The full save replaces the stub.
  3. Item saves only, before step 2: `key i`, `rclick` the cube to open it, move the Scroll of
     Identify into it, *Transmute*, then close the panels.
  4. `qitbarb` only: Tir, then El, socketed into the sword by hand, then step 2.
  5. Copy each `.d2s` to `workspace/samples/d2s/`. The two stubs are the files of characters
     `seedtest` and `uiu` as created, copied before their first *Save and Exit* as
     `stub-<name>.d2s`.

  The *Single Player* coordinate is the one in `tools/gdb/enter-sp.steps`. The click coordinates
  used on the class screen, the name field, the cube and the inventory were sent one command at a
  time and not recorded. No steps file was kept. A rerun must re-measure them from a screenshot
  (`xdrive.py shot`).
- **Observed:** 19 files, sha256 in [d2s.md § Sample hashes](d2s.md#sample-hashes). File times
  (`saves-backup/p0005/` and the copies) give the order: `smp*` (18:17–18:21), `qit1ama`, then
  `qitama`, `qitasn`, `qitnec`, `qitbar`, `qitpal`, `qitdru`, `qitsor` (18:28–18:33, variant `a`),
  then `qitnecb` and `qitbarb` (18:35–18:37, variant `b`). Variants `a` and `b` differ only in the
  Necromancer and Barbarian recipes.
  The tooltip of the `qitbarb` sword read "Steel … Ethereal (Cannot be Repaired), Socketed (2)".
  `python3 -I tools/d2s.py survey workspace/merged/data/global/excel workspace/samples/d2s/*.d2s`
  exits 0. In `qit1ama` the three level-1 cube outputs are a rare ring, a rare amulet and a magic
  ring (quality 6, 6, 4), from a recipe asking for `rin,uni`, `amu,rar` and *Angelic Halo*.
- **Raw log:** none kept. No screenshots kept. The saves are the record: `workspace/samples/d2s/`,
  plus the `.key`/`.ma0`/`.map` side files of the item and fresh saves in
  `workspace/runtime/saves-backup/p0005/`.
- **Conclusion:** gives the sample set behind the `[C]` layout rows of [d2s.md](d2s.md). The
  level-1 unique/set fallback is creation behaviour, `[L]` in d2s.md until a code anchor exists
  (backlog D2S (a)).

## run:2026-10-11-d2s-edit

- **Question:** does the game load a save rewritten by `tools/d2s.py`, and does it check the checksum?
- **Setup:** game dir `workspace/runtime/game/` (stock data), launched as in
  run:2026-10-11-d2s-samples without `-direct -txt`. Inputs: `workspace/samples/d2s/smpbar.d2s` and
  `smpsor.d2s` from that run. Outputs in `workspace/samples/d2s-edited/`.
- **Procedure:**
  1. `python3 -I tools/d2s.py setstat workspace/merged/data/global/excel workspace/samples/d2s/smpbar.d2s workspace/samples/d2s-edited/smpbar.d2s 0 45`.
     `cmp -l` against the original: offset `0x300` (one byte of the stat stream) and the checksum
     bytes `0x0E`–`0x0F`.
  2. `d2s-edited/smpsor.d2s`: `smpsor.d2s` with the byte at `0x2B` (header `level`) changed from 1
     to 2, and the checksum **not** fixed (`cmp -l`: only offset `0x2B`).
  3. `d2s-edited/smpsor-fixed.d2s`: the same bytes with the checksum recomputed
     (`d2s.py checksum` to compute it; `cmp -l` against step 2: only offset `0x0E`).
  4. For each file: put it alone in the save directory under its character's name, launch, then
     *Single Player* → select → *OK* (the sequence of `tools/gdb/enter-sp.steps`), then `key c` for
     the character screen. If the game was entered, `key Escape` → *Save and Exit Game*, and copy the
     written file back as `d2s-edited/<name>-resaved.d2s`.
- **Observed:**
  1. `smpbar` entered the game. The character screen showed Strength **45**.
  2. `smpsor` showed "Level 2 Sorceress" on the select screen. *OK* gave "Unable to enter game,
     generic bad file".
  3. `smpsor-fixed` entered the game.

  Both re-saved files have valid checksums (`d2s.py survey` exits 0 on them).
  `smpsor-resaved.d2s` has header `level` 1 again.
- **Raw log:** none kept. No screenshots kept. The five files in `workspace/samples/d2s-edited/`
  (sha256 in [d2s.md § Sample hashes](d2s.md#sample-hashes)) are the record.
- **Conclusion:** confirms the checksum algorithm and the stat-stream layout `[C]` in
  [d2s.md](d2s.md#checksum): the game accepts a parser-written save. The checksum alone accounts
  for the refusal in (2), because (3) has the same level mismatch and loads. Three behaviour
  observations stay `[L]` in d2s.md until a code anchor exists (backlog D2S (a)): the select screen
  skips the checksum, entering the game refuses a bad one, and the save rewrites the header level.
