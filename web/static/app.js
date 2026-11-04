// Page logic (Step 6c). Each dataset keeps its own messages in the browser.
const SHOW_DEBUG = location.search.indexOf("debug") !== -1;   // add ?debug to the address to see intent and confidence
const state = { datasets: [], active: null, chats: {}, info: {}, loaded: {} };
const el = id => document.getElementById(id);
const EN = ["January", "February", "March", "April", "May", "June", "July",
            "August", "September", "October", "November", "December"];
const FIL = ["Enero", "Pebrero", "Marso", "Abril", "Mayo", "Hunyo", "Hulyo",
             "Agosto", "Setyembre", "Oktubre", "Nobyembre", "Disyembre"];

function make(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined) node.textContent = text;   // textContent keeps text safe
  return node;
}

function monthLabel(dateText) {
  const parts = dateText.split("-");
  return EN[Number(parts[1]) - 1].slice(0, 3) + " " + parts[0];
}

async function loadInfo(id) {
  if (!state.info[id]) {
    const res = await fetch("/api/datasets/" + id + "/info");
    if (res.ok) state.info[id] = await res.json();
  }
  return state.info[id];
}

async function loadHistory(id) {
  if (state.loaded[id]) return;                    // load the saved chat only once per page load
  try {
    const res = await fetch("/api/datasets/" + id + "/history");
    if (res.ok) {
      const data = await res.json();
      const items = [];
      data.messages.forEach(m => {
        if (!m.message || !m.message.trim()) return;
        items.push({ who: "user", text: m.message });
        const bot = { who: "bot", text: m.response, chart: m.chart || null };
        if (m.intent) bot.meta = m.intent + " | " + Math.round(m.confidence * 100) + "%";
        items.push(bot);
      });
      state.chats[id] = items;
    }
  } catch (err) { /* offline: start with an empty chat */ }
  state.loaded[id] = true;
}

async function loadDatasets(selectId) {
  const res = await fetch("/api/datasets");
  state.datasets = await res.json();
  state.datasets.forEach(d => { if (!state.chats[d.id]) state.chats[d.id] = []; });
  const wanted = selectId || state.active || (state.datasets.length ? state.datasets[0].id : null);
  if (wanted !== null) { await selectDataset(wanted); }
  else { renderSidebar(); renderHeader(); renderChat(); }
}

async function selectDataset(id) {
  state.active = id;
  await loadInfo(id);
  await loadHistory(id);
  closeSidebar();
  renderSidebar();
  renderHeader();
  renderChat();
}

function closeSidebar() {
  el("sidebar").classList.remove("open");
  el("scrim").classList.remove("show");
}

function renderSidebar() {
  const list = el("dataset-list");
  list.innerHTML = "";
  state.datasets.forEach(d => {
    const b = make("button", d.id === state.active ? "active" : "", d.name);
    b.onclick = () => selectDataset(d.id);
    list.appendChild(b);
  });
}

function renderHeader() {
  const info = state.info[state.active];
  const d = state.datasets.find(x => x.id === state.active);
  el("ds-name").textContent = d ? d.name : "No dataset yet";
  el("ds-badge").hidden = !(info && info.is_sample);
  if (info && info.records > 0) {
    el("ds-meta").textContent = info.records + " records, " +
      monthLabel(info.first_date) + " to " + monthLabel(info.last_date);
  } else {
    el("ds-meta").textContent = d ? "No records yet" : "Click + New dataset to start";
  }
}

function exampleQuestions(info) {
  const base = ["Anong buwan pinakamataas ang presyo?"];
  if (!info || !info.last_date) return base;
  // chips use the newest months in the data, so they always find records
  const y = Number(info.last_date.slice(0, 4)), m = Number(info.last_date.slice(5, 7));
  const py = m === 1 ? y - 1 : y, pm = m === 1 ? 12 : m - 1;
  base.push("Ilang kilo ang na-trade noong " + FIL[m - 1] + " " + y + "?");
  base.push("Compare prices of " + EN[pm - 1] + " " + py + " and " + EN[m - 1] + " " + y);
  return base;
}

