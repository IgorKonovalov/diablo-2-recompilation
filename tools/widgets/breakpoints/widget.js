// widget-only/1
// Frames per action and breakpoints. A small tool of our own that restates the rate and the breakpoints of the
// animation timing page: an item stat gives a bonus, the bonus a factor, the factor with the animation's spd a rate,
// and the rate with the frame nfr a length in frames; each shorter length has a least factor and a least item stat.
// Every value shown is computed by our model in this page, from the numbers typed here; none is observed in the
// game, and the numbers offered are illustrative.

const NAME = "breakpoints";

function toInt(value, lo, hi, fallback) {
  const v = Math.trunc(Number(value));
  if (!Number.isFinite(v)) return fallback;
  return Math.min(hi, Math.max(lo, v));
}

function ceilDiv(a, b) {
  return Math.ceil(a / b);
}

// the bonus of an item stat: k fac s over k + s, toward zero (the stat is never negative here)
function bonusOf(k, s) {
  return s === 0 ? 0 : Math.trunc((k * s) / (k + s));
}

// the rate of a kind at a factor: the spd times the factor over 100, rounded down, never below 0, at most 0x7FFF
function rateAt(kind, spd, fac) {
  let q = Math.floor((spd * fac) / 100);
  if (kind === "block" || kind === "blockhs") q = q >= 1 ? q : 1;
  return Math.min(Math.max(q, 0), 0x7fff);
}

// the steps of the schedule: 256 x (frames - start) over the rate, rounded up (0 when the rate is 0)
function stepsOf(ticks, nf, start, rt) {
  return rt === 0 ? 0 : ceilDiv(ticks * (nf - start), rt);
}

function lengthOf(ticks, nf, start, rt) {
  if (rt === 0) return 1;
  return Math.max(2, stepsOf(ticks, nf, start, rt));
}

