// Easter eggs on the page: a closeable full-screen video and a cow animation.
function eggBox(w) {
  const box = document.createElement("div");
  box.className = "egg-box";
  const button = document.createElement("button");
  button.type = "button";
  button.className = "table-btn";
  button.textContent = w.kind === "rickroll" ? "\u25B6 Play again" : "\uD83D\uDC04 Play again";
  button.onclick = () => runEgg(w.kind);
  box.appendChild(button);
  return box;
}

function runEgg(kind) {
  if (kind === "rickroll") openVideoOverlay("/static/rickroll.mp4");
  else if (kind === "cows") runCows();
}

function openVideoOverlay(src) {
  if (document.getElementById("egg-overlay")) return;
  const overlay = document.createElement("div");
  overlay.id = "egg-overlay";
  const video = document.createElement("video");
  video.src = src;
  video.controls = true;
  video.autoplay = true;
  video.playsInline = true;
  const missing = document.createElement("div");
  missing.className = "egg-missing";
  missing.hidden = true;
  missing.textContent = "Video not found. Save your file as web/static/rickroll.mp4 and try again.";
  const close = document.createElement("button");
  close.type = "button";
  close.className = "egg-close";
  close.textContent = "\u2715 Close";

  function onKey(e) { if (e.key === "Escape") closeOverlay(); }
  function closeOverlay() {
    video.pause();
    overlay.remove();
    document.removeEventListener("keydown", onKey);
  }
  close.onclick = closeOverlay;
  video.addEventListener("error", () => { video.hidden = true; missing.hidden = false; });
  document.addEventListener("keydown", onKey);

  overlay.appendChild(video);
  overlay.appendChild(missing);
  overlay.appendChild(close);
  document.body.appendChild(overlay);
  const started = video.play();
  if (started && started.catch) {            // if the browser blocks sound, start muted (controls can unmute)
    started.catch(() => { video.muted = true; video.play().catch(() => {}); });
  }
}

function runCows() {
  const layer = document.createElement("div");
  layer.className = "cow-layer";
  for (let i = 0; i < 14; i++) {
    const cow = document.createElement("span");
    cow.className = "cow-run";
    cow.textContent = "\uD83D\uDC04";
    cow.style.top = (5 + Math.random() * 80) + "vh";
    cow.style.animationDelay = (Math.random() * 2.5) + "s";
    cow.style.fontSize = (28 + Math.random() * 36) + "px";
    layer.appendChild(cow);
  }
  document.body.appendChild(layer);
  setTimeout(() => layer.remove(), 7500);
}