function emptyState(d, info) {
  const box = make("div", "empty");
  box.appendChild(make("h1", "", d ? "Ask about " + d.name : "Welcome to BakaTrack"));
  box.appendChild(make("p", "", d ? "Try one of these, or type your own question in English, Filipino or Taglish."
                                  : "Upload a CSV to create your first dataset."));
  const chips = make("div", "chips");
  if (d) exampleQuestions(info).forEach(q => {
    const c = make("button", "chip", q);
    c.type = "button";
    c.onclick = () => sendMessage(q);
    chips.appendChild(c);
  });
  box.appendChild(chips);
  return box;
}

const FOOTER_STARTS = ["Period:", "Saklaw:"];

function splitFooter(text) {
  const i = text.lastIndexOf("\n\n");
  if (i === -1) return { main: text, footer: "" };
  const last = text.slice(i + 2);
  if (FOOTER_STARTS.some(s => last.startsWith(s))) {
    return { main: text.slice(0, i), footer: last };
  }
  return { main: text, footer: "" };
}

function renderChat() {
  const box = el("messages");
  box.innerHTML = "";
  const d = state.datasets.find(x => x.id === state.active);
  const list = state.chats[state.active] || [];
  if (list.length === 0) { box.appendChild(emptyState(d, state.info[state.active])); return; }
  list.forEach(m => {
    if (m.who === "user") { box.appendChild(make("div", "user-msg", m.text)); return; }
    const parts = splitFooter(m.text);
    const div = make("div", "bot-msg" + (m.pending ? " pending" : ""), parts.main);
    if (parts.footer) div.appendChild(make("div", "footer-note", parts.footer));
    if (m.chart) div.appendChild(widgetBox(m.chart));
    if (m.meta && SHOW_DEBUG) div.appendChild(make("span", "meta", m.meta));
    box.appendChild(div);
  });
  const scroller = el("chat-scroll");
  scroller.scrollTop = scroller.scrollHeight;
}


async function sendMessage(text) {
  text = text.trim();
  if (!text || state.active === null) return;
  const tab = state.active;                      // remember which dataset asked
  const pending = { who: "bot", text: "Thinking...", pending: true };
  state.chats[tab].push({ who: "user", text: text });
  state.chats[tab].push(pending);
  el("chat-input").value = "";
  el("send-btn").disabled = true;
  renderChat();
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dataset_id: tab, message: text })
    });
    const data = await res.json();
    if (res.ok) {
      pending.text = data.reply;
      pending.chart = data.chart || null;
      if (pending.chart && pending.chart.widget === "egg") {          // play it only for a fresh answer
        setTimeout(() => runEgg(pending.chart.kind), 150);
      }
      pending.meta = data.intent + " | " + Math.round(data.confidence * 100) + "% | " + data.seconds + "s";
    } else {
      pending.text = data.error || "Something went wrong.";
    }
  } catch (err) {
    pending.text = "Cannot reach the server. Is app.py running?";
  }
  pending.pending = false;
  el("send-btn").disabled = false;
  renderChat();
}

el("chat-form").onsubmit = e => { e.preventDefault(); sendMessage(el("chat-input").value); };

el("menu-btn").onclick = () => {
  el("sidebar").classList.add("open");
  el("scrim").classList.add("show");
};
el("scrim").onclick = closeSidebar;

el("clear-btn").onclick = async () => {
  if (state.active === null) return;
  if (!confirm("Clear this chat? The questions stay saved in the database.")) return;
  const id = state.active;
  await fetch("/api/datasets/" + id + "/clear", { method: "POST" });
  state.chats[id] = [];
  renderChat();
};

el("new-dataset").onclick = () => {
  el("upload-errors").innerHTML = "";
  el("upload-dialog").showModal();
};
el("upload-cancel").onclick = () => el("upload-dialog").close();

el("upload-form").onsubmit = async e => {
  e.preventDefault();
  const list = el("upload-errors");
  list.innerHTML = "";
  const form = new FormData();
  form.append("name", el("upload-name").value);
  form.append("file", el("upload-file").files[0]);
  const res = await fetch("/api/upload", { method: "POST", body: form });
  const data = await res.json();
  if (!res.ok) {
    (data.errors || ["Upload failed."]).forEach(msg => list.appendChild(make("li", "", msg)));
    return;
  }
  el("upload-dialog").close();
  el("upload-form").reset();
  await loadDatasets(data.dataset_id);
};

loadDatasets();
