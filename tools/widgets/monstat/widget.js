// widget-only/1
// Monster stat scaler. A small tool of our own that restates the first part of the monster stats page:
// a level selects one row of the level table (the last row for a higher level, no row below 0); the
// difficulty is 0 below 1 and at most 2; a scaled monster gets MulDiv(row value, cell, 100) for minimum
// and maximum hit points, defence and experience, a raw-cell monster gets its cell unchanged. MulDiv
// here is the 32-bit branch: a 32-bit product, then a division truncating toward zero.
// Every table here is invented for this widget. Every value shown is computed by our model, not
// observed in the game.

const NAME = "monstat";

function toInt(value, lo, hi, fallback) {
  const v = Math.trunc(Number(value));
  if (!Number.isFinite(v)) return fallback;
  return Math.min(hi, Math.max(lo, v));
}

function mulDiv(a, b, c) {
  if (c === 0) return 0;
  return Math.trunc(Math.imul(a, b) / c) + 0;
}

function by(d, a, b, c) {
  return d === 0 ? a : d === 1 ? b : c;
}

// The pure part: no page access. inputs: { monster, level, difficulty }; the parsed widget.json is the second argument.
export function compute(inputs, data) {
  const lim = data.inputs;
  const monster = toInt(inputs.monster, lim.monster.min, lim.monster.max, lim.monster.default);
  const level = toInt(inputs.level, lim.level.min, lim.level.max, lim.level.default);
  const asked = toInt(inputs.difficulty, lim.difficulty.min, lim.difficulty.max, lim.difficulty.default);
  const d = asked < 1 ? 0 : Math.min(asked, 2);
  const mon = data.monsters.items.at(monster);
  const scaled = mon.plain === 0;
  const row = level < 0 ? -1 : Math.min(level, data.levels.items.length - 1);
  if (row < 0) {
    return { monster, level, diff: d, row, scaled, rowVals: [0, 0, 0, 0], cell: [0, 0, 0, 0], result: [0, 0, 0, 0] };
  }
  const r = data.levels.items.at(row);
  const hp = by(d, r.hp0, r.hp1, r.hp2);
  const rowVals = [hp, hp, by(d, r.ac0, r.ac1, r.ac2), by(d, r.xp0, r.xp1, r.xp2)];
  const cell = [by(d, mon.mnhp0, mon.mnhp1, mon.mnhp2), by(d, mon.mxhp0, mon.mxhp1, mon.mxhp2),
    by(d, mon.ac0, mon.ac1, mon.ac2), by(d, mon.ex0, mon.ex1, mon.ex2)];
  const result = cell.map((c, i) => (scaled ? mulDiv(rowVals.at(i), c, 100) : c));
  return { monster, level, diff: d, row, scaled, rowVals, cell, result };
}

function make(el, text, cls) {
  if (text !== undefined) el.textContent = text;
  if (cls) el.className = cls;
  return el;
}

function td(text) {
  return make(document.createElement("td"), text);
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

function selectOf(labels, value) {
  const sel = document.createElement("select");
  labels.forEach((text, i) => {
    const o = document.createElement("option");
    o.value = String(i);
    o.textContent = text;
    sel.append(o);
  });
  sel.value = String(value);
  return sel;
}

export function mount(element, data) {
  const t = data.text;
  const uid = "w-" + NAME + "-" + Math.floor(Math.random() * 1e9);
  const root = make(document.createElement("div"), undefined, "widget-body");
  root.append(make(document.createElement("p"), t.intro));
  const form = make(document.createElement("form"), undefined, "widget-form");
  form.addEventListener("submit", (e) => e.preventDefault());
  const monIn = wrapField(form, uid + "-m", t.monsterLabel,
    selectOf(data.monsters.items.map((m) => m.name), data.inputs.monster.default));
  const lvIn = wrapField(form, uid + "-l", t.levelLabel, numberInput(data.inputs.level, data.inputs.level.default));
  const diffIn = wrapField(form, uid + "-d", t.diffLabel, selectOf(t.diffs.items, 0));
  const table = make(document.createElement("table"), undefined, "widget-table");
  const live = make(document.createElement("p"), undefined, "widget-live");
  live.setAttribute("aria-live", "polite");
  const note = make(document.createElement("p"), t.note, "widget-note");
  root.append(form, table, live, note);
  element.replaceChildren(root);

  function render() {
    const out = compute({ monster: monIn.value, level: lvIn.value, difficulty: diffIn.value }, data);
    table.replaceChildren();
    const head = document.createElement("tr");
    for (const h of t.columns.items) head.append(make(document.createElement("th"), h));
    const thead = document.createElement("thead");
    thead.append(head);
    const body = document.createElement("tbody");
    t.statNames.items.forEach((label, i) => {
      const tr = document.createElement("tr");
      if (out.row < 0) {
        tr.append(td(label), td("-"), td("-"), td(t.noRow));
      } else {
        const how = out.scaled ? t.scaled : t.plain;
        tr.append(td(label), td(String(out.rowVals.at(i))), td(String(out.cell.at(i))),
          td(String(out.result.at(i)) + " = " + how));
      }
      body.append(tr);
    });
    table.append(thead, body);
    live.textContent = t.liveHead + " " + out.level + ", " + t.liveRow + " " + out.row + ", " + t.liveOut + " " +
      out.result.join(", ") + ".";
  }

  for (const el of [monIn, lvIn, diffIn]) {
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
