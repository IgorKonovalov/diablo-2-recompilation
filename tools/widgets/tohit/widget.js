// widget-only/1
// Chance-to-hit calculator. A small tool of our own that restates the chance to hit of the to-hit page: the attack
// rating takes its percent, a negative side is swapped into the other, the chance is 100 x AR / (AR + DEF) truncated,
// then scaled by twice the attacker's level over the two levels' sum, and clamped to 5 to 95.
// Every value shown is computed by our model in this page, from the numbers typed here; none is observed in the
// game, and the numbers offered are illustrative.

const NAME = "tohit";

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

// The pure part: no page access. inputs: { ar, pct, def, alvl, dlvl }; the parsed widget.json is the second argument.
export function compute(inputs, data) {
  const lim = data.inputs;
  const rule = data.rule;
  const ar0 = toInt(inputs.ar, lim.ar.min, lim.ar.max, lim.ar.default);
  const pct = toInt(inputs.pct, lim.pct.min, lim.pct.max, lim.pct.default);
  const def0 = toInt(inputs.def, lim.def.min, lim.def.max, lim.def.default);
  const alvl = toInt(inputs.alvl, lim.alvl.min, lim.alvl.max, lim.alvl.default);
  const dlvl = toInt(inputs.dlvl, lim.dlvl.min, lim.dlvl.max, lim.dlvl.default);
  let ar = (ar0 + muldiv(ar0, pct, rule.percentBase)) | 0;
  const ar3 = ar;
  let df = def0;
  let swap = "none";
  if (df < 0) {
    ar = (ar - df) | 0;
    df = 0;
    swap = "def";
  }
  if (ar < 0) {
    df = (df - ar) | 0;
    ar = 0;
    swap = swap === "def" ? "both" : "ar";
  }
  if (df < 0) df = 0;
  const c1 = ar + df === 0 ? rule.percentBase : tdiv(Math.imul(rule.percentBase, ar), (ar + df) | 0);
  const c2 = tdiv(Math.imul(Math.imul(c1, alvl), rule.levelFactor), (alvl + dlvl) | 0);
  let c = c2;
  let clamp = "none";
  if (c2 <= rule.clampLow) {
    c = rule.clampLow;
    clamp = "low";
  } else if (c2 >= rule.clampHigh) {
    c = rule.clampHigh;
    clamp = "high";
  }
  return { ar: ar0, pct, def: def0, alvl, dlvl, ar3, swap, arAfter: ar, defAfter: df, c1, c2, chance: c, clamp };
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
  const lim = data.inputs;
  const ins = {
    ar: field(form, uid + "-ar", t.caps.ar, lim.ar, lim.ar.default),
    pct: field(form, uid + "-pct", t.caps.pct, lim.pct, lim.pct.default),
    def: field(form, uid + "-def", t.caps.def, lim.def, lim.def.default),
    alvl: field(form, uid + "-alvl", t.caps.alvl, lim.alvl, lim.alvl.default),
    dlvl: field(form, uid + "-dlvl", t.caps.dlvl, lim.dlvl, lim.dlvl.default),
  };
  const all = [ins.ar, ins.pct, ins.def, ins.alvl, ins.dlvl];
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
    const o = compute({ ar: ins.ar.value, pct: ins.pct.value, def: ins.def.value, alvl: ins.alvl.value, dlvl: ins.dlvl.value }, data);
    const swapText = o.swap === "def" ? t.calc.swapDef : o.swap === "ar" ? t.calc.swapAr : o.swap === "both" ? t.calc.swapBoth : t.calc.swapNone;
    const clampText = o.clamp === "low" ? t.calc.clampLow : o.clamp === "high" ? t.calc.clampHigh : t.calc.clampNone;
    const lines = [
      [t.steps.pct, t.calc.pct, o.ar + " -> " + o.ar3],
      [t.steps.swap, swapText, o.arAfter + " and " + o.defAfter],
      [t.steps.first, t.calc.first, o.c1 + "%"],
      [t.steps.level, t.calc.level, o.c2 + "%"],
      [t.steps.clamp, clampText, o.chance + "%"],
      [t.steps.roll, t.calc.roll, String(o.chance)],
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
    live.textContent = t.liveHead + ": " + o.chance + "% (" + t.liveAr + " " + o.ar + ", " + t.liveDef + " " + o.def + ").";
  }

  for (const el of all) el.addEventListener("input", render);
  preset.addEventListener("change", () => {
    if (preset.value !== "") {
      const p = data.presets.items.at(Number(preset.value));
      ins.ar.value = String(p.ar);
      ins.pct.value = String(p.pct);
      ins.def.value = String(p.def);
      ins.alvl.value = String(p.alvl);
      ins.dlvl.value = String(p.dlvl);
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
