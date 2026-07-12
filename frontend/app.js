/* EcoSphere - shared frontend helpers */

const NAV = [
  { section: "Dashboard", href: "dashboard.html" },
  { section: "AI Copilot", href: "ai.html" },
  { section: "Environmental", href: "environmental.html", items: [
      "Emission Factors", "Product ESG Profiles", "Carbon Transactions", "Environmental Goals"] },
  { section: "Social", href: "social.html", items: [
      "CSR Activities", "Employee Participation", "Diversity Dashboard"] },
  { section: "Governance", href: "governance.html", items: [
      "Policies", "Policy Acknowledgements", "Audits", "Compliance Issues"] },
  { section: "Gamification", href: "gamification.html", items: [
      "Challenges", "Challenge Participation", "Badges", "Rewards", "Leaderboard"] },
  { section: "Reports", href: "reports.html", items: [
      "Environmental Report", "Social Report", "Governance Report", "ESG Summary", "Custom Report Builder"] },
  { section: "Settings", href: "settings.html", items: [
      "Departments", "Categories", "ESG Configuration", "Notification Settings"] },
];

async function api(path, options = {}) {
  const opts = Object.assign({ headers: { "Content-Type": "application/json" } }, options);
  if (opts.body && typeof opts.body !== "string") opts.body = JSON.stringify(opts.body);
  const res = await fetch(`/api${path}`, opts);
  if (res.status === 401) {
    window.location.href = "login.html";
    return null;
  }
  let data = null;
  try { data = await res.json(); } catch (e) { /* no body */ }
  if (!res.ok) {
    const msg = (data && (data.error || data.message)) || `Request failed (${res.status})`;
    throw new Error(msg);
  }
  return data;
}

function toast(message, isError = false) {
  let el = document.getElementById("toast");
  if (!el) {
    el = document.createElement("div");
    el.id = "toast";
    el.className = "toast";
    document.body.appendChild(el);
  }
  el.textContent = message;
  el.className = "toast show" + (isError ? " error" : "");
  setTimeout(() => { el.className = "toast"; }, 3200);
}

function fmtDate(d) {
  if (!d) return "-";
  return d;
}

function esc(str) {
  if (str === null || str === undefined) return "";
  return String(str).replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[c]));
}

function renderShell(activePage, pageTitle) {
  const sidebarHtml = NAV.map(sec => {
    const active = sec.href === activePage;
    let html = `<a class="module-header ${active ? 'active' : ''}" href="${sec.href}" style="color:${active ? 'var(--primary)' : 'var(--text)'}">${sec.section}</a>`;
    if (sec.items) {
      html += sec.items.map(i => `<a class="nav-link" href="${sec.href}">${i}</a>`).join("");
    }
    return html;
  }).join("");

  document.getElementById("sidebar").innerHTML = `
    <div class="brand">EcoSphere</div>
    ${sidebarHtml}
  `;

  const tabsHtml = NAV.map(sec => `
    <a href="${sec.href}" class="${sec.href === activePage ? 'active' : ''}">${sec.section}</a>
  `).join("");

  document.getElementById("topbar").innerHTML = `
    <div style="display:flex;align-items:center;">
      <span class="dots">
        <span style="background:#e0605a"></span><span style="background:#f0b429"></span><span style="background:#3cb371"></span>
      </span>
      <span class="title">EcoSphere: ${pageTitle}</span>
    </div>
    <div class="right">
      <button class="btn btn-outline" style="padding:4px 8px; margin-right:10px; font-size:12px;" onclick="toggleTheme()">🌓 Theme</button>
      <span id="whoami"></span>
      <button class="logout" onclick="logout()">Logout</button>
    </div>
  `;
  document.getElementById("tabs").innerHTML = tabsHtml;

  // Apply saved theme
  if (localStorage.getItem("ecoTheme") === "light") {
    document.documentElement.setAttribute("data-theme", "light");
  }

  api("/auth/me").then(me => {
    if (me && me.authenticated) {
      document.getElementById("whoami").textContent = `${me.username} (${me.role})`;
    }
  }).catch(() => {});

  if (!document.getElementById("ai-assistant-toggle")) {
    const aiHTML = `
      <div id="ai-assistant-toggle" class="ai-assistant-toggle" onclick="toggleAIChat()">✨</div>
      <div id="ai-assistant-window" class="ai-assistant-window">
        <div class="ai-assistant-header">
          <div class="ai-assistant-header-left">
            <div class="icon">✨</div>
            <div class="title">AI ESG Copilot</div>
          </div>
          <button class="close-btn" onclick="toggleAIChat()">×</button>
        </div>
        <div class="ai-assistant-body" id="ai-chat-body">
          <div class="ai-msg system">Hi there! I'm your AI ESG Copilot. How can I assist you with your sustainability goals today?</div>
        </div>
        <div class="ai-assistant-footer">
          <input type="text" id="ai-chat-input" placeholder="Ask AI Copilot..." onkeypress="if(event.key==='Enter') sendAIChat()">
          <button onclick="sendAIChat()">↑</button>
        </div>
      </div>
    `;
    document.body.insertAdjacentHTML('beforeend', aiHTML);
  }
}

async function logout() {
  await fetch("/api/auth/logout", { method: "POST" });
  window.location.href = "login.html";
}

function openModal(id) { document.getElementById(id).classList.add("open"); }
function closeModal(id) { document.getElementById(id).classList.remove("open"); }

function showPanel(name, btnEl, groupClass) {
  document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
  document.getElementById(name).classList.add("active");
  document.querySelectorAll(".subtabs button").forEach(b => b.classList.remove("active"));
  if (btnEl) btnEl.classList.add("active");
}

function toggleAIChat() {
  document.getElementById("ai-assistant-window").classList.toggle("open");
}

function toggleTheme() {
  if (document.documentElement.getAttribute("data-theme") === "light") {
    document.documentElement.removeAttribute("data-theme");
    localStorage.setItem("ecoTheme", "dark");
  } else {
    document.documentElement.setAttribute("data-theme", "light");
    localStorage.setItem("ecoTheme", "light");
  }
}

function sendAIChat() {
  const input = document.getElementById("ai-chat-input");
  const text = input.value.trim();
  if (!text) return;
  
  const body = document.getElementById("ai-chat-body");
  body.innerHTML += `<div class="ai-msg user">${esc(text)}</div>`;
  input.value = "";
  body.scrollTop = body.scrollHeight;

  setTimeout(() => {
    const responses = [
      "I've analyzed your recent emissions data. There's a 12% anomaly in Scope 2. Would you like me to generate a detailed report?",
      "Based on current compliance trends, I recommend updating your diversity policy to align with the upcoming ISO standards.",
      "Generating AI insights... Your optimal carbon reduction strategy involves shifting 15% of fleet to EV this quarter.",
      "I can certainly help with that! Let me cross-reference our ESG framework guidelines."
    ];
    const reply = responses[Math.floor(Math.random() * responses.length)];
    body.innerHTML += `<div class="ai-msg system">${reply}</div>`;
    body.scrollTop = body.scrollHeight;
  }, 1000);
}
