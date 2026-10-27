# Animation experiments

Runtime records for [anim/0001](0001-modes-frames.md) and the later animation findings (plan 0050 Phase 2). Harness
and evidence rules: ADR-0003, ADR-0004, ADR-0011, ADR-0013, ADR-0014, ADR-0015, ADR-0021;
[tooling](../../../.claude/skills/reverser/references/tooling.md),
[harness-play](../../../.claude/skills/reverser/references/harness-play.md).

No harness run yet (Phase 2). Emulated runs (ADR-0015, no wine, nothing native):

## run:2026-10-27-anim-rates-emu

- **Question:** (plan 0050 Phase 1, batch P1.2) Does `sub_00621740_AnimRateBonus` map a unit's stat to
  `k s / (k + s)` (truncating) for each entry of `g_AnimRateBonus`, and does `UNIT_AnimAdvance` (a monster, no
  sequence) map frame, length, rate and the record's event bytes to the new frame and event byte as
  [anim/0001 § 8](0001-modes-frames.md#8-the-per-frame-advance) states, taking the rate at each call?
- **Setup:** Ghidra 12.1.2 p-code emulator on the pinned `game.exe` (lane copy `GHIDRA_PROJ_DIR=workspace/ghidra-p50b`,
  heap 3 GB, one instance, each under a 4 GB scope), `re/ghidra_scripts/EmuTrace.java` unchanged (`3255db0c…`). Case
  writers, models and check: `tools/anim_rates.py` `cases`/`check`, every draw from `random.Random("p50b-<family>")`;
  the cases regenerate byte-identical with the tool revision `p50b-commands.txt` names. Families: `bonus` (3 413
  calls, EAX the entry, ECX a scratch unit whose stat list holds the stat with decoys; the DataTables ItemStatCost
  pointer, count and `+0x05` bytes in the spec) and `advance` (1 200 pairs, 2 400 calls, a scratch type-1 unit with
  `+0x30` 0 and a scratch record; the second call of a pair starts from the first's modelled frame with a new rate).
  Guards on the fatal and allocator entries. Files in `workspace/logs/anim/p50b-emu/` and the manifest
  `workspace/logs/anim/p50b-manifest.sha256`; `p50b-emu-dev/` is the development run of an earlier revision, kept,
  not cited.
- **Result:** `check.txt` (`3566d9da…`): `FAMILY bonus cases=3413 bad=0 stops=0 reads_outside=0` (positive 2 569,
  negative 832, zero 12); `FAMILY advance cases=2400 bad=0 stops=0 reads_outside=0` (wraps 490, event bytes 1–4
  taken 205, 1 120 pairs with a changed rate of which 1 114 would mismatch under the old one); `SCAN check bad=0`.
- **Covers:** the two maps above, nothing about what the game stores in those fields or when it calls them
  (ADR-0015). Not covered: `s = −k` (a divide fault), the advance's sequence branch, a player, a start frame other
  than 0. Used by [anim/0002 §§ 2, 6](0002-rates.md).
