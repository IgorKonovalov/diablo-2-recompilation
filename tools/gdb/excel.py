# gdb Python logger for plan 0038 batch H3b (data-load): the file layer, the archive opens, the language byte, the
# string-table load and release, the excel load and two table lookups, from program start on. Meant for a game started
# with tools/d2run.py --early (gdb on the game before its startup code; plan 0038 inventory § 7, review ruling 3), but
# it works attached late too: XATT says which. Sourced by tools/gdb/excel.gdb after tools/gdb/pilot.py and
# tools/gdb/strings.py. One line per event, "TAG {json}"; every line carries "th" (the gdb thread number). Addresses
# refer to the pinned game.exe (image base 0x400000); the findings are docs/findings/data/0001-0003.
#
#   XATT  at source time: Storm's archive list head (0x0070835C), the d2data handle (0x007D561C), the string buffer
#         (0x008829B4), the language flag and byte (0x008829F0, 0x008829EC), Storm's direct flags (0x00779058),
#         g_bDirect (0x0074C82C), g_DataTblsCompileTxt (0x0096C8B4); "early" = all of them 0 (nothing has run yet)
#   XIFI  sub_00406870_InitFileIO (ECX, EDX) and, at its return, the two direct flags it writes
#   XARC  MPQ_OpenArchive 0x00517332 (ECX name, EDX flags, [ESP+4] retry callback, [ESP+8] priority) and its return
#         (EAX wrapper, [wrapper] Storm handle), then XLST: Storm's archive list front to back (node, priority +0x118,
#         flag +0x114, +0x258), walked by +4 from the head
#   XOPN  MPQ_OpenCoreArchives 0x004FAB90, MPQ_OpenGameArchives 0x004FAEC0, MPQ_OpenVideoArchives 0x004FAD10: entry
#         (caller) and return (EAX), each followed by an XLST
#   XLNG  LNG_GetLanguageIndex 0x00525150: the calls made while the flag 0x008829F0 is 0 at entry, and the first 8
#         calls, each with its return; later calls only count per caller (XSTAT), with the cached byte re-read
#   XFLW  FILE_LoadWhole 0x00517079 (ECX pool, EDX path, [ESP+4] size out): path, caller, and at 0x005170D5 the
#         buffer (EBX) and size (ESI), its sha256 and first 16 bytes, and the STORM_FindFile results inside the call;
#         a failed load (return 0) has buf 0
#   XFF   STORM_FindFile 0x00417F10 (ECX archive or 0, [ESP+4] name, [ESP+8] flags, [ESP+0xC] archive out): a line for
#         every call inside a FILE_LoadWhole (carried in its XFLW), every call whose name is under data\global\excel
#         or data\local, and every call that returns 2 (disk); every call is counted per (return, archive) in XSTAT
#   XTXT  sub_0044D9C0_ApplyTxtOption (ECX config: the byte at +0x215) and g_DataTblsCompileTxt after it
#   XDTA  DATATBLS_LoadAll 0x00619300 entry (three stack arguments, caller) and return; XTBL DATATBLS_LoadTable
#         0x006122F0 per call (name, record size, caller, the return: records, count), numbered within the LoadAll
#   XDMP  at each DATATBLS_LoadAll return and at the unload call 0x0044B971 (phase "load" / "unload"): items, monstats,
#         levels, charstats and gems record arrays written whole to $H3B_DUMP/<n>-<phase>-<table>.bin (when the
#         variable names a directory), with count, record size and sha256
#   XSLA  STRTABLE_LoadAll 0x005259C0 (EDX language code or 0, [ESP+4] expansionLoad) with the reference count
#         (0x008829D8) and the three buffers before and after; XSUL STRTABLE_Unload 0x00524E40 likewise
#   XIGC  ITEMS_GetByCode 0x00633640 ([ESP+4] code, [ESP+8] index out): one line per distinct (code, caller) with the
#         return and the index
#   XTCN  EXCEL_FindName 0x006BD3C0 on g_TCLink (0x0096C5E8): one line per distinct (name, caller) with the return;
#         XTCG TC_GetByName 0x00654DD0 (no reference in the image) per hit
#   XSTAT every 30 s and at the first event: counts
import hashlib
import json
import os
import struct
import time

import gdb


