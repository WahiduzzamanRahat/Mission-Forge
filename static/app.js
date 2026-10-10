const state = {
  destination: "mars",
  objective: "science",
  rocket: "medium",
  instruments: [],
  result: null,
};

const screens = ["home", "builder", "simulation", "report"];
const $ = (id) => document.getElementById(id);

function showScreen(id) {
  screens.forEach(s => document.getElementById(s).classList.toggle("active", s === id));
  window.scrollTo({top: 0, behavior: "smooth"});
}

$("startBtn").onclick = () => showScreen("builder");
document.querySelectorAll("[data-home]").forEach(b => b.onclick = () => showScreen("home"));
$("backBuilder").onclick = () => showScreen("builder");
$("newMission").onclick = () => {
  state.instruments = [];
  document.querySelectorAll(".instrument input").forEach(x => x.checked = false);
  state.destination = "mars"; state.objective = "science"; state.rocket = "medium";
  document.querySelectorAll("[data-destination]").forEach(x => x.classList.toggle("selected", x.dataset.destination === "mars"));
  document.querySelectorAll("[data-rocket]").forEach(x => x.classList.toggle("selected", x.dataset.rocket === "medium"));
  $("objective").value = "science";
  refresh();
  showScreen("builder");
};

document.querySelectorAll("[data-destination]").forEach(btn => {
  btn.onclick = () => {
    state.destination = btn.dataset.destination;
    document.querySelectorAll("[data-destination]").forEach(x => x.classList.remove("selected"));
    btn.classList.add("selected");
    refresh();
  };
});

document.querySelectorAll("[data-rocket]").forEach(btn => {
  btn.onclick = () => {
    state.rocket = btn.dataset.rocket;
    document.querySelectorAll("[data-rocket]").forEach(x => x.classList.remove("selected"));
    btn.classList.add("selected");
    refresh();
  };
});

$("objective").onchange = (e) => { state.objective = e.target.value; refresh(); };

const instrumentMeta = {
  camera: ["Camera", "1.0 t • $45M • 5 power", "13 science"],
  spectrometer: ["Spectrometer", "2.0 t • $105M • 11 power", "25 science"],
  radiation: ["Radiation Detector", "1.5 t • $85M • 8 power", "18 science"],
  soil: ["Soil Analyzer", "2.0 t • $110M • 12 power", "24 science"],
  weather: ["Weather Station", "1.2 t • $70M • 9 power", "16 science"],
};

function buildInstruments() {
  const box = $("instrumentChoices");
  box.innerHTML = "";
  Object.entries(instrumentMeta).forEach(([id, data]) => {
    const label = document.createElement("label");
    label.className = "instrument";
    label.innerHTML = `<input type="checkbox" value="${id}"><span class="instrument-info"><b>${data[0]}</b><span>${data[1]} • ${data[2]}</span></span>`;
    label.querySelector("input").onchange = (e) => {
      if (e.target.checked) state.instruments.push(id);
      else state.instruments = state.instruments.filter(x => x !== id);
      refresh();
    };
    box.appendChild(label);
  });
}

async function calculate(payload = currentPayload()) {
  const r = await fetch("/api/simulate", {
    method: "POST", headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload)
  });
  return r.json();
}

function currentPayload() {
  return {destination: state.destination, objective: state.objective, rocket: state.rocket, instruments: [...state.instruments]};
}

function setBar(id, value, max=100) {
  $(id).style.width = `${Math.max(0, Math.min(100, value / max * 100))}%`;
}

