// widget-only/1
// Physical damage, built and reduced. A small tool of our own that restates the physical roll of the damage page and
// the first row of the reductions page: the weapon's bounds in 256ths, the enhanced-damage percent with the
// strength and dexterity shares, one draw between the lowest and the highest, then the pair's percent P, the
// defender's flat reduction and the physical resistance.
// Every value shown is computed by our model in this page, from the numbers typed here; none is observed in the
// game, and the numbers offered are illustrative.

const NAME = "damage";

function toInt(value, lo, hi, fallback) {
  const v = Math.trunc(Number(value));
  if (!Number.isFinite(v)) return fallback;
  return Math.min(hi, Math.max(lo, v));
}

function tdiv(a, b) {
  return Math.trunc(a / b);
}

// the signed multiply-divide of the page (a guarded product over a divisor), in 32-bit integers
function muldiv(a, b, c) {
  a |= 0;
  b |= 0;
  c |= 0;
  if (c === 0) return 0;
  if (a > 0x100000) {
    if (c > a >> 4) return tdiv(a * b, c) | 0;
    return (tdiv(a, c) * b) | 0;
  }
  if (b > 0x10000) {
    if (c > b >> 4) return tdiv(a * b, c) | 0;
    return (tdiv(b, c) * a) | 0;
  }
  return tdiv(Math.imul(a, b), c);
}

