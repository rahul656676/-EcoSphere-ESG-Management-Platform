/* EcoSphere - shared frontend helpers */

const NAV = [
  { section: "Dashboard", href: "dashboard.html", icon: "layout-dashboard" },
  { section: "AI Copilot", href: "ai.html", icon: "sparkles" },
  { section: "Environmental", href: "environmental.html", icon: "leaf", items: [
      "Emission Factors", "Product ESG Profiles", "Carbon Transactions", "Environmental Goals"] },
  { section: "Social", href: "social.html", icon: "users", items: [
      "CSR Activities", "Employee Participation", "Diversity Dashboard"] },
  { section: "Governance", href: "governance.html", icon: "shield-check", items: [
      "Policies", "Policy Acknowledgements", "Audits", "Compliance Issues"] },
  { section: "Gamification", href: "gamification.html", icon: "award", items: [
      "Challenges", "Challenge Participation", "Badges", "Rewards", "Leaderboard"] },
  { section: "Reports", href: "reports.html", icon: "file-pie-chart", items: [
      "Environmental Report", "Social Report", "Governance Report", "ESG Summary", "Custom Report Builder"] },
  { section: "Settings", href: "settings.html", icon: "settings", items: [
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

function toggleSidebar() {
  const sidebar = document.getElementById("sidebar");
  if (sidebar) {
    sidebar.classList.toggle("open");
  }
}

function renderShell(activePage, pageTitle) {
  const sidebarHtml = NAV.map(sec => {
    const active = sec.href === activePage;
    let html = `<div class="sidebar-nav-item ${active ? 'active' : ''}" onclick="window.location.href='${sec.href}'">
      <i data-lucide="${sec.icon}" class="icon"></i>
      <span>${sec.section}</span>
    </div>`;
    if (sec.items && active) {
      html += `<div class="sidebar-sub">` + sec.items.map(i => `<a href="${sec.href}">${i}</a>`).join("") + `</div>`;
    }
    return html;
  }).join("");

  document.getElementById("sidebar").innerHTML = `
    <div class="brand">
      <i data-lucide="leaf" class="logo-icon"></i>
      EcoSphere
    </div>
    <div class="sidebar-nav">
      ${sidebarHtml}
    </div>
  `;

  document.getElementById("topbar").innerHTML = `
    <div class="topbar-left">
      <div class="breadcrumb">
        <i data-lucide="home" class="icon"></i>
        <span>/</span>
        <span>${pageTitle}</span>
      </div>
      <div class="global-search">
        <i data-lucide="search" class="icon"></i>
        <input type="text" placeholder="Search departments, metrics, or reports...">
      </div>
    </div>
    <div class="topbar-right">
      <button class="topbar-btn" onclick="toggleTheme()" title="Toggle Theme">
        <i data-lucide="moon" class="icon"></i>
      </button>
      <button class="topbar-btn" title="Notifications">
        <i data-lucide="bell" class="icon"></i>
      </button>
      <div class="profile-menu" onclick="logout()" title="Click to Logout">
        <div class="profile-avatar">A</div>
        <div class="profile-name" id="whoami">Admin</div>
      </div>
    </div>
  `;

  // Apply saved theme
  if (localStorage.getItem("ecoTheme") === "light") {
    document.documentElement.setAttribute("data-theme", "light");
  }

  api("/auth/me").then(me => {
    if (me && me.authenticated) {
      document.getElementById("whoami").textContent = `${me.username}`;
      const firstLetter = me.username.charAt(0).toUpperCase();
      document.querySelector('.profile-avatar').textContent = firstLetter;
    }
  }).catch(() => {});

  if (!document.getElementById("ai-assistant-toggle")) {
    const aiHTML = `
      <div id="ai-assistant-toggle" class="ai-assistant-toggle" onclick="toggleAIChat()">
        <i data-lucide="sparkles" class="icon"></i>
      </div>
      <div id="ai-assistant-window" class="ai-assistant-window">
        <div class="ai-assistant-header">
          <div class="ai-title">
            <i data-lucide="bot" class="icon"></i>
            AI ESG Copilot
          </div>
          <button class="topbar-btn" style="width:30px;height:30px;" onclick="toggleAIChat()">
            <i data-lucide="x" class="icon"></i>
          </button>
        </div>
        <div class="ai-assistant-body" id="ai-chat-body">
          <div class="ai-msg system">Hi there! I'm your AI ESG Copilot. How can I assist you with your sustainability goals today?</div>
        </div>
        <div class="ai-assistant-footer">
          <input type="text" id="ai-chat-input" placeholder="Ask AI Copilot..." onkeypress="if(event.key==='Enter') sendAIChat()">
          <button onclick="sendAIChat()">
            <i data-lucide="send" class="icon" style="width:18px;height:18px;"></i>
          </button>
        </div>
      </div>
    `;
    document.body.insertAdjacentHTML('beforeend', aiHTML);
  }

  // Initialize Lucide icons
  if (window.lucide) {
    lucide.createIcons();
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

  const typingId = "typing-" + Date.now();
  body.innerHTML += `<div id="${typingId}" class="ai-msg system muted">AI Copilot is thinking...</div>`;
  body.scrollTop = body.scrollHeight;

  api("/ai/chat", { method: "POST", body: { message: text } })
    .then(res => {
      document.getElementById(typingId).remove();
      if (res && res.reply) {
        body.innerHTML += `<div class="ai-msg system">${esc(res.reply)}</div>`;
      } else {
        body.innerHTML += `<div class="ai-msg system">Sorry, I couldn't process that.</div>`;
      }
      body.scrollTop = body.scrollHeight;
    })
    .catch(e => {
      document.getElementById(typingId).remove();
      body.innerHTML += `<div class="ai-msg system" style="color:var(--red);">Error connecting to AI: ${esc(e.message)}</div>`;
      body.scrollTop = body.scrollHeight;
    });
}

// Global animation helper for counter
function animateValue(obj, start, end, duration) {
  let startTimestamp = null;
  const step = (timestamp) => {
    if (!startTimestamp) startTimestamp = timestamp;
    const progress = Math.min((timestamp - startTimestamp) / duration, 1);
    obj.innerHTML = Math.floor(progress * (end - start) + start);
    if (progress < 1) {
      window.requestAnimationFrame(step);
    } else {
      obj.innerHTML = end; // Ensure final value is exact
    }
  };
  window.requestAnimationFrame(step);
}
