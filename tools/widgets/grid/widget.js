// widget-only/1
// Placement search. A small tool of our own that restates the placement search of the inventory page: for a player's
// page an item one cell high takes the free spot scored best, the columns from the right and each from the bottom,
// and a taller item takes the best by rows from the top, each from the left; for any other owner the first spot that
// fits wins (one cell high: columns from the right, each from the top; otherwise columns from the left). The score
// counts the filled neighbouring cells, an edge of the page counting as filled; a tie keeps the earlier spot.
// The shapes are typed here as toy shapes; every value shown is computed by our model, not observed in the game.

const NAME = "grid";

function toInt(value, lo, hi, fallback) {
  const v = Math.trunc(Number(value));
  if (!Number.isFinite(v)) return fallback;
  return Math.min(hi, Math.max(lo, v));
}

// Sizes: tokens apart by spaces or commas, each a digit 1 to 4, an x or X, a digit 1 to 4.
// Returns { shapes, fault } with fault 0 none, 1 a bad token, 2 too many items.
function parseShapes(text, maxItems) {
  const tokens = [];
  let cur = "";
  for (const ch of text) {
    if (ch === " " || ch === ",") {
      if (cur !== "") tokens.push(cur);
      cur = "";
    } else {
      cur += ch;
    }
  }
  if (cur !== "") tokens.push(cur);
  const shapes = [];
  for (const t of tokens) {
    const ok = t.length === 3 && "1234".includes(t[0]) && (t[1] === "x" || t[1] === "X") && "1234".includes(t[2]);
    if (!ok) return { shapes: [], fault: 1 };
    shapes.push({ wd: Number(t[0]), ht: Number(t[2]) });
  }
  if (shapes.length > maxItems) return { shapes: [], fault: 2 };
  return { shapes, fault: 0 };
}

function filled(cells, gw, col, row) {
  return cells.at(row * gw + col) !== 0;
}

function fits(cells, gw, gh, col, row, w, h) {
  if (col + w > gw || row + h > gh) return false;
  for (let r = row; r < row + h; r++) {
    for (let c = col; c < col + w; c++) {
      if (filled(cells, gw, c, r)) return false;
    }
  }
  return true;
}

// the filled cells along the four sides, a side outside the page counting its whole length; the perfect score when all are
function score(cells, gw, gh, col, row, w, h, perfect) {
  let n = 0;
  if (col < 1) {
    n += h;
  } else {
    for (let r = row; r < row + h; r++) if (filled(cells, gw, col - 1, r)) n++;
  }
  if (col + w < gw) {
    for (let r = row; r < row + h; r++) if (filled(cells, gw, col + w, r)) n++;
  } else {
    n += h;
  }
  if (row < 1) {
    n += w;
  } else {
    for (let c = col; c < col + w; c++) if (filled(cells, gw, c, row - 1)) n++;
  }
  if (row + h < gh) {
    for (let c = col; c < col + w; c++) if (filled(cells, gw, c, row + h)) n++;
  } else {
    n += w;
  }
  return 2 * (w + h) <= n ? perfect : n;
}

// the m-th spot of the search order: a player's page takes the score; a one-cell-high item goes by columns from the right
function spotAt(m, gw, gh, order) {
  const byColumn = Math.trunc(m / gh);
  if (order === "bestOne") return { col: gw - 1 - byColumn, row: gh - 1 - (m % gh) };
  if (order === "bestTall") return { col: m % gw, row: Math.trunc(m / gw) };
  if (order === "firstOne") return { col: gw - 1 - byColumn, row: m % gh };
  return { col: byColumn, row: m % gh };
}

function search(cells, gw, gh, w, h, player, perfect) {
  const one = h === 1;
  const order = player ? (one ? "bestOne" : "bestTall") : one ? "firstOne" : "firstTall";
  let best = 0;
  let at = { col: -1, row: -1 };
  for (let m = 0; m < gw * gh; m++) {
    const s = spotAt(m, gw, gh, order);
    if (!fits(cells, gw, gh, s.col, s.row, w, h)) continue;
    if (!player) return { col: s.col, row: s.row, score: -1 };
    const sc = score(cells, gw, gh, s.col, s.row, w, h, perfect);
    if (sc > best) {
      best = sc;
      at = { col: s.col, row: s.row };
      if (sc === perfect) break;
    }
  }
  return { col: at.col, row: at.row, score: at.col < 0 ? -1 : best };
}