// The pure part: no page access. The parsed widget.json is the second argument.
export function compute(inputs, data) {
  const lim = data.inputs;
  const rule = data.rule;
  const num = (x, spec) => toInt(x, spec.min, spec.max, spec.default);
  const v = {
    wmin: num(inputs.wmin, lim.wmin),
    wmax: num(inputs.wmax, lim.wmax),
    add: num(inputs.add, lim.add),
    ed: num(inputs.ed, lim.ed),
    str: num(inputs.str, lim.str),
    strBonus: num(inputs.strBonus, lim.strBonus),
    dex: num(inputs.dex, lim.dex),
    dexBonus: num(inputs.dexBonus, lim.dexBonus),
    seed: num(inputs.seed, lim.seed),
    flat: num(inputs.flat, lim.flat),
    resist: num(inputs.resist, lim.resist),
    pct: num(inputs.pct, lim.pct),
  };
  const kind = lim.kind.items.indexOf(inputs.kind) >= 0 ? inputs.kind : lim.kind.default;
  const sh = rule.shift;
  let mn = (v.wmin << sh) | 0;
  let mx = (v.wmax << sh) | 0;
  const addShifted = (v.add << sh) | 0;
  mx = (mx + addShifted) | 0;
  mn = (mn + addShifted) | 0;
  if (mn < 1) mn = 1 << sh;
  if (mx <= mn) mx = (mn + (1 << sh)) | 0;
  let ed = (v.ed + tdiv(Math.imul(v.str, v.strBonus), 100) + tdiv(Math.imul(v.dex, v.dexBonus), 100)) | 0;
  ed = Math.max(ed, rule.edFloor);
  const lo = (mn + muldiv(mn, ed, 100)) | 0;
  const hi = (mx + muldiv(mx, ed, 100)) | 0;
  let phys = lo;
  const gapLen = (hi - lo) | 0;
  const drew = hi > lo;
  let draw = 0;
  let low = v.seed >>> 0;
  let high = rule.initHigh;
  if (drew) {
    const step = BigInt(low) * BigInt("0x" + rule.multiplier) + BigInt(high);
    low = Number(BigInt.asUintN(32, step));
    high = Number(BigInt.asUintN(32, step >> 32n));
    draw = low % gapLen;
    phys = (phys + draw) | 0;
  }
  phys = Math.max(phys, 0);
  const scaled = v.pct !== rule.percentBase && phys > 0 ? muldiv(phys, v.pct, rule.percentBase) : phys;
  const flat8 = (v.flat << sh) | 0;
  // the resistance as used: below 1 it stands (never under -100); a monster's is not capped, a player's is
  let res = v.resist;
  if (res <= 0) {
    if (res <= -100) res = -100;
  } else if (kind === "player" && res >= rule.playerPhysicalCap) {
    res = rule.playerPhysicalCap;
  }
  let afterFlat = (scaled - flat8) | 0;
  let final = 0;
  if (scaled > 0) {
    let d = afterFlat;
    if (d > 0 && res !== 0) d = muldiv(d, rule.percentBase - Math.min(res, rule.immune), rule.percentBase);
    final = d;
  } else {
    afterFlat = 0;
  }
  return {
    inputs: v, kind, mn, mx, ed, lo, hi, gapLen, drew, draw, low, high, phys, scaled, flat8, afterFlat, res, final,
  };
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

function select(form, id, label, names, value) {
  const wrap = make(document.createElement("div"), undefined, "widget-field");
  const lab = make(document.createElement("label"), label);
  lab.htmlFor = id;
  const sel = document.createElement("select");
  sel.id = id;
  for (const [val, text] of names) {
    const o = document.createElement("option");
    o.value = val;
    o.textContent = text;
    sel.append(o);
  }
  sel.value = value;
  wrap.append(lab, sel);
  form.append(wrap);
  return sel;
}

// 256ths of a point, with the points beside the count
function fmt(raw, unit) {
  const neg = raw < 0;
  const a = Math.abs(raw);
  const whole = Math.floor(a / 256);
  const frac = Math.floor(((a % 256) * 100) / 256);
  return raw + " (" + (neg ? "-" : "") + whole + "." + String(frac).padStart(2, "0") + " " + unit + ")";
}

export function mount(element, data) {
  const t = data.text;
  const uid = "w-" + NAME + "-" + Math.floor(Math.random() * 1e9);
  const root = make(document.createElement("div"), undefined, "widget-body");
  root.append(make(document.createElement("p"), t.intro));
  const form = make(document.createElement("form"), undefined, "widget-form");
  form.addEventListener("submit", (e) => e.preventDefault());
  const lim = data.inputs;
  const ins = {
    wmin: field(form, uid + "-wmin", t.caps.wmin, lim.wmin, lim.wmin.default),
    wmax: field(form, uid + "-wmax", t.caps.wmax, lim.wmax, lim.wmax.default),
    add: field(form, uid + "-add", t.caps.add, lim.add, lim.add.default),
    ed: field(form, uid + "-ed", t.caps.ed, lim.ed, lim.ed.default),
    str: field(form, uid + "-str", t.caps.str, lim.str, lim.str.default),
    strBonus: field(form, uid + "-strBonus", t.caps.strBonus, lim.strBonus, lim.strBonus.default),
    dex: field(form, uid + "-dex", t.caps.dex, lim.dex, lim.dex.default),
    dexBonus: field(form, uid + "-dexBonus", t.caps.dexBonus, lim.dexBonus, lim.dexBonus.default),
    seed: field(form, uid + "-seed", t.caps.seed, lim.seed, lim.seed.default),
    flat: field(form, uid + "-flat", t.caps.flat, lim.flat, lim.flat.default),
    resist: field(form, uid + "-resist", t.caps.resist, lim.resist, lim.resist.default),
    pct: field(form, uid + "-pct", t.caps.pct, lim.pct, lim.pct.default),
  };
  const all = [ins.wmin, ins.wmax, ins.add, ins.ed, ins.str, ins.strBonus, ins.dex, ins.dexBonus, ins.seed, ins.flat, ins.resist, ins.pct];
  const kindSel = select(form, uid + "-kind", t.caps.kind, t.kinds.items.map((x) => [x.id, x.name]), lim.kind.default);
  const presetWrap = make(document.createElement("div"), undefined, "widget-field");
  const presetLab = make(document.createElement("label"), t.presetLabel);
  presetLab.htmlFor = uid + "-preset";
  const preset = document.createElement("select");
  preset.id = uid + "-preset";
  const none = document.createElement("option");
  none.value = "";
  none.textContent = t.presetNone;
  preset.append(none);
  data.presets.items.forEach((p, i) => {
    const o = document.createElement("option");
    o.value = String(i);
    o.textContent = p.name;
    preset.append(o);
  });
  presetWrap.append(presetLab, preset);
  form.append(presetWrap);
  const table = make(document.createElement("table"), undefined, "widget-table");
  const live = make(document.createElement("p"), undefined, "widget-live");
  live.setAttribute("aria-live", "polite");
  const note = make(document.createElement("p"), t.note, "widget-note");
  root.append(form, table, live, note);
  element.replaceChildren(root);

  function render() {
    const typed = {
      kind: kindSel.value, wmin: ins.wmin.value, wmax: ins.wmax.value, add: ins.add.value, ed: ins.ed.value,
      str: ins.str.value, strBonus: ins.strBonus.value, dex: ins.dex.value, dexBonus: ins.dexBonus.value,
      seed: ins.seed.value, flat: ins.flat.value, resist: ins.resist.value, pct: ins.pct.value,
    };
    const o = compute(typed, data);
    const u = t.unitPts;
    const lines = [
      [t.steps.first, t.calc.first, o.mn + " and " + o.mx],
      [t.steps.ed, t.calc.ed, o.ed + "%"],
      [t.steps.bounds, t.calc.bounds, o.lo + " and " + o.hi],
      [t.steps.draw, o.drew ? t.calc.drawYes : t.calc.drawNo, o.drew ? o.draw + " of " + o.gapLen : "-"],
      [t.steps.roll, t.calc.roll, fmt(o.phys, u)],
      [t.steps.pscaled, o.inputs.pct === data.rule.percentBase ? t.calc.scaleSame : t.calc.scaleDo, fmt(o.scaled, u)],
      [t.steps.flat, t.calc.flat, fmt(o.afterFlat, u)],
      [t.steps.resist, o.kind === "player" ? t.calc.resistPlayer : t.calc.resistMonster, o.res + "%"],
      [t.steps.final, t.calc.final, fmt(o.final, u)],
    ];
    table.replaceChildren();
    const head = document.createElement("tr");
    for (const h of t.columns.items) head.append(make(document.createElement("th"), h));
    const thead = document.createElement("thead");
    thead.append(head);
    const body = document.createElement("tbody");
    for (const l of lines) {
      const tr = document.createElement("tr");
      tr.append(td(l[0]), td(l[1]), td(l[2]));
      body.append(tr);
    }
    table.append(thead, body);
    live.textContent = t.liveHead + ": " + fmt(o.phys, u) + " " + t.liveRaw + ", " + fmt(o.final, u) + " " + t.liveFinal + ".";
  }

  for (const el of all) el.addEventListener("input", render);
  kindSel.addEventListener("change", render);
  preset.addEventListener("change", () => {
    if (preset.value !== "") {
      const p = data.presets.items.at(Number(preset.value));
      ins.wmin.value = String(p.wmin);
      ins.wmax.value = String(p.wmax);
      ins.add.value = String(p.add);
      ins.ed.value = String(p.ed);
      ins.str.value = String(p.str);
      ins.strBonus.value = String(p.strBonus);
      ins.dex.value = String(p.dex);
      ins.dexBonus.value = String(p.dexBonus);
      ins.flat.value = String(p.flat);
      ins.resist.value = String(p.resist);
      ins.pct.value = String(p.pct);
      kindSel.value = p.kind;
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
