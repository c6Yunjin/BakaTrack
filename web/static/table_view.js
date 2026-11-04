// Draws a data table (sortable, paged) inside a bot answer. Used for "show the data".
function tvMake(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined) node.textContent = text;     // textContent keeps text safe
  return node;
}

function tvFormat(type, value) {
  if (value === null || value === undefined || value === "") return "-";
  if (type === "price") return "\u20B1" + Number(value).toLocaleString(undefined,
    { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  if (type === "kilos") return Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 });
  if (type === "int") return Number(value).toLocaleString();
  return String(value);
}

function tableBox(w) {
  const pageSize = w.page_size || 12;
  const state = { page: 0, sort: -1, asc: true, rows: w.rows.map((r, i) => ({ i: i, r: r })) };
  const box = tvMake("div", "table-box");
  if (w.title) box.appendChild(tvMake("div", "table-title", w.title));
  const wrap = tvMake("div", "table-wrap");
  const table = tvMake("table", "data-table");
  wrap.appendChild(table);
  box.appendChild(wrap);

  const bar = tvMake("div", "table-bar");
  const info = tvMake("span", "table-info");
  const prev = tvMake("button", "table-btn", "\u2039 Prev");
  const next = tvMake("button", "table-btn", "Next \u203A");
  prev.type = "button";
  next.type = "button";
  bar.appendChild(info);
  bar.appendChild(prev);
  bar.appendChild(next);
  if (w.export_url) {
    const link = tvMake("a", "table-btn", "Download CSV");
    link.href = w.export_url;
    link.setAttribute("download", "");
    bar.appendChild(link);
  }
  box.appendChild(bar);
  if (w.note) box.appendChild(tvMake("div", "table-note", w.note));

  function sortedRows() {
    const rows = state.rows.slice();
    if (state.sort < 0) return rows;
    const col = w.columns[state.sort];
    rows.sort((a, b) => {
      let x, y;
      if (col.type === "label") { x = a.i; y = b.i; }               // months keep their time order
      else if (col.type === "date") { x = a.r[state.sort]; y = b.r[state.sort]; }
      else { x = Number(a.r[state.sort]); y = Number(b.r[state.sort]); }
      const c = x < y ? -1 : (x > y ? 1 : 0);
      return state.asc ? c : -c;
    });
    return rows;
  }

  function draw() {
    const rows = sortedRows();
    table.innerHTML = "";
    const head = tvMake("tr");
    w.columns.forEach((col, idx) => {
      const arrow = state.sort === idx ? (state.asc ? " \u25B2" : " \u25BC") : "";
      const th = tvMake("th", col.type === "label" || col.type === "date" ? "" : "num", col.label + arrow);
      th.onclick = () => {
        if (state.sort === idx) state.asc = !state.asc; else { state.sort = idx; state.asc = true; }
        state.page = 0;
        draw();
      };
      head.appendChild(th);
    });
    table.appendChild(tvMake("thead")).appendChild(head);
    const body = tvMake("tbody");
    const start = state.page * pageSize;
    rows.slice(start, start + pageSize).forEach(item => {
      const tr = tvMake("tr");
      w.columns.forEach((col, idx) => {
        tr.appendChild(tvMake("td", col.type === "label" || col.type === "date" ? "" : "num",
                              tvFormat(col.type, item.r[idx])));
      });
      body.appendChild(tr);
    });
    table.appendChild(body);
    const shown = Math.min(start + pageSize, rows.length);
    info.textContent = rows.length ? (start + 1) + "\u2013" + shown + " of " + rows.length : "0 rows";
    const paged = rows.length > pageSize;
    prev.hidden = next.hidden = !paged;
    prev.disabled = state.page === 0;
    next.disabled = start + pageSize >= rows.length;
  }
  prev.onclick = () => { state.page -= 1; draw(); };
  next.onclick = () => { state.page += 1; draw(); };
  draw();
  return box;
}

// Chooses the right widget for one bot answer: a table or a chart.
function widgetBox(w) {
  if (w && w.widget === "egg") return eggBox(w);
  return (w && w.widget === "table") ? tableBox(w) : chartBox(w);
}
