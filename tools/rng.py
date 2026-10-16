"""Reference reimplementation of the Game.exe RNG primitives, and a checker against emulator output.

Usage:
  python3 -I tools/rng.py cases <out.txt> [count] [py-seed]
  python3 -I tools/rng.py check <kind> <cases.txt> <emu-out.txt>
  python3 -I tools/rng.py seedtree <run.log> [...]

The seed is two u32 words {low, high} (struct offset +0 and +4). Primitives, each modelled on one
function in the pinned Game.exe (docs/findings/rng/0001-rng-core.md):
  step      seed = low * 0x6AC690C5 + high (64-bit), low = bits 0..31, high = bits 32..63
  range     if (int32)n < 1: return 0 and leave the seed untouched; else step, return low % n
            (the binary uses low & (n-1) when n is a power of two, which is the same value)
  pow2      step, return low & (n-1)  (no guard; callers pass a power of two)
  init      low = value, high = 666
  init1     low = 1, high = 666

`cases` writes test vectors, one "low high edx" line each (hex u32), with every edge case first
(0, 1, all-ones, carry-out, n <= 0, n = 1, powers of two, n = 0x7FFFFFFF) and then pseudo-random lines.
`check` reads the "eax low high" lines that re/ghidra_scripts/EmuFastcall.java writes when it runs the
binary's own function on the same cases, and compares them line by line with this module. Exit 0 only if every line matches.
`seedtree` checks a runtime log written by tools/d2run.py with tools/gdb/seed-tree.gdb against the
seed-tree derivation (docs/findings/rng/0002-seed-tree.md), predicting every value from the `-seed` N
alone: game seed = init(N), map seed = N; act seed = step(init(N)), +0x470 = its low; Act II tombs =
two range-7 draws (unguarded low % 7) repeated until they differ, + 66; Act III bit = low & 1 of one
more step; level seed = init(+0x470 + levelId) (u32 wrap); room seed = step(init(level low after
its step)), room +0x04 = room low. ACTEND lines are not predicted: the checker reports how many steps
of the act seed separate them from the ACT line. Lines added in plan 0003 Phase 1:
DACT (DUNGEON_ActCreate entry) seed = N, caller 0x0053ACA5 (server) or 0x0044E142 (client);
RRESEED/RACT/AROOM (room activation): the DRLG room seed is re-initialised to init(room +0x04), then
stepped k times by the room-type code (k is reported, not predicted), then once by DRLG_RoomActivate;
the active-room seed = init(that low). SUNITPRE/SUNIT (server unit seed 0x00552DF0): parent pointer =
game +0xD0, unit seed = init(step(parent).low), +0x28 = that low; the parent's position in the game
seed's sequence from init(N) is reported. CUNITPRE/CUNIT (client unit 0x00465FD0): unit seed =
init(step(active room).low); steps since the room's AROOM line are reported.
ENTIN/ENTOUT/GAMECLOCK (tools/gdb/entropy.gdb, a run with -seed 0, i.e. no override): RNG_EntropySeed
= lcg(lcg(lcg(tick + time + salt))) & 0x7FFFFFFF with lcg(x) = x * 0x19660D + 0x3C6EF35F, all mod 2^32;
GAME_InitSeeds' second call is salted with the game seed low after one step of init(first result), and
the map seed is the second result.
Exit 0 only if every predicted value matches. Stdlib only.
"""
import random
import sys

MASK = 0xFFFFFFFF
MULT = 0x6AC690C5
INIT_HIGH = 666


def step(low, high):
    v = low * MULT + high
    return v & MASK, (v >> 32) & MASK


def rng_range(low, high, n):
    """Returns (result, low, high)."""
    if n & 0x80000000 or n == 0:  # (int32)n < 1
        return 0, low, high
    low, high = step(low, high)
    return low % n, low, high


def rng_pow2(low, high, n):
    low, high = step(low, high)
    return low & ((n - 1) & MASK), low, high


