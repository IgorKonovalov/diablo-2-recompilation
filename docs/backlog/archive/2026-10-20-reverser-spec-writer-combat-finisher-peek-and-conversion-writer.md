---
from: reverser
to: spec-writer
date: 2026-10-20
status: done
context:
  - ../../findings/skills/0001-dispatch.md#12-progressive-charges
  - ../../findings/skills/0001-dispatch.md#11-the-skill-packet
  - ../../specs/combat/delivery.md
resolution: "2026-10-20 (spec-writer, lane/cfix): combat/delivery § A2 now says the finisher peeks the attacker's seed (save 0x005D5374, RNG_Step 0x005D537B, restore 0x005D538C), [I], with a reimplementation note and an open question for the srvprgfunc entries and 0x00571AA0; combat/damage § D1 names the skill hit builders as the conversion writers ([I], the old open question struck); combat/README and the combat wiki page follow. [delivery § A](../../specs/combat/delivery.md#a-queue-and-delivery), [damage § D](../../specs/combat/damage.md#d-conversion)"
---

Two combat-spec changes from plan 0045 P1.1 (after the architect's review of
[skills/0001](../../findings/skills/0001-dispatch.md)). Not blocking.

1. [combat/delivery § A2](../../specs/combat/delivery.md): "the progressive-charge finisher, which steps the attacker's
   seed once per charged state" is wrong for the finisher's own step: it copies the seed out, calls `RNG_Step`, and
   copies it back (`0x005D5368`–`0x005D538C`), so the seed is unchanged by it; the `srvprgfunc` entries it then calls
   may draw (not read yet). combat/0001's paragraph carries the dated correction; `[I]`.
2. The packet's conversion fields `+0x65` / `+0x68` have a writer: the skill hit builders set `EType` and `calc4`
   (when calc4 > 0) on a hit (skills/0001 § 11). Where the combat spec lists the conversion as an input with no
   writer, it can point at skills/0001 (the skills spec of plan 0045 Phase 3 will carry the full rule).
