# gdb Python logger for plan 0067 Phase 2 (two-client player trade, cases T1-T13 of
# docs/findings/multiplayer/0003-trade.md § 11). Attach it to the HOST (the TCP/IP host runs the server game, ADR-0008),
# through tools/gdb/two-trade.gdb, after tools/gdb/pilot.py and tools/gdb/two-players.py (the lines tools/d2pilot.py
# steers by). Read-only (ADR-0003): it reads memory and registers and never writes either. One line per event,
# "TAG {json}". Addresses refer to the pinned game.exe (image base 0x400000). Checked by tools/trade_check.py.
#
# Every entry line X and its after line XR (taken at the call's return address, matched by the stack pointer) carry
#   "f"   the game frame (Game +0xA8)
#   "pl"  every player unit of the game (lists at Game +0x1120, next +0xE4, as tools/gdb/two-players.py walks them):
#         id (+0x0C), mode (+0x10), fl (Unit +0xC8 bits 22 and 23 as b22, b23), ia [+0x64 unit id, +0x68 kind,
#         +0x6C valid byte] (PlayerGetInteract 0x00554100), gold (stat 14), lvl (stat 12), cur (the cursor item's id,
#         inventory +0x20, 0 for none), and from PlayerData (Unit +0x14): st +0x50, t54 +0x54, t58 +0x58, b4c +0x4C,
#         rec +0x5C; with a record: r0 +0x00 (snapshot bytes), off +0x0C (gold offer), g10 +0x10 (gold at opening),
#         lk +0x14 (lock time), map [[original id, copy id], ...] (nodes at +0x08: +0, +4, next +8), sha (sha256 of
#         the snapshot's r0 bytes at +0x04, first 16 hex)
#   "inv" {player id: [[item id, class, page (+0x45), x, y, mode, loc (+0x69)], ...]} (the inventory list +0x0C,
#         next ItemData +0x64; x, y from the static path +0x0C, +0x10)
#
#   TRQ/TRQR  sub_00566E60_TradeRequest (ECX game, EDX requester, [esp+4] target); TRQR "pc" is the ret taken:
#             0x00566ED8 event 8, 0x00566F0D event 9 named, 0x00566F55 event 9 unnamed, 0x00567000 opened (1/2),
#             0x00567015 nothing (busy, end lock, a state != 0, the rate) or not in town (a TQN line before it)
#   TQT       0x00566E8F: GetTickCount's value t (EAX)            TQN  0x00567003: not both in town (both cleared)
#   TRB/TRBR  sub_00568060_PktInteractButton (EDX presser, [esp+4] button, [esp+8] param); TRBR "eax"
#   TRA       sub_00566B30_TradeRecAlloc's rets 0x00566BDC (AL 1) and 0x00566BE2 (AL 0): EBX the player, its record
#             and its live list (the snapshot's source)
#   TRO       sub_00567020_TradeOpen entry
#   TIT/TITR  sub_00567620_TradeItemTest (EDX mover, [esp+4] item); TITR at the four rets 0x0056765D, 0x0056768E,
#             0x00567826, 0x0056783B: "pc", "eax"
#   TBL/TBLR  sub_00567840_TradeBeltLock (EDX player); TBLR "eax"
#   TSO/TSOR  sub_00568770_TradeShowOffer (EDX placer, [esp+4] item); TSP 0x005688AF after InvPlaceItem: "ok" EAX,
#             orig EDI, copy [ebp+8], partner ESI, x [ebp-8], y [ebp-4]
#   THO/THOR  sub_00567400_TradeHideOffer (EDX placer, [esp+4] item)
#   TCM/TCMR  sub_00567C70_TradeCommit (EAX A, [esp+8] B); TRT 0x00567DDD after TradeRoomTest: "eax", "side"
#             [ebp-4]; SCP 0x0063E228 in InvScratchPlace after InvSpotFindBySize: "ok", item EBX, x [ebp-8],
#             y [ebp+0xC], "own" the scratch's owner word [EDI+8], "row_of" the unit [ebp+8]; TMP 0x0056718D in
#             TradeMoveItems after InvPlaceItem: "ok", orig EDI, copy ESI and its cell, "to" [ebp+0xC];
#             TMV 0x00567F1C (A to B) and 0x00567F42 (B to A): "al"
#   TCX/TCXR  sub_00567B00_TradeCancel (EDI A, EBX B; "site" its return address names the commit's cancel)
#   TCL/TCLR  sub_005679E0_TradeClose (EDX presser, [esp+4] partner, [esp+0x10] code; "site")
#   TAB/TABR  sub_00568640_TradeAbort (EDX leaver; "site")
#   TRS/TRSR  sub_00566CC0_TradeRestoreSnapshot (EDX player)
#   TTK/TTKR  sub_005689D0_TradeStateTick (EDX player)
#   TSV       sub_00531BB0_SaveItemListOrSnapshot entry (EDX unit, [esp+4] buffer, [esp+8] room, [esp+0xC] flag,
#             "site" the caller); TSC 0x00531BDB after TradeSnapshotCopy: "eax" and the sha256 (16 hex) of the
#             buffer's first EAX bytes ("sha"), to compare with the record's "sha"
#   TMS       sub_0053CAB0_SendTrade77 entry: "code" DL, "site" the return address
#   TG9       sub_0053CBE0_SendGold79 entry: "dl", "arg" [esp+4], "site"
#   TEV       sub_00566D90_TradeEventMsg entry: "ev" DL, "who" ECX's unit id, "site"
#   CRM       sub_00539DA0_ClientRemove entry: ECX, EDX, [esp+4], [esp+8] (the save argument's caller, open question)
#   TRDY      the logger is armed (the runner's ready line, review-fix 16)
import hashlib
import json
import struct

