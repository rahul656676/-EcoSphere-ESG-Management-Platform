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

function toggleSidebar() {
  const sidebar = document.getElementById("sidebar");
  if (sidebar) {
    sidebar.classList.toggle("open");
  }
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
    <div style="display:flex;align-items:center;gap:12px;">
      <button class="menu-toggle" onclick="toggleSidebar()">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
      </button>
      <span class="dots">
        <span style="background:#e0605a"></span><span style="background:#f0b429"></span><span style="background:#3cb371"></span>
      </span>
      <span class="title hide-mobile">EcoSphere: ${pageTitle}</span>
      <span class="title title-mobile" style="display:none;">${pageTitle}</span>
    </div>
    <div class="right">
      <button class="btn btn-outline hide-mobile" style="padding:4px 8px; margin-right:10px; font-size:12px;" onclick="toggleTheme()">🌓 Theme</button>
      <button class="btn btn-outline" style="padding:4px; font-size:16px;" onclick="toggleTheme()" id="theme-btn-mobile">🌓</button>
      <span id="whoami" class="hide-mobile"></span>
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

// --- Global Animations & Polish ---
const uiObserver = new MutationObserver(mutations => {
  let delay = 0;
  let addedTargets = false;
  
  mutations.forEach(m => {
    m.addedNodes.forEach(node => {
      if (node.nodeType === 1) {
        const checkAndAdd = (el) => {
          if (!el.classList.contains("stagger-item")) {
            el.classList.add("stagger-item");
            el.style.animationDelay = `${delay}s`;
            delay += 0.08;
            addedTargets = true;
          }
        };
        
        if (node.matches && node.matches(".card, .table-wrap, .feature-card, .score-card")) {
          checkAndAdd(node);
        }
        if (node.querySelectorAll) {
          node.querySelectorAll(".card, .table-wrap, .feature-card, .score-card").forEach(checkAndAdd);
        }
      }
    });
  });
  
});

uiObserver.observe(document.body, { childList: true, subtree: true });

document.addEventListener("DOMContentLoaded", () => {
  
  
  // Animate progress bars
  setTimeout(() => {
    document.querySelectorAll(".progress-bar > div").forEach(bar => {
      const target = bar.style.width;
      bar.style.width = "0%";
      setTimeout(() => bar.style.width = target, 50);
    });
  }, 100);
});