// The pure part: no page access. inputs: { gw, gh, owner, shapes }; the parsed widget.json is the second argument.
export function compute(inputs, data) {
  const lim = data.inputs;
  const gw = toInt(inputs.gw, lim.gw.min, lim.gw.max, lim.gw.default);
  const gh = toInt(inputs.gh, lim.gh.min, lim.gh.max, lim.gh.default);
  const owner = toInt(inputs.owner, lim.owner.min, lim.owner.max, lim.owner.default);
  const parsed = parseShapes(String(inputs.shapes), data.rule.maxItems);
  const cells = new Array(gw * gh).fill(0);
  const letters = new Array(gw * gh).fill(".");
  const rows = [];
  parsed.shapes.forEach((sz, k) => {
    const hit = search(cells, gw, gh, sz.wd, sz.ht, owner === 0, data.rule.perfect);
    const placed = hit.col >= 0;
    rows.push({ num: k + 1, wd: sz.wd, ht: sz.ht, placed, col: hit.col, row: hit.col < 0 ? -1 : hit.row, score: hit.score });
    if (placed) {
      for (let r = hit.row; r < hit.row + sz.ht; r++) {
        for (let c = hit.col; c < hit.col + sz.wd; c++) {
          cells.fill(1, r * gw + c, r * gw + c + 1);
          letters.fill("ABCDEFGHIJKL".at(k), r * gw + c, r * gw + c + 1);
        }
      }
    }
  });
  const grid = [];
  for (let r = 0; r < gh; r++) grid.push(letters.slice(r * gw, r * gw + gw).join(""));
  return { fault: parsed.fault, gw, gh, owner, rows, grid };
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
    gw: field(form, uid + "-gw", t.caps.gw, lim.gw, lim.gw.default),
    gh: field(form, uid + "-gh", t.caps.gh, lim.gh, lim.gh.default),
    owner: field(form, uid + "-owner", t.caps.owner, lim.owner, lim.owner.default),
  };
  const shapesWrap = make(document.createElement("div"), undefined, "widget-field");
  const shapesLab = make(document.createElement("label"), t.caps.shapes);
  shapesLab.htmlFor = uid + "-shapes";
  const shapesIn = document.createElement("input");
  shapesIn.type = "text";
  shapesIn.id = uid + "-shapes";
  shapesIn.value = lim.shapes.default;
  shapesWrap.append(shapesLab, shapesIn);
  form.append(shapesWrap);
  const all = [ins.gw, ins.gh, ins.owner, shapesIn];
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
  const gridHead = make(document.createElement("p"), t.gridHead, "widget-note");
  const pic = make(document.createElement("pre"), undefined, "widget-grid");
  const live = make(document.createElement("p"), undefined, "widget-live");
  live.setAttribute("aria-live", "polite");
  const note = make(document.createElement("p"), t.note, "widget-note");
  root.append(form, table, gridHead, pic, live, note);
  element.replaceChildren(root);

  function render() {
    const o = compute({ gw: ins.gw.value, gh: ins.gh.value, owner: ins.owner.value, shapes: shapesIn.value }, data);
    table.replaceChildren();
    const head = document.createElement("tr");
    for (const h of t.columns.items) head.append(make(document.createElement("th"), h));
    const thead = document.createElement("thead");
    thead.append(head);
    const body = document.createElement("tbody");
    for (const r of o.rows) {
      const tr = document.createElement("tr");
      const spot = r.placed ? r.col + ", " + r.row : t.none;
      const sc = r.score >= 0 ? String(r.score) : r.placed ? t.noScore : "-";
      tr.append(td(String(r.num)), td(r.wd + " x " + r.ht), td(spot), td(sc));
      body.append(tr);
    }
    table.append(thead, body);
    pic.textContent = o.fault === 0 ? o.grid.join("\n") : "";
    if (o.fault === 1) {
      live.textContent = t.errBad + " " + shapesIn.value;
    } else if (o.fault === 2) {
      live.textContent = t.errLong;
    } else {
      const got = o.rows.filter((r) => r.placed).length;
      live.textContent = t.liveHead + " " + got + " " + t.liveOf + " " + o.rows.length + " " + t.liveItems;
    }
  }

  for (const el of all) el.addEventListener("input", render);
  preset.addEventListener("change", () => {
    if (preset.value !== "") {
      const p = data.presets.items.at(Number(preset.value));
      ins.gw.value = String(p.gw);
      ins.gh.value = String(p.gh);
      ins.owner.value = String(p.owner);
      shapesIn.value = p.shapes;
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