def primitive(kind, low, high, edx):
    """Model of one emulated call: returns the (eax, low, high) the binary should produce.
    eax is None where the binary's return value is not meaningful (void functions)."""
    if kind == "step":
        return (None,) + step(low, high)
    if kind == "range":
        return rng_range(low, high, edx)
    if kind == "pow2":
        return rng_pow2(low, high, edx)
    if kind == "init":
        return None, edx, INIT_HIGH
    if kind == "init1":
        return None, 1, INIT_HIGH
    raise SystemExit(f"unknown kind {kind}")


def cases(path, count=5000, pyseed=1):
    rnd = random.Random(pyseed)
    seeds = [(0, 0), (1, 666), (MASK, MASK), (MASK, 0), (0, MASK), (0x80000000, 0x80000000), (0x12345678, 0x29A)]
    ns = [0, 1, 2, 3, 4, 7, 8, 10, 100, 0x10000, 0x7FFFFFFF, 0x80000000, MASK, 0xFFFFFFFE, 0x80000001, 0x40000000]
    lines = [(lo, hi, n) for lo, hi in seeds for n in ns]
    while len(lines) < count:
        r = rnd.random()
        n = rnd.randrange(1, 0x101) if r < 0.4 else (1 << rnd.randrange(0, 32)) if r < 0.6 else rnd.getrandbits(32)
        lines.append((rnd.getrandbits(32), rnd.getrandbits(32), n))
    with open(path, "w") as fh:
        for lo, hi, n in lines:
            fh.write(f"{lo:08x} {hi:08x} {n:08x}\n")
    print(f"{len(lines)} cases -> {path}")


def check(kind, cases_path, emu_path):
    with open(cases_path) as fh:
        inputs = [tuple(int(x, 16) for x in ln.split()) for ln in fh if ln.strip()]
    with open(emu_path) as fh:
        outputs = [tuple(int(x, 16) for x in ln.split()) for ln in fh if ln.strip()]
    if len(inputs) != len(outputs):
        raise SystemExit(f"{len(inputs)} cases but {len(outputs)} emulator lines")
    bad = 0
    for i, ((lo, hi, edx), (eax, elo, ehi)) in enumerate(zip(inputs, outputs)):
        want = primitive(kind, lo, hi, edx)
        got = (eax if want[0] is not None else None, elo, ehi)
        if got != want:
            bad += 1
            if bad <= 10:
                print(f"MISMATCH line {i + 1}: in {lo:08x} {hi:08x} {edx:08x} want {want} got {got}")
    print(f"{kind}: {len(inputs) - bad}/{len(inputs)} match")
    return 0 if bad == 0 else 1


def act_seeds(n, idx):
    """Act seed after DRLG_ActCreate's act-specific draws: (base, low, high, tomb94, tomb484, bit474)."""
    low, high = step(n & MASK, INIT_HIGH)
    base = low
    t94 = t484 = bit = 0
    if idx == 1:
        while True:
            low, high = step(low, high)
            a = low % 7
            low, high = step(low, high)
            b = low % 7
            if a != b:
                break
        t94, t484 = a + 66, b + 66
    elif idx == 2:
        low, high = step(low, high)
        bit = low & 1
    return base, low, high, t94, t484, bit


def steps_between(start, target, limit=5000):
    """Number of steps from seed `start` to seed `target`, or None if not reached within `limit`."""
    if start[0] is None:
        return None
    cur = start
    for k in range(limit + 1):
        if cur == target:
            return k
        cur = step(*cur)
    return None


def parse_kv(line):
    tag, *rest = line.split()
    kv = {}
    for item in rest:
        k, v = item.split("=", 1)
        kv[k] = tuple(int(x, 16) for x in v.split(":")) if ":" in v else v
    return tag, kv