function refresh() {
  calculate().then(result => {
    state.result = result;
    $("missionLabel").textContent = `${result.destination.toUpperCase()} ${result.rocket.toUpperCase()} MISSION`;
    $("massValue").textContent = `${result.mass} / ${result.limits.mass} t`;
    $("budgetValue").textContent = `$${result.budget}M / $${result.limits.budget}M`;
    $("powerValue").textContent = `${result.power} / 100`;
    $("commValue").textContent = `${result.communication} / 100`;
    $("scienceValue").textContent = `${result.science} / 100`;
    $("riskValue").textContent = `${result.risk} / 100`;
    setBar("massBar", result.mass, result.limits.mass);
    setBar("budgetBar", result.budget, result.limits.budget);
    setBar("powerBar", result.power);
    setBar("commBar", result.communication);
    setBar("scienceBar", result.science);
    setBar("riskBar", result.risk);
    const box = $("constraintBox");
    if (result.failures.length) {
      box.className = "constraint bad";
      box.innerHTML = "⚠ " + result.failures.join("<br>⚠ ");
    } else {
      box.className = "constraint ok";
      box.textContent = "✓ Configuration is currently feasible.";
    }
  });
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

$("simulateBtn").onclick = async () => {
  const result = state.result || await calculate();
  state.result = result;
  showScreen("simulation");
  await runSimulation(result);
  renderReport(result);
  showScreen("report");
  loadAdvisor();
  loadNASA();
};

async function runSimulation(result) {
  const items = [...document.querySelectorAll(".timeline-item")];
  items.forEach((x,i) => { x.className = "timeline-item" + (i === 0 ? " active" : ""); x.querySelector("em").textContent = "Standby"; });
  $("consoleLog").innerHTML = "";
  const stages = ["Launch", "Earth Orbit", "Departure", "Deep Space", "Communication", "Arrival", "Landing", "Science Operations"];
  const messages = [
    "Launch vehicle ignition confirmed.",
    "Stable Earth orbit achieved.",
    "Departure burn complete.",
    "Cruise trajectory established.",
    "Deep-space communications link checked.",
    `${result.destination} approach initiated.`,
    "Final approach and landing sequence.",
    "Scientific payload activated."
  ];
  for (let i=0; i<stages.length; i++) {
    for (let t=10; t>=1; t--) {
      if (i === 0) $("countdown").textContent = `T − ${t}`;
      else $("countdown").textContent = `PHASE ${String(i+1).padStart(2,"0")}`;
      $("simPercent").textContent = `${Math.round((i / stages.length) * 100)}%`;
      await sleep(i === 0 ? 120 : 80);
    }
    items.forEach((x,j) => {
      x.className = "timeline-item" + (j < i ? " done" : j === i ? " active" : "");
      if (j < i) x.querySelector("em").textContent = "Complete";
    });
    items[i].querySelector("em").textContent = "Complete";
    $("simStatus").textContent = messages[i];
    $("consoleLog").innerHTML += `<div>[OK] ${messages[i]}</div>`;
    $("consoleLog").scrollTop = $("consoleLog").scrollHeight;
    await sleep(300);
  }
  $("simPercent").textContent = "100%";
  $("countdown").textContent = result.success ? "MISSION COMPLETE" : "MISSION REVIEW";
  $("simStatus").textContent = result.success ? "All modeled mission phases completed." : "Mission completed with critical constraints.";
  document.querySelectorAll(".timeline-item").forEach(x => x.className = "timeline-item done");
  $("simMetrics").innerHTML = metricRows(result);
}

function metricRows(r) {
  return [
    ["MISSION SCORE", `${r.score}/100`],
    ["MASS", `${r.mass} / ${r.limits.mass} t`],
    ["POWER", `${r.power}`],
    ["COMMUNICATION", `${r.communication}`],
    ["SCIENCE", `${r.science}`],
    ["RISK", `${r.risk}`],
  ].map(x => `<div class="sim-metric"><span>${x[0]}</span><b>${x[1]}</b></div>`).join("");
}

function renderReport(r) {
  $("finalScore").textContent = r.score;
  $("outcomeTitle").textContent = r.success ? "MISSION COMPLETE" : "MISSION FAILED";
  $("outcomeCopy").textContent = r.success
    ? `The modeled ${r.destination} mission completed all critical phases. Explore the What-If Lab to see how another engineering decision changes the outcome.`
    : `The modeled mission encountered constraints that prevented a robust mission outcome. Use the What-If Lab to redesign it.`;
  $("reportMetrics").innerHTML = [
    ["Scientific Value", r.science], ["Reliability", r.reliability],
    ["Communication", r.communication], ["Power", r.power],
    ["Risk", r.risk], ["Budget", `$${r.budget}M`],
    ["Mass", `${r.mass} t`], ["Vehicle", r.rocket]
  ].map(x => `<div class="report-metric"><span>${x[0]}</span><strong>${x[1]}</strong></div>`).join("");
  $("modelNote").textContent = r.model_note;
}

async function loadAdvisor() {
  const box = $("advisorContent");
  box.innerHTML = `<div class="spinner"></div><p>Analyzing your mission…</p>`;
  try {
    const response = await fetch("/api/advisor", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify(currentPayload())
    });
    const data = await response.json();
    if (data.text) {
      box.textContent = data.text;
      return;
    }
    box.innerHTML = `<p>${data.summary || ""}</p>
      <p><strong>Strongest:</strong> ${data.strongest || "—"}</p>
      <p><strong>Risk:</strong> ${data.risk || "—"}</p>
      <p><strong>Recommendations:</strong><br>• ${(data.recommendations || []).join("<br>• ")}</p>
      <small>${data.source || ""}</small>`;
  } catch (e) {
    box.textContent = "Advisor unavailable. The numerical simulation is still valid.";
  }
}

