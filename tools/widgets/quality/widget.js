// widget-only/1
// Quality chances. A small tool of our own that restates the quality roll page: d is the item level
// minus the item's quality level; the magic find factor is 0 or the plain mf + 100 for the magic test and
// a diminished one for the unique, set and rare tests; each test's c is (row value - d / divisor) x 128,
// divided by the factor, raised to the row minimum, then reduced by its ratio word; the superior and
// normal tests use the row terms alone. A test with c below 1 wins with no draw, otherwise a draw from 0
// to c - 1 wins below 128. The chance to win is shown as about 128 in c. Magic find of -100 or below goes
// straight to the superior test. All divisions truncate toward zero, in 32-bit arithmetic.
// The record rows are those of the page around the widget; the item types are invented. Every value shown
// is computed by our model, not observed in the game.

const NAME = "quality";

function toInt(value, lo, hi, fallback) {
  const v = Math.trunc(Number(value));
  if (!Number.isFinite(v)) return fallback;
  return Math.min(hi, Math.max(lo, v));
}

function tdiv(a, b) {
  return Math.trunc(a / b) + 0;
}

function diminish(m100, k) {
  if (m100 <= 110) return m100;
  const x = m100 - 100;
  return tdiv(Math.imul(x, k), x + k) + 100;
}

// The pure part: no page access. inputs: { ilvl, qlvl, mf, record, kind, w0, w1, w2, w3 } (w0 to w3: magic, rare, set, unique
// ratio words); the parsed widget.json is the second argument.
export function compute(inputs, data) {
  const lim = data.inputs;
  const rule = data.rule;
  const ilvl = toInt(inputs.ilvl, lim.ilvl.min, lim.ilvl.max, lim.ilvl.default);
  const qlvl = toInt(inputs.qlvl, lim.qlvl.min, lim.qlvl.max, lim.qlvl.default);
  const mf = toInt(inputs.mf, lim.mf.min, lim.mf.max, lim.mf.default);
  const record = toInt(inputs.record, lim.record.min, lim.record.max, lim.record.default);
  const kind = toInt(inputs.kind, lim.kind.min, lim.kind.max, lim.kind.default);
  const w = [inputs.w0, inputs.w1, inputs.w2, inputs.w3].map((v) => toInt(v, lim.word.min, lim.word.max, lim.word.default));
  const row = data.records.items.find((r) => r.rec === record);
  const d = ilvl - qlvl;
  const m100 = mf + 100;
  const toSuperior = mf !== 0 && mf <= -100;
  const useMf = mf !== 0 && !toSuperior;
  const steps = [];
  const outcomes = [];
  let reachN = 1n;
  let reachD = 1n;

  // one test: its chance c, and the outcome it adds with the reach left for the tests after it
  function run(test, rc, chance, afterMf, min, word) {
    const num = BigInt(chance < 1 ? 1 : Math.min(rule.drawWin, chance));
    const den = BigInt(chance < 1 ? 1 : chance);
    const winPpm = Number((num * 1000000n) / den);
    const ppm = Number((reachN * num * 1000000n) / (reachD * den));
    steps.push({ name: test, rc, afterMf, min, word, chance, noDraw: chance < 1, winPpm });
    outcomes.push({ name: test, rc, ppm });
    reachN *= den - num;
    reachD *= den;
    return reachN > 0n;
  }

  function scaled(term, div, min, k, word) {
    let c = (term - tdiv(d, div)) << 7;
    if (useMf) {
      const f = k === 0 ? m100 : diminish(m100, k);
      if (f !== 0) c = tdiv(Math.imul(c, 100), f);
    }
    const afterMf = c;
    if (c <= min) c = min;
    c -= tdiv(Math.imul(word, c), rule.ratioScale);
    return { chance: c, afterMf };
  }

  let more = true;
  if (kind === 3) {
    outcomes.push({ name: "normal", rc: 2, ppm: 1000000 });
    more = false;
  }
  if (more && !toSuperior) {
    const u = scaled(row.uni, row.uniDiv, rule.uniqueMin, rule.uniqueK, w.at(3));
    more = run("unique", 7, u.chance, u.afterMf, rule.uniqueMin, w.at(3));
    if (more) {
      const s = scaled(row.set, row.setDiv, rule.setMin, rule.setK, w.at(2));
      more = run("set", 5, s.chance, s.afterMf, rule.setMin, w.at(2));
    }
    if (more && kind !== 1) {
      const r = scaled(row.rare, row.rareDiv, rule.rareMin, rule.rareK, w.at(1));
      more = run("rare", 6, r.chance, r.afterMf, rule.rareMin, w.at(1));
    }
    if (more && kind === 2) {
      outcomes.push({ name: "magic", rc: 4, ppm: Number((reachN * 1000000n) / reachD) });
      more = false;
    }
    if (more) {
      const m = scaled(row.mag, row.magDiv, rule.magicMin, 0, w.at(0));
      more = run("magic", 4, m.chance, m.afterMf, rule.magicMin, w.at(0));
    }
  }
  if (more) {
    more = run("superior", 3, (row.hi - tdiv(d, row.hiDiv)) << 7, null, null, null);
  }
  if (more) {
    more = run("normal", 2, (row.nor - tdiv(d, row.norDiv)) << 7, null, null, null);
  }
  if (more) outcomes.push({ name: "low", rc: 1, ppm: Number((reachN * 1000000n) / reachD) });
  return { ilvl, qlvl, mf, record, kind, words: w, gap: d, steps, outcomes };
}