def _excel_main():
    inf = gdb.selected_inferior()
    dump_dir = os.environ.get("H3B_DUMP") or None
    if dump_dir and not os.path.isdir(dump_dir):
        dump_dir = None
    st = {"t0": time.time(), "last": 0.0, "ff": {}, "ff_calls": 0, "ff_disk": 0, "lng": {}, "lng_calls": 0,
          "igc_calls": 0, "tcn_calls": 0, "tcg_calls": 0, "flw": 0, "loadall": 0, "dumps": 0}
    pend = {}          # (thread, kind) -> list of (entry esp, data)
    seen_igc, seen_tcn = set(), set()
    ret_bps = {}

    def mem(a, n):
        return bytes(inf.read_memory(a, n))

    def u32(a):
        return struct.unpack("<I", mem(a, 4))[0]

    def reg(n):
        return int(gdb.parse_and_eval("$" + n)) & 0xFFFFFFFF

    def thn():
        t = gdb.selected_thread()
        return t.num if t else 0

    def emit(tag, d):
        d["th"] = thn()
        gdb.write("%s %s\n" % (tag, json.dumps(d, separators=(",", ":"), ensure_ascii=True)))

    def stat(force=False):
        now = time.time()
        if force or now - st["last"] >= 30:
            st["last"] = now
            emit("XSTAT", {"t": round(now - st["t0"], 1), "ff_calls": st["ff_calls"], "ff_disk": st["ff_disk"],
                           "ff": {k: v for k, v in sorted(st["ff"].items())}, "lng_calls": st["lng_calls"],
                           "lng_ra": {"%x" % k: v for k, v in sorted(st["lng"].items())},
                           "lng_byte": u32(0x008829EC) & 0xFF, "lng_flag": u32(0x008829F0),
                           "igc_calls": st["igc_calls"], "tcn_calls": st["tcn_calls"], "tcg_calls": st["tcg_calls"],
                           "flw": st["flw"], "loadall": st["loadall"], "dumps": st["dumps"]})

    def cstr(a, cap=512):
        if not a:
            return None
        out = b""
        while len(out) < cap:
            chunk = mem(a + len(out), 64)
            z = chunk.find(b"\0")
            if z >= 0:
                return (out + chunk[:z]).decode("latin-1")
            out += chunk
        return out.decode("latin-1")

    def arclist():
        out, node, n = [], u32(0x0070835C), 0
        while node and node < 0x80000000 and n < 64:
            out.append(["%08x" % node, u32(node + 0x118), u32(node + 0x114), u32(node + 0x258)])
            node = u32(node + 4)
            n += 1
        return out

    class Bp(gdb.Breakpoint):
        def __init__(self, addr, fn):
            super().__init__("*0x%08X" % addr, internal=True)
            self.silent = True
            self.fn = fn
            self.addr = addr

        def stop(self):
            try:
                self.fn(self.addr)
            except Exception as e:  # never stop the game on a logger error; log it instead
                gdb.write("LOGERR excel %r\n" % (e,))
            return False

    def on_ret_addr(addr):
        """A breakpoint at a return address: pop the newest pending call of this thread whose entry esp lies below
        the current esp (the callee has returned past it) and was made from this address."""
        esp, th = reg("esp"), thn()
        for key in [k for k in pend if k[0] == th]:
            lst = pend[key]
            for i in range(len(lst) - 1, -1, -1):
                e_esp, ra, data, cb = lst[i]
                if ra == addr and e_esp < esp:
                    del lst[i]
                    cb(data)
                    return

    def hook_return(kind, data, cb):
        esp = reg("esp")
        ra = u32(esp)
        pend.setdefault((thn(), kind), []).append((esp, ra, data, cb))
        if ra not in ret_bps:
            ret_bps[ra] = Bp(ra, on_ret_addr)
        return ra

    def top(kind):
        lst = pend.get((thn(), kind))
        return lst[-1][2] if lst else None

    # --- attach state ----------------------------------------------------------------------------------------------
    att = {"list": u32(0x0070835C), "d2data": u32(0x007D561C), "strtbl": u32(0x008829B4), "lng_flag": u32(0x008829F0),
           "lng_byte": u32(0x008829EC) & 0xFF, "storm_direct": u32(0x00779058), "direct": u32(0x0074C82C),
           "compile_txt": u32(0x0096C8B4)}
    att["early"] = not any(att.values())
    emit("XATT", att)

    # --- file I/O mode -----------------------------------------------------------------------------------------------
    def on_ifi(_):
        d = {"ecx": reg("ecx"), "edx": reg("edx")}
        d["ra"] = hook_return("ifi", d, lambda d: emit("XIFI", dict(d, storm_direct=u32(0x00779058),
                                                                     direct=u32(0x0074C82C))))

    # --- archives --------------------------------------------------------------------------------------------------
    def on_arc(_):
        esp = reg("esp")
        d = {"name": cstr(reg("ecx")), "flags": reg("edx"), "retry": u32(esp + 4), "prio": u32(esp + 8)}

        def done(d):
            w = reg("eax")
            d.update({"ret": w, "storm": u32(w) if w else 0})
            emit("XARC", d)
            emit("XLST", {"after": d["name"], "list": arclist()})
        d["ra"] = hook_return("arc", d, done)

    def on_opn(name):
        def f(_):
            d = {"fn": name}

            def done(d):
                emit("XOPN", dict(d, ret=reg("eax")))
                emit("XLST", {"after": name, "list": arclist()})
            d["ra"] = hook_return("opn", d, done)
            emit("XOPN", dict(d, phase="entry"))
        return f

    # --- language byte -----------------------------------------------------------------------------------------------
    def on_lng(_):
        st["lng_calls"] += 1
        ra = u32(reg("esp"))
        st["lng"][ra] = st["lng"].get(ra, 0) + 1
        flag = u32(0x008829F0)
        if flag == 0 or st["lng_calls"] <= 8:
            d = {"n": st["lng_calls"], "flag_in": flag, "byte_in": u32(0x008829EC) & 0xFF}
            d["ra"] = hook_return("lng", d, lambda d: emit("XLNG", dict(d, ret=reg("eax"), flag=u32(0x008829F0),
                                                                     byte=u32(0x008829EC) & 0xFF)))
        stat(st["lng_calls"] == 1)

    # --- whole-file loads and the file lookup ------------------------------------------------------------------------
    def on_flw(_):
        st["flw"] += 1
        d = {"path": cstr(reg("edx")), "pool": reg("ecx"), "buf": 0, "size": None, "ff": []}
        d["ra"] = hook_return("flw", d, flw_done)

    def on_flw_ok(_):
        d = top("flw")
        if d is not None:
            d["buf"], d["size"] = reg("ebx"), reg("esi")

    def flw_done(d):
        buf, size = d["buf"], d["size"]
        if buf and size is not None:
            data = mem(buf, size) if size <= (16 << 20) else b""
            d["sha256"] = hashlib.sha256(data).hexdigest() if data else None
            d["head"] = data[:16].hex()
        d["ret"] = reg("eax")
        emit("XFLW", d)
        stat()

    def on_ff(_):
        esp = reg("esp")
        d = {"name": cstr(u32(esp + 4)), "flags": u32(esp + 8), "arc_in": reg("ecx"), "outp": u32(esp + 12)}
        d["ra"] = hook_return("ff", d, ff_done)

    def ff_done(d):
        st["ff_calls"] += 1
        r = reg("eax")
        arc = u32(d["outp"]) if d["outp"] and r == 1 else 0
        key = "%d:%08x" % (r, arc)
        st["ff"][key] = st["ff"].get(key, 0) + 1
        if r == 2:
            st["ff_disk"] += 1
        rec = {"name": d["name"], "flags": d["flags"], "arc_in": d["arc_in"], "ret": r, "arc": "%08x" % arc,
               "ra": d["ra"]}
        f = top("flw")
        if f is not None:
            f["ff"].append(rec)
        nm = (d["name"] or "").lower().replace("/", "\\")
        if r == 2 or nm.startswith("data\\global\\excel") or nm.startswith("data\\local"):
            emit("XFF", rec)

    # --- -txt --------------------------------------------------------------------------------------------------------
    def on_txt(_):
        cfg = reg("ecx")
        d = {"cfg_txt": mem(cfg + 0x215, 1)[0], "before": u32(0x0096C8B4)}
        d["ra"] = hook_return("txt", d, lambda d: emit("XTXT", dict(d, after=u32(0x0096C8B4))))

    # --- excel load --------------------------------------------------------------------------------------------------
    TABLES = (("items", 0x0096CA5C, 0x0096CA58, 0x1A8), ("monstats", 0x0096C6A8, 0x0096C6B0, 0x1A8),
              ("levels", 0x0096C888, 0x0096C88C, 0x220), ("charstats", 0x0096C7F4, 0x0096C7F8, 0xC4),
              ("gems", 0x0096CA94, 0x0096CA90, 0xC0))
    seq = {"n": 0}

    def dumps(phase):
        st["dumps"] += 1
        for name, pa, ca, rs in TABLES:
            p, n = u32(pa), u32(ca)
            d = {"phase": phase, "loadall": st["loadall"], "table": name, "ptr": p, "count": n, "rec": rs}
            if p and 0 < n < 100000:
                data = mem(p, n * rs)
                d["sha256"] = hashlib.sha256(data).hexdigest()
                if dump_dir:
                    fn = "%d-%s-%s.bin" % (st["loadall"], phase, name)
                    with open(os.path.join(dump_dir, fn), "wb") as fh:
                        fh.write(data)
                    d["file"] = fn
            emit("XDMP", d)

    def on_dta(_):
        esp = reg("esp")
        st["loadall"] += 1
        seq["n"] = 0
        d = {"n": st["loadall"], "args": [u32(esp + 4), u32(esp + 8), u32(esp + 12)]}

        def done(d):
            emit("XDTA", dict(d, phase="return", tables=seq["n"]))
            dumps("load")
        d["ra"] = hook_return("dta", d, done)
        emit("XDTA", dict(d, phase="entry"))

    def on_tbl(_):
        esp = reg("esp")
        seq["n"] += 1
        d = {"loadall": st["loadall"], "seq": seq["n"], "name": cstr(u32(esp + 8)), "rec": u32(esp + 20),
             "pcount": u32(esp + 16)}

        def done(d):
            r = reg("eax")
            pc = d.pop("pcount")
            emit("XTBL", dict(d, ret=r, count=u32(pc) if pc else None))
        d["ra"] = hook_return("tbl", d, done)

    def on_unload_call(_):
        dumps("unload")

    # --- string tables -----------------------------------------------------------------------------------------------
    def strstate():
        return {"ref": u32(0x008829D8), "s": u32(0x008829B4), "p": u32(0x008829D0), "x": u32(0x008829D4)}

    def on_sla(_):
        esp = reg("esp")
        edx = reg("edx")
        d = {"lang": cstr(edx) if edx else None, "exp": u32(esp + 4), "before": strstate()}
        d["ra"] = hook_return("sla", d, lambda d: emit("XSLA", dict(d, ret=reg("eax"), after=strstate())))

    def on_sul(_):
        d = {"before": strstate()}
        d["ra"] = hook_return("sul", d, lambda d: emit("XSUL", dict(d, after=strstate())))

    # --- lookups -----------------------------------------------------------------------------------------------------
    def on_igc(_):
        st["igc_calls"] += 1
        esp = reg("esp")
        code, pi, ra = u32(esp + 4), u32(esp + 8), u32(esp)
        if (code, ra) in seen_igc:
            return
        seen_igc.add((code, ra))
        d = {"code": code, "text": struct.pack("<I", code).decode("latin-1"), "pidx": pi}

        def done(d):
            pi = d.pop("pidx")
            emit("XIGC", dict(d, ret=reg("eax"), idx=u32(pi) if pi else None, items=u32(0x0096CA5C)))
        d["ra"] = hook_return("igc", d, done)

    def on_fname(_):
        esp = reg("esp")
        if u32(esp + 4) != u32(0x0096C5E8):
            return
        st["tcn_calls"] += 1
        name, ra = cstr(u32(esp + 8)), u32(esp)
        if (name, ra) in seen_tcn:
            return
        seen_tcn.add((name, ra))
        d = {"name": name}
        d["ra"] = hook_return("tcn", d, lambda d: emit("XTCN", dict(d, ret=reg("eax"))))

    def on_tcg(_):
        st["tcg_calls"] += 1
        emit("XTCG", {"name": cstr(u32(reg("esp") + 4)), "ra": u32(reg("esp"))})

    Bp(0x00406870, on_ifi)
    Bp(0x00517332, on_arc)
    Bp(0x004FAB90, on_opn("core"))
    Bp(0x004FAEC0, on_opn("game"))
    Bp(0x004FAD10, on_opn("video"))
    Bp(0x00525150, on_lng)
    Bp(0x00517079, on_flw)
    Bp(0x005170D5, on_flw_ok)
    Bp(0x00417F10, on_ff)
    Bp(0x0044D9C0, on_txt)
    Bp(0x00619300, on_dta)
    Bp(0x006122F0, on_tbl)
    Bp(0x0044B971, on_unload_call)
    Bp(0x005259C0, on_sla)
    Bp(0x00524E40, on_sul)
    Bp(0x00633640, on_igc)
    Bp(0x006BD3C0, on_fname)
    Bp(0x00654DD0, on_tcg)
    gdb.write("EXCEL logger armed\n")


_excel_main()
