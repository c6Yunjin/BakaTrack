// Page logic: tabs, chat, upload. Each tab keeps its own messages.
const state = { datasets: [], active: null, chats: {} };
const el = id => document.getElementById(id);

async function loadDatasets(selectId) {
  const res = await fetch("/api/datasets");
  state.datasets = await res.json();
  state.datasets.forEach(d => { if (!state.chats[d.id]) state.chats[d.id] = []; });
  if (selectId) state.active = selectId;
  if (state.active === null && state.datasets.length) state.active = state.datasets[0].id;
  showGreeting();
  renderTabs();
  renderMessages();
}

function showGreeting() {
  const d = state.datasets.find(x => x.id === state.active);
  if (d && state.chats[d.id].length === 0) {
    state.chats[d.id].push({ who: "bot",
      text: "You are in the tab \"" + d.name + "\". Ask me about kilos, head count or prices. Type \"help\" to see examples." });
  }
}

function renderTabs() {
  const nav = el("tabs");
  nav.innerHTML = "";
  state.datasets.forEach(d => {
    const b = document.createElement("button");
    b.textContent = d.name;
    if (d.id === state.active) b.className = "active";
    b.onclick = () => { state.active = d.id; showGreeting(); renderTabs(); renderMessages(); };
    nav.appendChild(b);
  });
  const plus = document.createElement("button");
  plus.textContent = "+";
  plus.title = "Upload a CSV and make a new tab";
  plus.onclick = () => { el("upload-panel").hidden = false; };
  nav.appendChild(plus);
}

function renderMessages() {
  const box = el("messages");
  box.innerHTML = "";
  (state.chats[state.active] || []).forEach(m => {
    const div = document.createElement("div");
    div.className = "msg " + m.who;
    div.textContent = m.text;              // textContent keeps user text safe
    if (m.meta) {
      const small = document.createElement("span");
      small.className = "meta";
      small.textContent = m.meta;
      div.appendChild(small);
    }
    box.appendChild(div);
  });
  box.scrollTop = box.scrollHeight;
}

el("chat-form").onsubmit = async e => {
  e.preventDefault();
  const input = el("chat-input");
  const text = input.value.trim();
  if (!text || state.active === null) return;
  const tab = state.active;                 // remember which tab asked
  state.chats[tab].push({ who: "user", text: text });
  input.value = "";
  renderMessages();
  el("send-btn").disabled = true;
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dataset_id: tab, message: text })
    });
    const data = await res.json();
    if (res.ok) {
      state.chats[tab].push({ who: "bot", text: data.reply,
        meta: data.intent + " | " + Math.round(data.confidence * 100) + "% | " + data.seconds + "s" });
    } else {
      state.chats[tab].push({ who: "bot", text: data.error || "Something went wrong." });
    }
  } catch (err) {
    state.chats[tab].push({ who: "bot", text: "Cannot reach the server. Is app.py running?" });
  }
  el("send-btn").disabled = false;
  renderMessages();
};

el("upload-cancel").onclick = () => { el("upload-panel").hidden = true; };

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
    (data.errors || ["Upload failed."]).forEach(msg => {
      const li = document.createElement("li");
      li.textContent = msg;
      list.appendChild(li);
    });
    return;
  }
  el("upload-panel").hidden = true;
  el("upload-form").reset();
  await loadDatasets(data.dataset_id);
};

loadDatasets();
