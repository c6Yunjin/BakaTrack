// Draws one chart (Chart.js, saved locally in web/static) inside a bot answer.
function chartBox(chart) {
  const box = document.createElement("div");
  box.className = "chart-box";
  if (typeof Chart === "undefined") {
    box.textContent = "Chart library not loaded (web/static/chart.umd.js is missing).";
    return box;
  }
  const canvas = document.createElement("canvas");
  box.appendChild(canvas);
  const isPrice = chart.metric === "price_per_kilo";
  const fmt = v => isPrice ? "\u20B1" + Number(v).toLocaleString(undefined, { maximumFractionDigits: 2 })
                           : Number(v).toLocaleString();
  new Chart(canvas, {
    type: chart.type,
    data: {
      labels: chart.labels,
      datasets: [{
        label: chart.label,
        data: chart.values,
        borderColor: "#5D4037",
        backgroundColor: chart.type === "bar" ? "#8D6E63" : "#5D4037",
        borderWidth: 2,
        tension: 0.25,
        spanGaps: false          // a month with no records stays a visible gap
      }]
    },
    options: {
      animation: false,
      responsive: true,
      maintainAspectRatio: false,
      plugins: { tooltip: { callbacks: { label: ctx => ctx.dataset.label + ": " + fmt(ctx.parsed.y) } } },
      scales: {
        x: { ticks: { color: "#3E2723" }, grid: { color: "#EFEBE9" } },
        y: { ticks: { color: "#3E2723", callback: v => fmt(v) }, grid: { color: "#D7CCC8" },
             beginAtZero: chart.type === "bar" }
      }
    }
  });
  return box;
}