$("whatIfBtn").onclick = async () => {
  const action = $("whatIfAction").value;
  const p = currentPayload();
  const [type, value] = action.split(":");
  if (type === "remove") p.instruments = p.instruments.filter(x => x !== value);
  if (type === "add" && !p.instruments.includes(value)) p.instruments.push(value);
  if (type === "rocket") p.rocket = value;
  const next = await calculate(p);
  const base = state.result || await calculate();
  const fields = [
    ["Score", base.score, next.score],
    ["Science", base.science, next.science],
    ["Mass", base.mass, next.mass],
    ["Power", base.power, next.power],
    ["Risk", base.risk, next.risk],
  ];
  $("whatIfResult").classList.remove("hidden");
  $("whatIfResult").innerHTML = `<b>What changed?</b><div class="delta-grid">${
    fields.map(([name,a,b]) => {
      const diff = +(b-a).toFixed(1);
      const cls = diff === 0 ? "" : ((name === "Risk" || name === "Mass") ? (diff < 0 ? "positive" : "negative") : (diff > 0 ? "positive" : "negative"));
      return `<div class="delta"><span>${name}</span><b>${a} → ${b}</b><small class="${cls}">${diff > 0 ? "+" : ""}${diff}</small></div>`;
    }).join("")
  }</div><p class="muted">This is a simplified educational trade-off model, not a NASA flight calculation.</p>`;
};

async function loadNASA() {
  $("nasaTitle").textContent = "Loading NASA data…";
  try {
    const r = await fetch("/api/nasa/apod");
    const data = await r.json();
    if (!data.ok) throw new Error(data.message);
    $("nasaTitle").textContent = data.title;
    $("nasaDate").textContent = data.date;
    $("nasaExplanation").textContent = data.explanation;
    $("nasaCredit").textContent = data.copyright ? `Credit: ${data.copyright}` : "Source: NASA Astronomy Picture of the Day";
    if (data.media_type === "image") $("nasaImage").src = data.hdurl || data.url;
  } catch (e) {
    $("nasaTitle").textContent = "NASA data temporarily unavailable";
    $("nasaExplanation").textContent = "The mission simulator remains fully usable. Add a NASA API key in .env for higher API limits.";
    $("nasaCredit").textContent = "NASA Open APIs";
  }
}

buildInstruments();
refresh();
