const $ = (id) => document.getElementById(id);

function money(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency", currency: "INR", maximumFractionDigits: 0
  }).format(value);
}

function scrollToId(id) {
  document.getElementById(id)?.scrollIntoView({behavior:"smooth"});
}
window.scrollToId = scrollToId;

async function postJSON(url, payload) {
  const res = await fetch(url, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
}

$("eligibilityForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const box = $("eligibilityResult");
  box.innerHTML = "<h3>Analyzing…</h3><p class='muted'>Checking the demo model.</p>";
  try {
    const data = await postJSON("/api/eligibility", {
      income: $("income").value,
      age: $("age").value,
      credit_score: $("creditScore").value,
      employment: $("employment").value,
      save_record: $("saveRecord").checked
    });
    const cls = data.eligible ? "success" : "warning";
    box.innerHTML = `
      <div class="result-icon">✓</div>
      <div class="score ${cls}">${data.eligible ? "Eligible" : "Review"}</div>
      <p><b>Demo score:</b> ${data.score}/100 • <b>Band:</b> ${data.band}</p>
      <p>Estimated loan amount: <b>${money(data.estimated_loan_amount)}</b><br>
      Estimated max EMI: <b>${money(data.estimated_max_emi)}</b></p>
      <ul>${data.reasons.map(r => `<li>${r}</li>`).join("")}</ul>
      <small class="muted">${data.disclaimer}</small>
      ${data.sheets ? `<small class="muted">${data.sheets.message}</small>` : ""}
    `;
  } catch (err) {
    box.innerHTML = `<h3 class="danger">Error</h3><p>${err.message}</p>`;
  }
});

$("creditForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const box = $("creditResult");
  try {
    const data = await postJSON("/api/credit-score", {credit_score: $("creditInput").value});
    const cls = data.score >= 700 ? "success" : data.score >= 650 ? "warning" : "danger";
    box.innerHTML = `
      <div class="score ${cls}">${data.score}</div>
      <h3>${data.rating}</h3>
      <p>Risk band: <b>${data.risk}</b></p>
      <ul>${data.factors.map(x => `<li>${x}</li>`).join("")}</ul>
      <small class="muted">${data.disclaimer}</small>
    `;
  } catch (err) {
    box.innerHTML = `<h3 class="danger">Error</h3><p>${err.message}</p>`;
  }
});

$("emiForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const box = $("emiResult");
  try {
    const data = await postJSON("/api/emi", {
      principal: $("principal").value,
      rate: $("rate").value,
      months: $("months").value
    });
    box.innerHTML = `
      <div class="score success">${money(data.emi)}</div>
      <h3>Monthly EMI</h3>
      <p>Total payment: <b>${money(data.total_payment)}</b><br>
      Total interest: <b>${money(data.total_interest)}</b></p>
      <small class="muted">${data.months} months at ${data.annual_rate}% annual interest.</small>
    `;
  } catch (err) {
    box.innerHTML = `<h3 class="danger">Error</h3><p>${err.message}</p>`;
  }
});

$("askAi").addEventListener("click", async () => {
  const prompt = $("aiPrompt").value.trim();
  const box = $("aiAnswer");
  if (!prompt) return;
  box.textContent = "Thinking…";
  try {
    const data = await postJSON("/api/ai", {prompt});
    box.textContent = data.answer;
  } catch (err) {
    box.textContent = err.message;
  }
});

async function loadTips() {
  const data = await fetch("/api/tips").then(r => r.json());
  $("tipsList").innerHTML = data.tips.map((tip, i) =>
    `<div class="tip"><b>0${i+1}</b><p>${tip}</p></div>`
  ).join("");
}
loadTips();
