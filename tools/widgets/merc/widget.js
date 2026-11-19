// widget-only/1
// Mercenary stats at a level. A small tool of our own that restates the stats-per-level section of the
// hirelings page: the band row is the last row whose first level is at or below L (the first row for a
// lower L); d is L minus that row's level; strength, dexterity and the damage pair add their column
// times d divided by 8, resistances divide by 4, both truncating toward zero; life is (HP + HP/Lvl x d)
// x 256; the other stats add the column times d; each has its own floor. ExpForLevel is
// (L + 1) x L x L x e in 32-bit arithmetic. Skills are left out.
// Every band row here is invented for this widget. Every value shown is computed by our model, not
// observed in the game.

const NAME = "merc";

function toInt(value, lo, hi, fallback) {
  const v = Math.trunc(Number(value));
  if (!Number.isFinite(v)) return fallback;
  return Math.min(hi, Math.max(lo, v));
}

function tdiv(a, b) {
  return Math.trunc(a / b) + 0;
}

function i32(v) {
  return Number(BigInt.asIntN(32, BigInt(v)));
}

function expFor(lvl, e) {
  return i32(i32(i32((lvl + 1) * e) * lvl) * lvl);
}

// The pure part: no page access. inputs: { level }; the parsed widget.json is the second argument.
export function compute(inputs, data) {
  const lim = data.inputs.level;
  const lvl = toInt(inputs.level, lim.min, lim.max, lim.default);
  const bands = data.bands.items;
  let band = 0;
  bands.forEach((b, i) => {
    if (b.lv <= lvl) band = i;
  });
  const r = bands.at(band);
  const dlt = lvl - r.lv;
  const hp = Math.max(10240, i32(i32(i32(r.hpl * 256) * dlt) + i32(r.hp * 256)));
  const resist = Math.max(0, r.rs + tdiv(i32(r.rsl * dlt), 4));
  const result = [
    lvl,
    lvl < data.rule.maxLevel - 1 ? expFor(lvl + 1, r.expl) : 0,
    expFor(lvl, r.expl),
    Math.max(10, r.st + tdiv(i32(r.stl * dlt), 8)),
    Math.max(10, r.dexb + tdiv(i32(r.dxl * dlt), 8)),
    hp,
    Math.max(0, i32(r.dfl * dlt + r.df)),
    Math.max(0, i32(r.arl * dlt + r.ar)),
    Math.max(0, r.dmin + tdiv(i32(r.dml * dlt), 8)),
    Math.max(1, r.dmax + tdiv(i32(r.dml * dlt), 8)),
    resist,
    Math.max(0, tdiv(hp, 2000)),
  ];
  return { level: lvl, band, dlt, result };
}

function make(el, text, cls) {
  if (text !== undefined) el.textContent = text;
  if (cls) el.className = cls;
  return el;
}

function td(text) {
  return make(document.createElement("td"), text);
}

export function mount(element, data) {
  const t = data.text;
  const uid = "w-" + NAME + "-" + Math.floor(Math.random() * 1e9);
  const root = make(document.createElement("div"), undefined, "widget-body");
  root.append(make(document.createElement("p"), t.intro));
  const form = make(document.createElement("form"), undefined, "widget-form");
  form.addEventListener("submit", (e) => e.preventDefault());
  const wrap = make(document.createElement("div"), undefined, "widget-field");
  const lab = make(document.createElement("label"), t.levelLabel);
  lab.htmlFor = uid + "-l";
  const lvIn = document.createElement("input");
  lvIn.type = "number";
  lvIn.id = uid + "-l";
  lvIn.min = String(data.inputs.level.min);
  lvIn.max = String(data.inputs.level.max);
  lvIn.step = "1";
  lvIn.value = String(data.inputs.level.default);
  wrap.append(lab, lvIn);
  form.append(wrap);
  const info = make(document.createElement("p"), undefined, "widget-note");
  const table = make(document.createElement("table"), undefined, "widget-table");
  const live = make(document.createElement("p"), undefined, "widget-live");
  live.setAttribute("aria-live", "polite");
  const note = make(document.createElement("p"), t.note, "widget-note");
  root.append(form, info, table, live, note);
  element.replaceChildren(root);

  function render() {
    const out = compute({ level: lvIn.value }, data);
    table.replaceChildren();
    const head = document.createElement("tr");
    for (const h of t.columns.items) head.append(make(document.createElement("th"), h));
    const thead = document.createElement("thead");
    thead.append(head);
    const body = document.createElement("tbody");
    t.names.items.forEach((label, i) => {
      const tr = document.createElement("tr");
      tr.append(td(label), td(t.how.items.at(i)), td(String(out.result.at(i))));
      body.append(tr);
    });
    table.append(thead, body);
    info.textContent = t.bandHead + ": " + data.bands.items.at(out.band).lv + ". " + t.dHead + " = " + out.dlt + ".";
    live.textContent = t.liveHead + " " + out.level + ", " + t.liveBand + " " + out.band + ", " + t.liveD + " " +
      out.dlt + ": " + out.result.join(", ") + ".";
  }

  lvIn.addEventListener("input", render);
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
