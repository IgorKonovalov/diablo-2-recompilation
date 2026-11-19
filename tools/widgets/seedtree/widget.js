// widget-only/1
// Seed tree expander. A small tool of our own that restates the seed tree of the randomness page: the map seed N
// builds the acts, each act's seed is Init(N) stepped once (its low word is the level seed
// start), a level's seed is
// Init(start + level id) with no draw, and each room of a level takes one draw on the level seed, then starts its own
// seed from the result and steps once. Act II then draws pairs mod 7 until they differ, Act III draws one more time.
// Every value shown is computed by our model in this page, from the number typed here; none is observed in the
// game, and the seed offered is illustrative. Level and room numbers are plain counters of our own.

const NAME = "seedtree";

function toInt(value, lo, hi, fallback) {
  const v = Math.trunc(Number(value));
  if (!Number.isFinite(v)) return fallback;
  return Math.min(hi, Math.max(lo, v));
}

// One Step of the generator on a pair of 32-bit words: low * multiplier + high, in 64 bits.
function step(seed, mult) {
  const v = BigInt(seed.low) * mult + BigInt(seed.high);
  seed.low = Number(BigInt.asUintN(32, v));
  seed.high = Number(BigInt.asUintN(32, v >> 32n));
  return seed.low;
}

// The pure part: no page access. inputs: { seed, act, level, rooms }; the parsed widget.json is the second argument.
export function compute(inputs, data) {
  const lim = data.inputs;
  const rule = data.rule;
  const seed = toInt(inputs.seed, lim.seed.min, lim.seed.max, lim.seed.default);
  const act = toInt(inputs.act, lim.act.min, lim.act.max, lim.act.default);
  const level = toInt(inputs.level, lim.level.min, lim.level.max, lim.level.default);
  const rooms = toInt(inputs.rooms, lim.rooms.min, lim.rooms.max, lim.rooms.default);
  const mult = BigInt("0x" + rule.multiplier);
  const acts = [];
  for (let i = 0; i < data.acts.items.length; i++) {
    const a = { low: seed >>> 0, high: rule.initHigh };
    step(a, mult);
    const seedBase = a.low;
    let draws = 1;
    let tombs = null;
    let bit = null;
    if (i === rule.tombAct) {
      for (;;) {
        const x = step(a, mult) % rule.tombMod;
        const y = step(a, mult) % rule.tombMod;
        draws += 2;
        if (x !== y) {
          tombs = [x + rule.tombBase, y + rule.tombBase];
          break;
        }
      }
    } else if (i === rule.gateAct) {
      bit = step(a, mult) & 1;
      draws += 1;
    }
    acts.push({ idx: i, lead: seedBase, draws, tombs, bit });
  }
  const seedBase = acts.at(act).lead;
  const levelSum = (seedBase + level) >>> 0;
  const ls = { low: levelSum, high: rule.initHigh };
  const roomRows = [];
  for (let k = 1; k <= rooms; k++) {
    step(ls, mult);
    const rs = { low: ls.low, high: rule.initHigh };
    step(rs, mult);
    roomRows.push({ k, levelLow: ls.low, levelHigh: ls.high, roomLow: rs.low, roomHigh: rs.high });
  }
  return {
    seed, act, level, rooms,
    game: { low: seed >>> 0, high: rule.initHigh },
    acts,
    levelSeed: { lead: seedBase, id: level, sum: levelSum, high: rule.initHigh },
    roomRows,
  };
}

function hex8(v) {
  return v.toString(16).toUpperCase().padStart(8, "0");
}

function make(el, text, cls) {
  if (text !== undefined) el.textContent = text;
  if (cls) el.className = cls;
  return el;
}

function td(text) {
  return make(document.createElement("td"), text);
}

function field(form, id, label, spec, value) {
  const wrap = make(document.createElement("div"), undefined, "widget-field");
  const lab = make(document.createElement("label"), label);
  lab.htmlFor = id;
  const inp = document.createElement("input");
  inp.type = "number";
  inp.id = id;
  inp.min = String(spec.min);
  inp.max = String(spec.max);
  inp.step = "1";
  inp.value = String(value);
  wrap.append(lab, inp);
  form.append(wrap);
  return inp;
}

