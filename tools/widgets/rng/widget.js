// widget-only/1
// RNG draw stepper. A small tool of our own that restates the generator of the randomness page:
// Init(v) sets low to v and high to 666; Range(n) returns 0 with no draw when n is below 1, and
// otherwise takes one Step and returns the new low mod n. Step: low * multiplier + high in 64 bits,
// the bottom half is the new low, the top half the new high.
// Every value shown is computed by our model in this page, from the numbers typed here; none is
// observed in the game, and the seed offered is illustrative.

const NAME = "rng";

function toInt(value, lo, hi, fallback) {
  const v = Math.trunc(Number(value));
  if (!Number.isFinite(v)) return fallback;
  return Math.min(hi, Math.max(lo, v));
}

// The pure part: no page access. inputs: { seed, n, draws }; the parsed widget.json is the second argument.
export function compute(inputs, data) {
  const lim = data.inputs;
  const seed = toInt(inputs.seed, lim.seed.min, lim.seed.max, lim.seed.default);
  const n = toInt(inputs.n, lim.n.min, lim.n.max, lim.n.default);
  const draws = toInt(inputs.draws, lim.draws.min, lim.draws.max, lim.draws.default);
  const mult = BigInt("0x" + data.rule.multiplier);
  let low = seed >>> 0;
  let high = data.rule.initHigh;
  const rows = [];
  for (let k = 1; k <= draws; k++) {
    let result = 0;
    let drew = false;
    if (n >= 1) {
      const v = BigInt(low) * mult + BigInt(high);
      low = Number(BigInt.asUintN(32, v));
      high = Number(BigInt.asUintN(32, v >> 32n));
      result = low % n;
      drew = true;
    }
    rows.push({ k, drew, result, low, high });
  }
  return { seed, n, draws, start: { low: seed >>> 0, high: data.rule.initHigh }, rows };
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
  const nIn = field(form, uid + "-n", t.nLabel, data.inputs.n, data.inputs.n.default);
  const drawsIn = field(form, uid + "-draws", t.drawsLabel, data.inputs.draws, data.inputs.draws.default);
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
    const out = compute({ seed: seedIn.value, n: nIn.value, draws: drawsIn.value }, data);
    table.replaceChildren();
    const head = document.createElement("tr");
    for (const h of t.columns.items) head.append(make(document.createElement("th"), h));
    const thead = document.createElement("thead");
    thead.append(head);
    const body = document.createElement("tbody");
    const first = document.createElement("tr");
    first.append(td("0"), td(t.initName), td("-"),
      td(hex8(out.start.low)), td(hex8(out.start.high)));
    body.append(first);
    for (const r of out.rows) {
      const tr = document.createElement("tr");
      tr.append(td(String(r.k)), td(t.rangeName), td(r.drew ? String(r.result) : t.noDraw),
        td(hex8(r.low)), td(hex8(r.high)));
      body.append(tr);
    }
    table.append(thead, body);
    const last = out.rows.at(-1);
    live.textContent = t.liveHead + " " + out.seed + ", " + t.liveN + " " + out.n + ": " +
      out.rows.map((r) => (r.drew ? String(r.result) : t.noDraw)).join(", ") + ". " + t.liveLow + " " + hex8(last.low) + ".";
  }

  for (const el of [seedIn, nIn, drawsIn]) el.addEventListener("input", render);
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