function make(el, text, cls) {
  if (text !== undefined) el.textContent = text;
  if (cls) el.className = cls;
  return el;
}

function td(text) {
  return make(document.createElement("td"), text);
}

function pct(ppm) {
  const whole = Math.floor(ppm / 10000);
  const frac = Math.floor((ppm % 10000) / 100);
  return whole + "." + String(frac).padStart(2, "0");
}

function wrapField(form, id, label, control) {
  const wrap = make(document.createElement("div"), undefined, "widget-field");
  const lab = make(document.createElement("label"), label);
  lab.htmlFor = id;
  control.id = id;
  wrap.append(lab, control);
  form.append(wrap);
  return control;
}

function numberInput(spec, value) {
  const inp = document.createElement("input");
  inp.type = "number";
  inp.min = String(spec.min);
  inp.max = String(spec.max);
  inp.step = "1";
  inp.value = String(value);
  return inp;
}

function selectOf(labels, first, value) {
  const sel = document.createElement("select");
  labels.forEach((text, i) => {
    const o = document.createElement("option");
    o.value = String(i + first);
    o.textContent = text;
    sel.append(o);
  });
  sel.value = String(value);
  return sel;
}

export function mount(element, data) {
  const t = data.text;
  const lim = data.inputs;
  const uid = "w-" + NAME + "-" + Math.floor(Math.random() * 1e9);
  const root = make(document.createElement("div"), undefined, "widget-body");
  root.append(make(document.createElement("p"), t.intro));
  const form = make(document.createElement("form"), undefined, "widget-form");
  form.addEventListener("submit", (e) => e.preventDefault());
  const ilvlIn = wrapField(form, uid + "-i", t.ilvlLabel, numberInput(lim.ilvl, lim.ilvl.default));
  const qlvlIn = wrapField(form, uid + "-q", t.qlvlLabel, numberInput(lim.qlvl, lim.qlvl.default));
  const mfIn = wrapField(form, uid + "-m", t.mfLabel, numberInput(lim.mf, lim.mf.default));
  const recIn = wrapField(form, uid + "-r", t.recordLabel,
    selectOf(data.records.items.map((r) => String(r.rec)), lim.record.min, lim.record.default));
  const kindIn = wrapField(form, uid + "-k", t.kindLabel, selectOf(t.kinds.items, 0, lim.kind.default));
  const wIn = t.ratioLabels.items.map((label, i) =>
    wrapField(form, uid + "-w" + i, label, numberInput(lim.word, lim.word.default)));
  const info = make(document.createElement("p"), undefined, "widget-note");
  const table = make(document.createElement("table"), undefined, "widget-table");
  const live = make(document.createElement("p"), undefined, "widget-live");
  live.setAttribute("aria-live", "polite");
  const note = make(document.createElement("p"), t.note, "widget-note");
  root.append(form, info, table, live, note);
  element.replaceChildren(root);

  function render() {
    const out = compute({ ilvl: ilvlIn.value, qlvl: qlvlIn.value, mf: mfIn.value, record: recIn.value,
      kind: kindIn.value, w0: wIn.at(0).value, w1: wIn.at(1).value, w2: wIn.at(2).value, w3: wIn.at(3).value }, data);
    const label = (o) => {
      if (o.name === "magic" && !out.steps.some((s) => s.name === "magic")) return t.magicType;
      return o.name === "normal" && out.kind === 3 ? t.normalType : o.name;
    };
    const ppmOf = (n) => {
      const o = out.outcomes.find((x) => x.name === n);
      return o ? o.ppm : 0;
    };
    table.replaceChildren();
    const head = document.createElement("tr");
    for (const h of t.columns.items) head.append(make(document.createElement("th"), h));
    const thead = document.createElement("thead");
    thead.append(head);
    const body = document.createElement("tbody");
    for (const s of out.steps) {
      const tr = document.createElement("tr");
      tr.append(td(s.name),
        td(s.afterMf === null ? t.none : String(s.afterMf)),
        td(s.min === null ? t.none : String(s.min)),
        td(s.noDraw ? String(s.chance) + ", " + t.noDraw : String(s.chance)),
        td(pct(s.winPpm)), td(pct(ppmOf(s.name))));
      body.append(tr);
    }
    table.append(thead, body);
    info.textContent = t.dHead + " " + out.gap + ". " + t.resultHead + ": " +
      out.outcomes.map((o) => label(o) + " " + pct(o.ppm)).join("; ") + ".";
    live.textContent = t.liveHead + " " + out.outcomes.map((o) => label(o) + " " + pct(o.ppm)).join(", ") + ".";
  }

  for (const el of [ilvlIn, qlvlIn, mfIn, recIn, kindIn].concat(wIn)) {
    el.addEventListener("input", render);
    el.addEventListener("change", render);
  }
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