// The pure part: no page access. inputs: { kind, nfr: nf, start, spd, stat, term, evt }; the parsed widget.json is
// the second argument.
export function compute(inputs, data) {
  const lim = data.inputs;
  const rule = data.rule;
  const kind = lim.kind.items.indexOf(inputs.kind) >= 0 ? inputs.kind : lim.kind.default;
  const spec = rule.kinds.items.find((q) => q.id === kind);
  const nf = toInt(inputs.nfr, lim.nfr.min, lim.nfr.max, lim.nfr.default);
  const start = Math.min(toInt(inputs.start, lim.start.min, lim.start.max, lim.start.default), nf - 1);
  const spd = toInt(inputs.spd, lim.spd.min, lim.spd.max, lim.spd.default);
  const stat = toInt(inputs.stat, lim.stat.min, lim.stat.max, lim.stat.default);
  const term = toInt(inputs.term, lim.term.min, lim.term.max, lim.term.default);
  const evt = toInt(inputs.evt, lim.evt.min, lim.evt.max, lim.evt.default);
  const attack = kind === "attack";
  const t = attack ? term : 0;
  const bonus = bonusOf(rule.k, stat);
  let fac = spec.plus + bonus + t;
  if (kind === "attack") fac = Math.max(spec.lo, Math.min(spec.hi, fac));
  if (kind === "cast") fac = Math.min(fac, spec.hi);
  const rt = rateAt(kind, spd, fac);
  const n = lengthOf(rule.ticks, nf, start, rt);
  // the last step: one less than the steps, so an action of one step (the rate covers it whole) fires no event
  const N = stepsOf(rule.ticks, nf, start, rt) - 1;
  let fireAt = null;
  if (evt >= start && rt > 0) {
    const f = Math.max(1, ceilDiv(rule.ticks * (evt - start), rt));
    if (f <= N) fireAt = f;
  }
  // the lengths the factor range reaches, each with its least factor and least item stat
  const lens = new Set();
  for (let xx = spec.lo; xx <= spec.hi; xx++) {
    const rr = rateAt(kind, spd, xx);
    if (rr === 0) continue;
    lens.add(lengthOf(rule.ticks, nf, start, rr));
  }
  const ms = [...lens].filter((m) => m <= n).sort((a, b) => b - a);
  const rows = [];
  for (const m of ms) {
    const need = ceilDiv(rule.ticks * (nf - start), m);
    let xm = Math.max(spec.lo, ceilDiv(100 * need, spd));
    if (xm > spec.hi) xm = null;
    let least = null;
    if (xm !== null) {
      if (attack && xm === spec.lo) least = 0;
      else {
        const y = xm - spec.plus - t;
        if (y <= 0) least = 0;
        else if (y >= rule.k) least = null;
        else least = ceilDiv(rule.k * y, rule.k - y);
      }
    }
    rows.push({ m, fac: xm, stat: least });
  }
  const capped = rows.length > rule.maxRows;
  return {
    kind, nfr: nf, start, spd, stat, term: t, evt, bonus, fac, rt, n, fireAt,
    rows: rows.slice(0, rule.maxRows), capped,
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

function headRow(names) {
  const head = document.createElement("tr");
  for (const h of names) head.append(make(document.createElement("th"), h));
  const thead = document.createElement("thead");
  thead.append(head);
  return thead;
}

export function mount(element, data) {
  const t = data.text;
  const uid = "w-" + NAME + "-" + Math.floor(Math.random() * 1e9);
  const root = make(document.createElement("div"), undefined, "widget-body");
  root.append(make(document.createElement("p"), t.intro));
  const form = make(document.createElement("form"), undefined, "widget-form");
  form.addEventListener("submit", (e) => e.preventDefault());
  const kindSel = select(form, uid + "-kind", t.caps.kind, t.kinds.items.map((q) => [q.id, q.name]), data.inputs.kind.default);
  const lim = data.inputs;
  const ins = {
    nfr: field(form, uid + "-nfr", t.caps.nfr, lim.nfr, lim.nfr.default),
    start: field(form, uid + "-start", t.caps.start, lim.start, lim.start.default),
    spd: field(form, uid + "-spd", t.caps.spd, lim.spd, lim.spd.default),
    stat: field(form, uid + "-stat", t.caps.stat, lim.stat, lim.stat.default),
    term: field(form, uid + "-term", t.caps.term, lim.term, lim.term.default),
    evt: field(form, uid + "-evt", t.caps.evt, lim.evt, lim.evt.default),
  };
  const all = [ins.nfr, ins.start, ins.spd, ins.stat, ins.term, ins.evt];
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
  const bpTable = make(document.createElement("table"), undefined, "widget-table");
  const live = make(document.createElement("p"), undefined, "widget-live");
  live.setAttribute("aria-live", "polite");
  const note = make(document.createElement("p"), t.note, "widget-note");
  root.append(form, table, make(document.createElement("p"), t.bpHead), bpTable, live, note);
  element.replaceChildren(root);

  function render() {
    const typed = {
      kind: kindSel.value, nfr: ins.nfr.value, start: ins.start.value, spd: ins.spd.value, stat: ins.stat.value,
      term: ins.term.value, evt: ins.evt.value,
    };
    const o = compute(typed, data);
    const lines = [
      [t.steps.bonus, t.calc.bonus, String(o.bonus)],
      [t.steps.factor, t.kinds.items.find((q) => q.id === o.kind).calc, String(o.fac)],
      [t.steps.pace, t.calc.pace, String(o.rt)],
      [t.steps.length, t.calc.length, o.n + " " + t.unitFrames],
      [t.steps.evt, o.fireAt === null ? t.calc.eventNo : t.calc.eventYes,
        o.fireAt === null ? "-" : o.fireAt + " " + t.unitFrames],
    ];
    table.replaceChildren();
    const body = document.createElement("tbody");
    for (const l of lines) {
      const tr = document.createElement("tr");
      tr.append(td(l[0]), td(l[1]), td(l[2]));
      body.append(tr);
    }
    table.append(headRow(t.columns.items), body);
    bpTable.replaceChildren();
    const bpBody = document.createElement("tbody");
    for (const rt of o.rows) {
      const tr = document.createElement("tr");
      tr.append(td(String(rt.m)), td(rt.fac === null ? "-" : String(rt.fac)),
        td(rt.stat === null ? t.never : rt.stat === 0 ? t.none : String(rt.stat)));
      bpBody.append(tr);
    }
    bpTable.append(headRow(t.bpColumns.items), bpBody);
    live.textContent = t.liveHead + ": " + o.n + " " + t.unitFrames + " (" + t.liveFactor + " " + o.fac + ")." + (o.capped ? " " + t.more : "");
  }

  for (const el of all) el.addEventListener("input", render);
  kindSel.addEventListener("change", render);
  preset.addEventListener("change", () => {
    if (preset.value !== "") {
      const p = data.presets.items.at(Number(preset.value));
      ins.nfr.value = String(p.nfr);
      ins.start.value = String(p.start);
      ins.spd.value = String(p.spd);
      ins.stat.value = String(p.stat);
      ins.term.value = String(p.term);
      ins.evt.value = String(p.evt);
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
