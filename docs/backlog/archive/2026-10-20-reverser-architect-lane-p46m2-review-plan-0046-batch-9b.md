---
from: reverser
to: architect
date: 2026-10-20
status: done
context:
  - ../../plans/done/0046-skills-function-catalogue.md
  - ../../findings/skills/0005-missile-do-19-36-damage.md
  - ../../findings/skills/experiments.md#run2026-10-20-cat-emu-9b
resolution: "Reviewed 2026-10-20 (architect): batch 9b accepted with fixes (5). ADR-0021 accepted by the owner: the 18 '(ADR-0021)' claims of skills/0005 raised to [C], each scoped to its named boundary, the code after it [I] (raised in part where a remainder follows). Do 31's CollideKill control for Explosion accepted (no output depends on Explosion; the term stays [I]). Damage 12's packet replacement accepted as 'replaces the damage fields PacketClearDamage zeroes'; the stat-list +0x18 end-frame reading stays [L]. Checks in workspace/logs/skills-cat-9b-review/. Batch 9c may start. Plan 0046 log."
---

Review `lane/p46m2` (from main `2ebd473`; Ghidra copy `workspace/ghidra-p46m2`, no harness): [plan 0046](../../plans/done/0046-skills-function-catalogue.md) Phase 1 batch **9b**, missile server do functions 19–36 and damage functions 1–14. Blocking 9c.

- **Read.** 30 entries (do 24 is do 23's function; damage 6 unused): all in [skills/0005](../../findings/skills/0005-missile-do-19-36-damage.md), with the helpers `0x005A8C70` (the `EType` roll), `0x005A91C0`, `0x005A9270`, `0x0064B0C0`, `0x004E6CA0`, `0x005A99E0` (EBX convention), `0x0056DDE0`, Redemption's callbacks and `0x0058E920` (read only).
- **Draws.** Do 28, 30 (on the target unit's seed), 34, 35, 25 (via `0x005A9820`); damage 3, 5, 12, 13, 14 on the missile seed; none elsewhere before a boundary.
- **Emulation** (run:2026-10-20-cat-emu-9b): 13 families, 17 100 cases, 0 mismatches, 0 undeclared reads, 0 stops. The 9a review's three rules are applied: (a) every 9b model names the return address of each boundary and the checker fails another one; a site control re-checks all 8 762 matched boundary cases with the address changed (all fail; 40 `site` lines in `check.txt`); (b) every family runs two negative controls on different claims, each failing (lowest: `knock` ×3 for ×2, 2, beside `small`/`large` swapped, 60; `dmgelem` undead mask, 12, beside 125; `dmgpkt` `& 0xFF`, 17, beside 53; `reseed9b` swap, 43, beside 304); (c) boundary claims are `[I]` marked "(ADR-0021)", refusal paths that return `[C]`. The damage functions mostly return, so 12 of the 13 damage entries are `[C]` outright (damage 8's call `[I]` (ADR-0021)).
- **Tool.** The same revision of `tools/skills_catalogue_emu.py` reproduces 9a's `check.txt` and `static.txt` from 9a's kept outputs and regenerates 9a's case files byte for byte (`--batch` defaults to 9a). `EmuBoundary.java` unchanged.
- **Symbols.** 38 rows, subsystem `skills/catalogue`; checked against `main` `2ebd473` (no clash; the P1.3 names of do 23, 28, 34, 35 and damage 3 kept).
- **Please check in particular:** § 13's reading that damage 12 replaces the whole packet with one element; § 6/§ 15's `[L]` that a stat list's `+0x18` is the state's end frame; whether the do-31 `Explosion` control replacement (it cannot fail before a boundary) is acceptable.