import gdb


def _two_trade_main():
    inf = gdb.selected_inferior()
    st = {"game": 0}
    pend = {}       # return address -> [(entry esp + 4 + popped bytes, tag, context), ...]
    retbp = {}      # return address -> breakpoint

    def mem(a, n):
        return bytes(inf.read_memory(a, n))

    def u8(a):
        return mem(a, 1)[0]

    def u32(a):
        return struct.unpack("<I", mem(a, 4))[0]

    def s32(a):
        return struct.unpack("<i", mem(a, 4))[0]

    def s16(a):
        return struct.unpack("<h", mem(a, 2))[0]

    def reg(n):
        return int(gdb.parse_and_eval("$" + n)) & 0xFFFFFFFF

    def arg(k):
        return u32(reg("esp") + 4 * k)

    def emit(tag, d):
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"))))
        gdb.flush()

    def frame():
        g = st["game"]
        return s32(g + 0xA8) if g else None

    def uid(u):
        try:
            return u32(u + 0x0C) if u else None
        except gdb.MemoryError:
            return None

    # stats as tools/gdb/inventory.py reads them (the list +0x5C, the cache when +0x10 has 0x80000000)
    def stat(u, sid):
        lst = u32(u + 0x5C) if u else 0
        if not lst:
            return None
        cache = bool(u32(lst + 0x10) & 0x80000000)
        arr, n = (u32(lst + 0x48), s16(lst + 0x4C)) if cache else (u32(lst + 0x24), s16(lst + 0x28))
        if not arr or n <= 0 or n > 4096:
            return 0
        for k, v in struct.iter_unpack("<Ii", mem(arr, 8 * n)):
            if k == sid << 16:
                return v
        return 0

    def item(u):
        d = [u32(u + 0x0C), s32(u + 4), None, None, None, u32(u + 0x10), None]
        idata = u32(u + 0x14)
        if idata:
            d[2], d[6] = u8(idata + 0x45), u8(idata + 0x69)
        p = u32(u + 0x2C)
        if p:
            d[3], d[4] = s32(p + 0x0C), s32(p + 0x10)
        return d

    def inv_list(player):
        out = []
        try:
            inv = u32(player + 0x60)
            it, k = (u32(inv + 0x0C) if inv else 0), 0
            while it and k < 300:
                k += 1
                out.append(item(it))
                it = u32(u32(it + 0x14) + 0x64)
        except gdb.MemoryError:
            out.append("err")
        return out

    def record(rec):
        d = {"r0": s32(rec), "off": s32(rec + 0x0C), "g10": s32(rec + 0x10), "lk": u32(rec + 0x14), "map": []}
        n, k = u32(rec + 0x08), 0
        while n and k < 64:
            d["map"].append([u32(n), u32(n + 4)])
            n = u32(n + 8)
            k += 1
        buf = u32(rec + 0x04)
        if buf and 0 < d["r0"] <= 0x2000:
            d["sha"] = hashlib.sha256(mem(buf, d["r0"])).hexdigest()[:16]
        return d

    def player(u):
        fl = u32(u + 0xC8)
        d = {"id": u32(u + 0x0C), "mode": u32(u + 0x10), "b22": (fl >> 22) & 1, "b23": (fl >> 23) & 1,
             "ia": [u32(u + 0x64), u32(u + 0x68), u8(u + 0x6C)], "gold": stat(u, 14), "lvl": stat(u, 12), "cur": 0}
        inv = u32(u + 0x60)
        if inv and u32(inv) == 0x01020304:
            c = u32(inv + 0x20)
            d["cur"] = uid(c) if c else 0
        pd = u32(u + 0x14)
        if pd:
            d.update(st=s32(pd + 0x50), t54=u32(pd + 0x54), t58=u32(pd + 0x58), b4c=u32(pd + 0x4C),
                     rec=u32(pd + 0x5C))
            if d["rec"]:
                d.update(record(d["rec"]))
        return d

    def players():
        g, out = st["game"], []
        if not g:
            return out
        for i in range(128):
            u, n = u32(g + 0x1120 + 4 * i), 0
            while u and n < 64:
                out.append(u)
                u = u32(u + 0xE4)
                n += 1
        return out

    def dump(d, inv=True):
        us = players()
        d["f"] = frame()
        d["pl"] = [player(u) for u in us]
        if inv:
            d["inv"] = {str(u32(u + 0x0C)): inv_list(u) for u in us}
        return d

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.fn = fn

        def stop(self):
            try:
                self.fn()
            except Exception as e:  # never stop the game on a logger error; log it instead
                gdb.write("LOGERR two-trade %r\n" % (e,))
            return False

    def on_ret_at(ra):
        def fn():
            q = pend.get(ra) or []
            sp = reg("esp")
            for k, (want, tag, ctx) in enumerate(q):
                if want == sp:
                    q.pop(k)
                    d = dump(dict(ctx, eax=reg("eax")))
                    emit(tag, d)
                    break
            if not q:
                retbp[ra].enabled = False
        return fn

    def after(tag, popped, ctx):
        """Log TAG at this call's return: the return address [esp], matched by esp = entry esp + 4 + popped."""
        sp = reg("esp")
        ra = u32(sp)
        pend.setdefault(ra, []).append((sp + 4 + popped, tag, ctx))
        if ra in retbp:
            retbp[ra].enabled = True
        else:
            retbp[ra] = Bp(ra, on_ret_at(ra))

    def entry(tag, popped, ctx_fn, inv=True):
        def fn():
            ctx = ctx_fn()
            ctx["site"] = u32(reg("esp"))
            emit(tag, dump(dict(ctx), inv))
            if popped is not None:
                after(tag + "R", popped, ctx)
        return fn

    def on_game():
        st["game"] = reg("edi")

    Bp(0x0052C312, on_game)     # GAME_InitSeeds: EDI the game (as pilot.py's GPTR and two-players.py read it)

    def item_ctx(u):
        return item(u) if u else None

    # the request
    Bp(0x00566E60, entry("TRQ", 4, lambda: {"req": uid(reg("edx")), "tgt": uid(arg(1))}))
    Bp(0x00566E8F, lambda: emit("TQT", {"t": reg("eax"), "f": frame()}))
    Bp(0x00567003, lambda: emit("TQN", {"f": frame()}))
    for pc in (0x00566ED8, 0x00566F0D, 0x00566F55, 0x00567000, 0x00567015):
        Bp(pc, (lambda pc: lambda: emit("TQX", {"pc": pc, "f": frame()}))(pc))

    # the buttons, the record, the window
    Bp(0x00568060, entry("TRB", 8, lambda: {"p": uid(reg("edx")), "button": arg(1), "param": arg(2)}))
    Bp(0x00566BDC, lambda: emit("TRA", dump({"p": uid(reg("ebx")), "ok": reg("eax") & 0xFF})))
    Bp(0x00566BE2, lambda: emit("TRA", dump({"p": uid(reg("ebx")), "ok": reg("eax") & 0xFF})))
    Bp(0x00567020, entry("TRO", None, lambda: {}, inv=False))

    # the change lock, the belt lock, the offer pages
    def tit_ctx():
        it = arg(1)
        return {"p": uid(reg("edx")), "item": item_ctx(it)}

    Bp(0x00567620, entry("TIT", None, tit_ctx))
    for pc in (0x0056765D, 0x0056768E, 0x00567826, 0x0056783B):
        Bp(pc, (lambda pc: lambda: emit("TITR", dump({"pc": pc, "eax": reg("eax")})))(pc))
    Bp(0x00567840, entry("TBL", 0, lambda: {"p": uid(reg("edx"))}, inv=False))
    Bp(0x00568770, entry("TSO", 4, lambda: {"p": uid(reg("edx")), "item": item_ctx(arg(1))}))

    def on_tsp():
        ebp = reg("ebp")
        copy = u32(ebp + 8)
        emit("TSP", {"ok": reg("eax"), "orig": uid(reg("edi")), "copy": uid(copy), "copy_item": item_ctx(copy),
                     "partner": uid(reg("esi")), "x": s32(ebp - 8), "y": s32(ebp - 4), "f": frame()})

    Bp(0x005688AF, on_tsp)
    Bp(0x00567400, entry("THO", 4, lambda: {"p": uid(reg("edx")), "item": item_ctx(arg(1))}))

    # the commit
    Bp(0x00567C70, entry("TCM", 0x10, lambda: {"a": uid(reg("eax")), "b": uid(arg(2))}))
    Bp(0x00567DDD, lambda: emit("TRT", {"eax": reg("eax"), "side": u32(reg("ebp") - 4), "a": uid(reg("edi")),
                                        "b": uid(reg("esi")), "f": frame()}))

    def on_scp():
        ebp, edi = reg("ebp"), reg("edi")
        emit("SCP", {"ok": reg("eax"), "item": item_ctx(reg("ebx")), "x": s32(ebp - 8), "y": s32(ebp + 0x0C),
                     "own": u32(edi + 8), "row_of": uid(u32(ebp + 8)), "f": frame()})

    Bp(0x0063E228, on_scp)

    def on_tmp():
        esi = reg("esi")
        emit("TMP", {"ok": reg("eax"), "orig": uid(reg("edi")), "copy": item_ctx(esi) if esi else None,
                     "to": uid(u32(reg("ebp") + 0x0C)), "f": frame()})

    Bp(0x0056718D, on_tmp)
    Bp(0x00567F1C, lambda: emit("TMV", {"dir": "ab", "al": reg("eax") & 0xFF, "f": frame()}))
    Bp(0x00567F42, lambda: emit("TMV", {"dir": "ba", "al": reg("eax") & 0xFF, "f": frame()}))

    # the ways out
    Bp(0x00567B00, entry("TCX", 8, lambda: {"a": uid(reg("edi")), "b": uid(reg("ebx"))}))
    Bp(0x005679E0, entry("TCL", 0x10, lambda: {"p": uid(reg("edx")), "q": uid(arg(1)), "code": arg(4)}))
    Bp(0x00568640, entry("TAB", 0, lambda: {"p": uid(reg("edx"))}))
    Bp(0x00566CC0, entry("TRS", 0, lambda: {"p": uid(reg("edx"))}, inv=False))
    Bp(0x005689D0, entry("TTK", 8, lambda: {"p": uid(reg("edx"))}))

    # the save
    def on_tsv():
        sp = reg("esp")
        emit("TSV", {"p": uid(reg("edx")), "buf": u32(sp + 4), "room": s32(sp + 8), "flag": u32(sp + 12),
                     "site": u32(sp), "f": frame()})

    def on_tsc():
        n, buf = reg("eax"), reg("ebx")
        d = {"eax": n, "p": uid(reg("esi")), "f": frame()}
        if 0 < n <= 0x2000 and buf:
            d["sha"] = hashlib.sha256(mem(buf, n)).hexdigest()[:16]
        emit("TSC", d)

    Bp(0x00531BB0, on_tsv)
    Bp(0x00531BDB, on_tsc)

    # the messages
    Bp(0x0053CAB0, lambda: emit("TMS", {"code": reg("edx") & 0xFF, "site": arg(0), "f": frame()}))
    Bp(0x0053CBE0, lambda: emit("TG9", {"dl": reg("edx") & 0xFF, "arg": arg(1), "site": arg(0), "f": frame()}))
    Bp(0x00566D90, lambda: emit("TEV", {"ev": reg("edx") & 0xFF, "who": uid(reg("ecx")), "site": arg(0),
                                        "f": frame()}))
    Bp(0x00539DA0, lambda: emit("CRM", {"ecx": reg("ecx"), "edx": reg("edx"), "a1": arg(1), "a2": arg(2),
                                        "site": arg(0), "f": frame()}))

    gdb.write("TWO-TRADE logger armed\n")
    emit("TRDY", {})


_two_trade_main()