def parse_json_act(line):
    """Plan 0038 H5c: the JSON RRESEED / RACT / AROOM lines of tools/gdb/drlg-roomk.py, in parse_kv's form (pointers
    as hex text, seeds as (low, high), decimal fields as text). Any other JSON line: None."""
    import json
    tag, _, rest = line.partition(" ")
    if tag not in ("RRESEED", "RACT", "AROOM"):
        return None
    d = json.loads(rest)
    sd = lambda v: tuple(int(x, 16) for x in v.split(":"))
    kv = {"room": "%x" % d["room"]}
    if tag == "RRESEED":
        kv["r04"] = "%x" % d["r04"]
    elif tag == "RACT":
        kv.update(r04="%x" % d["r04"], seed=sd(d["seed"]))
        for k in ("f28", "r60"):
            if k in d:
                kv[k] = "%x" % d[k]
        for k in ("fl", "nw", "nf"):
            if d.get(k) is not None:
                kv[k] = str(d[k])
    else:
        kv.update(aroom="%x" % d["aroom"], drlgseed=sd(d["seed"]), aseed=sd(d["aseed"]), flags=str(d["flags"]))
    return tag, kv


# LevelCreate's callers (rng/seeds step note 4; plan 0038 H5c): return address -> function
LEVEL_CALLERS = {0x00642BDA: "LevelEnsure", 0x00642C07: "LevelRoomCount", 0x00642CDB: "RoomFromCoords",
                 0x00642D70: "LevelSetPosition", 0x00642F5B: "ActCreate", 0x00642FE7: "LevelAddRef",
                 0x006430EE: "LevelUnloadCheck"}


def act_model_steps(n, idx, diff):
    """Act-seed steps after the act-specific draws (rng/seeds 3d), from tools/drlg.py's act model (class Act and
    act_links: LevelLinkBuild's level-6 step and Act III's jungle layout). None if the model cannot be loaded."""
    try:
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import drlg
        root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workspace")
        drlg.load_outdoor(os.path.join(root, "merged"), os.path.join(root, "install", "app", "game.exe"))
        A = drlg.Act(idx, n & MASK, diff)
        n0 = A.seed.n
        drlg.act_links(A)
        return A.seed.n - n0
    except Exception as e:  # noqa: BLE001 - report, do not guess
        print(f"  act model unavailable: {e!r}")
        return None


