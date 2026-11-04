# Plan 0052 Phase 1b case P1b-2 (docs/findings/ai/0014-community-cross-check.md section 4): the Greater Mummy's search
# callback (0x005F2A00) meets a dead monster. This is a BUILT state (harness placement), on only when AI_P1B2 is set:
# at the callback's entry a candidate in mode 12 whose MonStats record has no unique/champion flag gets the champion
# flag 4 (kind "champ") or the unique flag 8 (kind "uniq", the control), alternating by the order it is first met,
# written to the word at Unit+0x14 -> +0x16 (the word MonTypeFlag, 0x005A0180, tests). One P12 line per placement and
# one per later meeting; the think's own boundary lines (MonSkillTargetOk 0x005FD470, its AIR) show the verdict.
import os
import gdb

P12_REV = 2


def _p12_main():
    if os.environ.get("AI_P1B2", "0") != "1":
        return
    inf = gdb.selected_inferior()
    placed = {}

    def u32(a):
        return int.from_bytes(bytes(inf.read_memory(a, 4)), "little")

    def u16(a):
        return int.from_bytes(bytes(inf.read_memory(a, 2)), "little")

    class Bp(gdb.Breakpoint):
        def __init__(self):
            super().__init__("*0x005F2A00", internal=True)
            self.silent = True

        def stop(self):
            try:
                esp = int(gdb.parse_and_eval("$esp")) & 0xFFFFFFFF
                u = u32(esp + 4)
                if not u or u32(u) != 1 or u32(u + 0x10) != 12:
                    return False
                md = u32(u + 0x14)
                if not md:
                    return False
                uid, cls = u32(u + 0x0C), u32(u + 4)
                w = u16(md + 0x16)
                if uid not in placed:
                    kind = "champ" if len(placed) % 2 == 0 else "uniq"
                    if w & 0x0C:
                        placed[uid] = "native"
                    else:
                        inf.write_memory(md + 0x16, (w | (4 if kind == "champ" else 8)).to_bytes(2, "little"))
                        placed[uid] = kind
                    gdb.write("P12 place u=%d id=%d cls=%d kind=%s flags_before=0x%04X flags_after=0x%04X\n" % (
                        u, uid, cls, placed[uid], w, u16(md + 0x16)))
                else:
                    gdb.write("P12 meet u=%d id=%d cls=%d kind=%s\n" % (u, uid, cls, placed[uid]))
            except Exception as e:
                gdb.write("LOGERR p12 %r\n" % (e,))
            return False

    Bp()
    gdb.write("P12 armed rev %d\n" % P12_REV)


_p12_main()