export function mount(element, data) {
  const t = data.text;
  const uid = "w-" + NAME + "-" + Math.floor(Math.random() * 1e9);
  const root = make(document.createElement("div"), undefined, "widget-body");
  root.append(make(document.createElement("p"), t.intro));
  const form = make(document.createElement("form"), undefined, "widget-form");
  form.addEventListener("submit", (e) => e.preventDefault());
  const seedIn = field(form, uid + "-seed", t.seedLabel, data.inputs.seed, data.inputs.seed.default);
  const actIn = field(form, uid + "-act", t.actLabel, data.inputs.act, data.inputs.act.default);
  const levelIn = field(form, uid + "-level", t.levelLabel, data.inputs.level, data.inputs.level.default);
  const roomsIn = field(form, uid + "-rooms", t.roomsLabel, data.inputs.rooms, data.inputs.rooms.default);
  const presetWrap = make(document.createElement("div"), undefined, "widget-field");
  const presetLab = make(document.createElement("label"), t.presetLabel);
  presetLab.htmlFor = uid + "-preset";
  const preset = document.createElement("select");
  preset.id = uid + "-preset";
  const none = document.createElement("option");
  none.value = "";
  none.textContent = t.presetNone;
  preset.append(none);
  for (const s of data.seeds.items) {
    const o = document.createElement("option");
    o.value = String(s);
    o.textContent = String(s);
    preset.append(o);
  }
  presetWrap.append(presetLab, preset);
  form.append(presetWrap);
  const table = make(document.createElement("table"), undefined, "widget-table");
  const live = make(document.createElement("p"), undefined, "widget-live");
  live.setAttribute("aria-live", "polite");
  const note = make(document.createElement("p"), t.note, "widget-note");
  root.append(form, table, live, note);
  element.replaceChildren(root);

  function render() {
    const out = compute({ seed: seedIn.value, act: actIn.value, level: levelIn.value, rooms: roomsIn.value }, data);
    const names = data.acts.items;
    table.replaceChildren();
    const head = document.createElement("tr");
    for (const h of t.columns.items) head.append(make(document.createElement("th"), h));
    const thead = document.createElement("thead");
    thead.append(head);
    const body = document.createElement("tbody");
    const add = (a, b, c, d) => {
      const tr = document.createElement("tr");
      tr.append(td(a), td(b), td(c), td(d));
      body.append(tr);
    };
    add("1", t.mapName, hex8(out.seed), t.mapHow);
    add("1", t.gameName, hex8(out.game.low) + ":" + hex8(out.game.high), t.gameHow);
    for (const a of out.acts) {
      const mark = a.idx === out.act ? "> " : "";
      let how = t.actHow;
      if (a.tombs) how += ". " + t.tombsHow + " " + a.tombs[0] + ", " + a.tombs[1];
      if (a.bit !== null) how += ". " + t.gateHow + " " + a.bit;
      add("3", mark + names.at(a.idx) + " " + t.actName, hex8(a.lead), how);
    }
    add("4", t.levelName + " " + out.level, hex8(out.levelSeed.sum),
      t.levelHow + ": " + hex8(out.levelSeed.lead) + " + " + out.level);
    for (const r of out.roomRows) {
      add("5", t.roomDrawName + " " + r.k, hex8(r.levelLow), t.roomDrawHow + " " + hex8(r.levelLow));
      add("5", t.roomName + " " + r.k, hex8(r.roomLow), t.roomHow);
    }
    table.append(thead, body);
    live.textContent = t.liveHead + " " + out.seed + ": " + names.at(out.act) + " " + t.liveBase + " " +
      hex8(out.levelSeed.lead) + ", " + t.liveLevel + " " + out.level + " " + hex8(out.levelSeed.sum) + ".";
  }

  for (const el of [seedIn, actIn, levelIn, roomsIn]) el.addEventListener("input", render);
  preset.addEventListener("change", () => {
    if (preset.value !== "") {
      seedIn.value = preset.value;
      render();
    }
  });
  render();
}

if (typeof document !== "undefined") {
  for (const el of document.querySelectorAll('figure[data-widget-name="' + NAME + '"]')) {
    if (!el.dataset.mounted) {
      el.dataset.mounted = "1";
      mount(el, JSON.parse(el.dataset.widgetData));
    }
  }
}
