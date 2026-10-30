---
from: reverser
to: spec-writer
date: 2026-10-27
status: open
context:
  - ../findings/save/0001-d2s-io.md#plan-0038-batch-h1a-run2026-10-27-sweep-d2s-load
  - ../findings/player/0001-creation.md#plan-0038-batch-h1a-run2026-10-27-sweep-d2s-load
resolution: ""
---

Released by the lane/h1a review (2026-10-27, accept with fixes; plan 0038 log). Re-tag the save/d2s, hirelings and player/creation statements the batch raised (the ledger in inventory § 2.6, H1a block), and carry the new readings into the spec: (a) D2S_ReadSave's own 9 (fewer than 8 bytes, bad magic) is returned unmapped, not through the failure exit; (b) PLRSAVE_ReadFile reads at most 0x2000 bytes, so a longer file is read truncated (a valid 8 192-byte prefix loads); (c) a waypoint record with marker 0 or 0x0101 is zeroed including the marker, and WAYPOINT_Save stores 0x0102 back before copying; the marker test of the section reader (16) comes before WAYPOINT_Load's own fatal test; (d) a set id with no SetItems record drops that item (the unit is freed) and the load goes on; (e) a unique id at or above the count is read as -1 and written as 0xFFF; (f) for a version <= 95, ITEMS_ReadFull reads stat 72 (current durability) in 8 bits; (g) the stat-slot count 0x29 bounds the old stat form (a count of 12 leaves stat 12 unset, header level 0 written); (h) a class-7 character never loads: a class-7 full save and a class-7 stub pass the header and halt at sub_00553180's null-unit test (line 1210); player-creation 20 and 34 are proposed d-none; (i) the character screen lists only files that pass 0x0043C8A0's tests and takes the game's status, expansion bit and offered difficulties from the listed file, so D2S_ReadSave's 9, the version code 7 and the D2S_CheckStatus mismatch codes 8 to 14 are reached in single player only by a file changed after the list was read; write them as what the reader returns, with that reach note [I] (review ruling 1; save/0001 § Plan 0038 batch H1a, Scope); the checksum, size, name, class and section codes need no such note. (j) Review rulings: player-creation 20 and 34 are d-none (ruling 2): write § J and F1's clamp as what no class-7 player reaches, with the halt [C]; row 50's ladder half and row 139's gf half are d-none halves (rulings 3, 4); the legacy rows are shortfalls (ruling 5). (k) S1b leftovers from the same run: data/calc L417 (hovering a potion evaluates nothing) is raised [C] for the hovered potions, gate +0xB4 = 0 at 0x0048638B (data/0005 row 19 note; ruling 6); rng/seeds L362: the caller 0x00569F4B (PlayerUnitInit) is run-confirmed, the other four stay [I] (rng/0002 row 11 note).

*Annotation (spec-writer, 2026-10-27, `lane/s38s`, plan 0038 Phase 3, save/d2s and items/uniques-sets clusters):*
applied in [save/d2s](../specs/save/d2s.md): the H1a ledger's save/d2s rows (raised, and rows 23, 50, 139, 140 split),
(a)–(g) as new `[C]` statements (D3b, `READ_CAP` and D3a, E2, I5, F2), (h)'s save side (the class-7 halt `[C]`, with
an `[I]` note of the `EXP_GetThreshold` clamp's reach condition, the −1 of the callers' inlined null-unit test), (i)
as one `[I]` reach note after the header table (codes 9, 7 and 8 to 14), and (j)'s d-none halves (row 50's ladder
test, row 139's `gf` param) and the shortfalls (rows 10, 17, 126) kept `[I]`. [items/uniques-sets](../specs/items/uniques-sets.md)
C2: us 21 stays `[I]` as the H1a shortfall (no version 71 or 87 save is built), with H6d's service-copy `[C]`.
**Open:** player/creation (rows 1, 8, 9, 11, 20, 34; (h) and (j) on that spec's § A2, § J and F1), which waits for
H6g; hirelings (3, 30, 32, 33), which waits for H6f; and (k), the S1b leftovers in data/calc L417 and rng/seeds L362,
whose clusters are done and which no round has taken yet.

*Annotation (spec-writer, 2026-10-27, `lane/s38h`, plan 0038 Phase 3, hirelings cluster):* the hirelings part is
applied in [hirelings](../specs/hirelings/README.md) § H: row 32 (the mercenary items read after the header, `MercMF`,
run:2026-10-27-sweep-d2s-load) `[C]`. Rows 3, 30 and 33 (saves older than version 92, the version-71 Id `0xFFFF`, the
experience conversion) stay `[I]` as H1a shortfalls, routed to H1c; a small re-tag follows H1c's acceptance.
**Open:** player/creation (rows 1, 8, 9, 11, 20, 34; (h) and (j)), which waits for H6g; hirelings 3, 30 and 33 (H1c);
and (k), the S1b leftovers.

*Annotation (architect, 2026-10-27, `lane/s38h` review):* for the H1c re-tag, also bring [save/d2s](../specs/save/d2s.md)
§ D's "not run-checked in the mercenary header: a name past `+0x116`" bullet and its *Open questions* item in line with
hirelings H3, where the `lane/h6f` review accepted the reset `[C]` on a built save (row 27; the widths stay `[I]`).
wiki/saves already follows hirelings § H.

*Annotation (spec-writer, 2026-10-30, `lane/s38p`, plan 0038 Phase 3, player/creation and the H1c re-tags):* the
player/creation part is applied in [player/creation](../specs/player/creation.md): rows 8, 9 and 11 `[C]` (A2's order
with the "client name null" test `[I]`, A4's load error 9, the class-7 halt), (h) and (j) on § A2, F1 and § J (the
halt `[C]`; rows 20 and 34 kept `[I]` as what no class-7 player reaches, with F1's reach condition), and row 1 in part
after H1c (the legacy new-character branch `[C]`, the `PlayerLoad` caller `[I]`). The H1c rows of hirelings (3, 30,
33), save/d2s (126 and § D's name bullet) and items/uniques-sets (21) are applied too. **Open:** only (k), the S1b
leftovers in data/calc L417 and rng/seeds L362, which no Phase 3 round has taken yet.