def seedtree(paths):
    diff = 0
    if paths and paths[0].startswith("--diff="):
        diff = int(paths[0].split("=", 1)[1])
        paths = paths[1:]
    bad = total = 0
    model_steps = {}
    for path in paths:
        n = None
        counts = {}
        act_seed = {}
        room_r04, reseed, ract, aroom, pre, game_idx, hists = set(), {}, {}, {}, {}, [], {}
        ent_in, ent_out = [], []
        game_ptr = 0
        # plan 0038 H5c state
        act_levels = {}            # act pointer -> level ids created in it
        actsteps = []              # ACTSTEP lines since the last ACT line
        last_step = None
        ract_fl = {}               # DRLG room -> flags of its last RACT
        no_tile = set()            # DRLG rooms whose RA0 had no floor either (no activation expected)
        cu = {}                    # client unit -> CUNITXY state
        skip_pop = {}              # active room -> 1 while its last NRF had bit 0 set
        nrf_origin = {}            # active room -> flags its AROOM gave it

        def hist(key):
            hists[key] = hists.get(key, 0) + 1
        with open(path) as fh:
            # a log of the plan 0038 H5c logger (LEVEL lines with the caller) also has the ACTSTEP breakpoints
            seen_tags = {"ACTSTEP"} if any(ln.startswith("LEVEL ") and " ra=" in ln for ln in fh) else set()
        with open(path) as fh:
            for ln in fh:
                if ln.startswith("# d2run "):
                    n = int(ln.split("seed=", 1)[1].split()[0])
                    continue
                tag, _, rest = ln.partition(" ")
                if tag in ("RA0", "P0") and rest.startswith("{"):
                    # plan 0038 H5c: drlg-roomk.py RA0 (no wall entry; nf = 0 means no activation) and
                    # mon-spawn.py P0 (the population pass of an active room)
                    import json
                    d = json.loads(rest)
                    if tag == "RA0":
                        if d["nf"] == 0:
                            no_tile.add(d["room"])
                            hist("RA0: room with no wall and no floor entry (6c returns, no draw)")
                        else:
                            hist("RA0: no wall entry, floors present (6c draws)")
                    else:
                        total += 1
                        counts["P0"] = counts.get("P0", 0) + 1
                        hist("population pass (P0) on a room whose last NRF had bit 0 clear" if d["room"] in skip_pop
                             else "population pass (P0), no NRF line before it")
                        if skip_pop.get(d["room"]):
                            bad += 1
                            print(f"MISMATCH {path}: population pass on a room whose flags had bit 0: {ln.strip()[:120]}")
                    continue
                if tag not in ("GAME", "ACT", "ACTEND", "LEVEL", "ROOM", "DACT", "RRESEED", "RACT",
                               "AROOM", "SUNITPRE", "SUNIT", "CUNITPRE", "CUNIT", "ENTIN", "ENTOUT",
                               "GAMECLOCK", "ACTSTEP", "ACTSTEPX", "CUNITXY", "CUNITRM", "CUNITEND", "NRF"):
                    continue
                if n is None:
                    raise SystemExit(f"{path}: no '# d2run seed=' header")
                if rest.startswith("{"):
                    pj = parse_json_act(ln)
                    if pj is None:
                        continue
                    tag, kv = pj
                else:
                    tag, kv = parse_kv(ln)
                hx = lambda k: int(kv[k], 16)
                dec = lambda k: int(kv[k])
                if tag == "GAME":
                    got = (dec("override"), hx("map"), kv["seed"])
                    want = (1, n & MASK, (n & MASK, INIT_HIGH))
                    if "g" in kv:
                        game_ptr = hx("g")
                elif tag == "ENTIN":
                    ent_in.append(kv)
                    continue
                elif tag == "ENTOUT":
                    e = ent_in[-1]
                    x = (int(e["tick"], 16) + int(e["time"], 16) + int(e["salt"], 16)) & MASK
                    for _ in range(3):
                        x = (x * 0x19660D + 0x3C6EF35F) & MASK
                    got, want = hx("v"), x & 0x7FFFFFFF
                    ent_out.append(got)
                elif tag == "GAMECLOCK":
                    # Clock path: game seed = step(init(v1)); second call salted with its low; map = v2.
                    lo, hi = step(ent_out[0], INIT_HIGH)
                    got = (dec("override"), kv["seed"], int(ent_in[1]["salt"], 16), hx("map"))
                    want = (0, (lo, hi), lo, ent_out[1])
                elif tag == "DACT":
                    side = {0x0053ACA5: "server", 0x0044E142: "client"}.get(hx("ret"), "?")
                    hist(f"DACT {side} arg3={kv['arg3']}")
                    got = (hx("seed"), side != "?")
                    want = (n & MASK, True)
                elif tag == "RRESEED":
                    reseed[hx("room")] = hx("r04")
                    if hx("r04") not in room_r04:
                        bad += 1
                        print(f"MISMATCH {path}: re-seeded room has no ROOM line: {ln.strip()}")
                    continue
                elif tag == "RACT":
                    k = steps_between((reseed.pop(hx("room"), None), INIT_HIGH), kv["seed"])
                    hist(f"room-type steps before activation k={k}")
                    got = (k is not None, hx("r04") in room_r04)
                    want = (True, True)
                    ract[hx("room")] = kv["seed"]
                    if "fl" in kv:
                        # plan 0038 H5c, step 6c: flags = 4 if R+0x28 & 0x40000, else 1 if R+0x60 & 1, else 0;
                        # the draw happens only with a wall or floor entry (T+0x18 or T+0x20 non-zero)
                        f28, r60, fl = hx("f28"), hx("r60"), dec("fl")
                        pfl = 4 if f28 & 0x40000 else (1 if r60 & 1 else 0)
                        hist(f"activation flags {fl} (R+0x28 bit 0x40000 {1 if f28 & 0x40000 else 0}, "
                             f"R+0x60 bit 0 {r60 & 1})")
                        got += (fl, dec("nw") + dec("nf") > 0, int(kv["room"], 16) in no_tile)
                        want += (pfl, True, False)
                        ract_fl[hx("room")] = fl
                elif tag == "AROOM":
                    lo, hi = step(*ract.pop(hx("room")))
                    got = (kv["drlgseed"], kv["aseed"])
                    want = ((lo, hi), (lo, INIT_HIGH))
                    aroom[hx("aroom")] = kv["aseed"]
                    if hx("room") in ract_fl:
                        got += (dec("flags"),)
                        want += (ract_fl.pop(hx("room")),)
                    nrf_origin[hx("aroom")] = dec("flags")
                    skip_pop.pop(hx("aroom"), None)
                elif tag == "NRF":
                    fl = dec("flags")
                    room = hx("room")
                    skip_pop[room] = fl & 1
                    o = nrf_origin.get(room)
                    hist(f"NRF {kv['at']}: flags bit 0 {fl & 1} (flags at activation {o})")
                    if fl & 1 == 0:
                        continue
                    continue                # bit 0 set: no population pass may follow for this room (checked at P0)
                elif tag == "ACTSTEP":
                    last_step = (dec("idx"), kv["link"], kv["seed"])
                    continue
                elif tag == "ACTSTEPX":
                    idx, link, before = last_step
                    lo, hi = step(*before)
                    v = (~lo) & 1 if link == "3" else 2 - (lo & 1)
                    hist(f"LevelLinkBuild act-seed step: act {idx} link {link} value {v}")
                    got = (dec("idx"), kv["seed"], dec("v"))
                    want = (idx, (lo, hi), v)
                    actsteps.append(idx)
                    last_step = None
                elif tag == "CUNITXY":
                    x, y = int(kv["x"]), int(kv["y"])
                    cu[hx("unit")] = {"xy": (x, y), "rm": None}
                    hist("client unit (x, y) = (0, 0)" if (x, y) == (0, 0) else "client unit (x, y) != (0, 0)")
                    continue
                elif tag == "CUNITRM":
                    st = cu.get(hx("unit"))
                    got = (st is not None and st["xy"] != (0, 0),)
                    want = (True,)
                    if st is not None:
                        st["rm"] = hx("aroom")
                        if not hx("aroom"):
                            hist("client unit: ClientRoomAt found no room at (x, y) != (0, 0)")
                elif tag == "CUNITEND":
                    st = cu.pop(hx("unit"), None)
                    if st is None:
                        continue
                    room = st["rm"] or 0
                    got = (hx("aroom"),)
                    want = (room,)
                    if not room:
                        got += (kv["useed"],)
                        want += ((1, INIT_HIGH),)
                        hist("client unit without a room: seed stays {1, 666}" + (" (x, y) = (0, 0)" if st["xy"] == (0, 0) else ""))
                elif tag in ("SUNITPRE", "CUNITPRE"):
                    if tag == "SUNITPRE":
                        k = steps_between((n & MASK, INIT_HIGH), kv["pre"], 100000)
                        hist("server unit parent = game +0xD0: " + str(hx("p") == (game_ptr + 0xD0) & MASK))
                        if k is None or hx("p") != (game_ptr + 0xD0) & MASK:
                            bad += 1
                            print(f"MISMATCH {path}: {ln.strip()} (game-seed index {k})")
                        else:
                            game_idx.append((dec("type"), k))
                    else:
                        k = steps_between(aroom.get(hx("aroom"), (None, None)), kv["pre"])
                        hist(f"client unit: steps of its room seed since AROOM k={k if k is None or k < 4 else '4+'}")
                    pre[kv["unit"]] = kv["pre"]
                    continue
                elif tag in ("SUNIT", "CUNIT"):
                    lo, hi = step(*pre.pop(kv["unit"]))
                    got = (kv["post"], kv["useed"], hx("u28"))
                    want = ((lo, hi), (lo, INIT_HIGH), lo)
                elif tag == "ACT":
                    idx = dec("idx")
                    base, lo, hi, t94, t484, bit = act_seeds(n, idx)
                    act_seed[idx] = (lo, hi)
                    actsteps = []
                    if "actp" in kv:
                        act_levels[hx("actp")] = set()
                    got = (hx("map"), hx("base"), kv["seed"], dec("tomb94"), dec("tomb484"), dec("bit474"))
                    want = (n & MASK, base, (lo, hi), t94, t484, bit)
                elif tag == "ACTEND":
                    # Not a prediction: the level-link builder (0x006772C0 and the per-act code under
                    # 0x00678AD0) may step the act seed a data-dependent number of times. Report how many.
                    idx = dec("idx")
                    cur = act_seed.get(idx, act_seeds(n, idx)[1:3])
                    for k in range(5001):
                        if cur == kv["seed"]:
                            break
                        cur = step(*cur)
                    else:
                        k = None
                    print(f"  {path}: act {idx} seed stepped {k if k is not None else '>5000'} times "
                          f"between 0x00642F1A and 0x00642F61")
                    if k is None:
                        bad += 1
                        continue
                    # plan 0038 H5c: the steps are LevelLinkBuild's level-6 step (one ACTSTEP each) and Act III's
                    # jungle layout, as tools/drlg.py's act model replays them
                    if (n, idx) not in model_steps:
                        model_steps[(n, idx)] = act_model_steps(n, idx, diff)
                    m = model_steps[(n, idx)]
                    if m is None:
                        continue
                    hist(f"act {idx}: act-seed steps after the act draws = {k} (model {m}, ACTSTEP lines {len(actsteps)})")
                    got = (k,) + ((k - len(actsteps) if idx != 2 else 0,) if "ACTSTEP" in seen_tags else ())
                    want = (m,) + ((0,) if "ACTSTEP" in seen_tags else ())
                elif tag == "LEVEL":
                    base = act_seeds(n, dec("act"))[0]
                    got = (hx("base"), kv["seed"])
                    want = (base, ((base + dec("id")) & MASK, INIT_HIGH))
                    if "ra" in kv:
                        # plan 0038 H5c: the caller, and no level id created twice in one act
                        caller = LEVEL_CALLERS.get(hx("ra"), "?%s" % kv["ra"])
                        hist(f"LevelCreate caller {caller}")
                        seen = act_levels.setdefault(hx("actp"), set())
                        got += (caller in LEVEL_CALLERS.values(), dec("id") in seen)
                        want += (True, False)
                        seen.add(dec("id"))
                else:  # ROOM
                    room_r04.add(hx("r04"))
                    lo, hi = step(kv["lvlseed"][0], INIT_HIGH)
                    got = (kv["room"], hx("r04"))
                    want = ((lo, hi), lo)
                total += 1
                counts[tag] = counts.get(tag, 0) + 1
                if got != want:
                    bad += 1
                    if bad <= 20:
                        print(f"MISMATCH {path}: {ln.strip()}\n  want {want}\n  got  {got}")
        print(f"{path}: seed={n} " + " ".join(f"{k}={v}" for k, v in sorted(counts.items())))
        for key, v in sorted(hists.items()):
            print(f"  {key}: {v}")
        if game_idx:
            print("  server units (type, index of the game-seed draw from init(N)): "
                  + " ".join(f"{t}:{k + 1}" for t, k in game_idx[:12]) + (" ..." if len(game_idx) > 12 else ""))
    print(f"seedtree: {total - bad}/{total} match")
    return 0 if bad == 0 and total else 1


def main(argv):
    if len(argv) >= 2 and argv[0] == "cases":
        cases(argv[1], *(int(x) for x in argv[2:4]))
        return 0
    if len(argv) == 4 and argv[0] == "check":
        return check(*argv[1:])
    if len(argv) >= 2 and argv[0] == "seedtree":
        return seedtree(argv[1:])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
