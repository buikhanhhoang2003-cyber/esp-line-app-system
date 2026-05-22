// ─── State ─────────────────────────────────────────────────
const state = {
  token: "",
  connected: false,
  mode: "push",
  history: [],
};

// ─── API base (same origin) ────────────────────────────────
const API = "";

// ─── Init: load default token from .env ────────────────────
document.addEventListener("DOMContentLoaded", () => {
  fetch(`${API}/api/default-token`)
    .then((r) => r.json())
    .then((data) => {
      if (data.token) {
        document.getElementById("tokenInput").value = data.token;
        state.token = data.token;
      }
    })
    .catch(() => {});

  // Bind input listeners for send button state
  document.getElementById("msgInput").addEventListener("input", updateSendBtn);
  document.getElementById("userIdInput").addEventListener("input", updateSendBtn);
});

// ─── Token Toggle ──────────────────────────────────────────
function toggleToken() {
  const inp = document.getElementById("tokenInput");
  const btn = inp.parentElement.querySelector(".token-toggle");
  if (inp.type === "password") {
    inp.type = "text";
    btn.textContent = "HIDE";
  } else {
    inp.type = "password";
    btn.textContent = "SHOW";
  }
}

// ─── Connect ───────────────────────────────────────────────
async function connect() {
  state.token = document.getElementById("tokenInput").value.trim();
  if (!state.token) return;

  const btn = document.getElementById("connectBtn");
  btn.textContent = "CONNECTING...";
  btn.disabled = true;

  try {
    const r = await fetch(`${API}/api/connect`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token: state.token }),
    });
    const data = await r.json();

    if (r.ok && data.bot) {
      state.connected = true;
      updateStatus(true);
      showBotInfo(data.bot, data.quota);
      btn.textContent = "✓ RECONNECT";
      updateSendBtn();
    } else {
      state.connected = false;
      updateStatus(false);
      alert("Invalid token: " + (data.detail || data.error || "Unknown error"));
      btn.textContent = "⚡ CONNECT";
    }
  } catch (e) {
    alert("Connection error: " + e.message);
    btn.textContent = "⚡ CONNECT";
  }
  btn.disabled = false;
}

// ─── Status Badge ──────────────────────────────────────────
function updateStatus(online) {
  const badge = document.getElementById("statusBadge");
  const text = document.getElementById("statusText");
  badge.className = "status-badge " + (online ? "online" : "offline");
  text.textContent = online ? "ONLINE" : "OFFLINE";
}

// ─── Bot Info ──────────────────────────────────────────────
function showBotInfo(bot, quota) {
  const box = document.getElementById("botInfoBox");
  const avatarHtml = bot.pictureUrl
    ? `<img src="${bot.pictureUrl}" class="bot-avatar">`
    : `<div class="bot-avatar-placeholder">🤖</div>`;

  box.innerHTML = `
    <div class="bot-info">
      <div class="bot-row">
        ${avatarHtml}
        <div>
          <div class="bot-name">${escapeHtml(bot.displayName || "Bot")}</div>
          <div class="bot-id">${(bot.userId || "").slice(0, 16)}...</div>
        </div>
      </div>
      ${
        quota
          ? `
      <div class="bot-quota">
        <span>Messages sent this month</span>
        <span class="bot-quota-val">${(quota.totalUsage || 0).toLocaleString()}</span>
      </div>`
          : ""
      }
    </div>
  `;
  box.style.display = "block";
}

// ─── Mode Toggle ───────────────────────────────────────────
function setMode(mode) {
  state.mode = mode;
  document.getElementById("modePush").className = "mode-btn" + (mode === "push" ? " active" : "");
  document.getElementById("modeBcast").className = "mode-btn" + (mode === "broadcast" ? " active" : "");
  document.getElementById("userIdField").style.display = mode === "push" ? "block" : "none";
  document.getElementById("bcastWarn").style.display = mode === "broadcast" ? "block" : "none";
  updateSendBtn();
}

// ─── Send Button State ─────────────────────────────────────
function updateSendBtn() {
  const btn = document.getElementById("sendBtn");
  const msg = document.getElementById("msgInput").value.trim();
  const uid = document.getElementById("userIdInput").value.trim();
  const canSend = state.connected && msg && (state.mode === "broadcast" || uid);
  btn.disabled = !canSend;
  btn.innerHTML = state.mode === "push" ? "✉ SEND PUSH" : "📡 SEND BROADCAST";
}

// ─── Image Preview ─────────────────────────────────────────
function previewImage() {
  const url = document.getElementById("imageInput").value.trim();
  const box = document.getElementById("imgPreviewBox");
  const img = document.getElementById("imgPreview");
  if (url) {
    img.src = url;
    img.onerror = () => {
      box.style.display = "none";
    };
    box.style.display = "block";
  } else {
    box.style.display = "none";
  }
}

// ─── Send Message ──────────────────────────────────────────
async function sendMessage() {
  const msg = document.getElementById("msgInput").value.trim();
  const uid = document.getElementById("userIdInput").value.trim();
  const imgUrl = document.getElementById("imageInput").value.trim();

  if (!msg) return;
  if (state.mode === "push" && !uid) return;

  if (state.mode === "broadcast") {
    if (!confirm("This will send to ALL followers. Continue?")) return;
  }

  const btn = document.getElementById("sendBtn");
  btn.textContent = "SENDING...";
  btn.disabled = true;

  try {
    const r = await fetch(`${API}/api/send`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        token: state.token,
        mode: state.mode,
        userId: uid,
        message: msg,
        imageUrl: imgUrl,
      }),
    });
    const data = await r.json();

    const entry = {
      id: Date.now(),
      timestamp: data.timestamp || new Date().toLocaleString(),
      mode: state.mode,
      target: state.mode === "push" ? uid : "ALL",
      message: msg,
      imageUrl: imgUrl || null,
      ok: data.ok,
      status: data.status,
      error: data.body?.message || null,
    };

    state.history.unshift(entry);
    renderHistory();
    updateStats();

    if (data.ok) {
      document.getElementById("msgInput").value = "";
      document.getElementById("imageInput").value = "";
      document.getElementById("imgPreviewBox").style.display = "none";
    }
  } catch (e) {
    alert("Send error: " + e.message);
  }

  updateSendBtn();
}

// ─── History Rendering ─────────────────────────────────────
function renderHistory() {
  const list = document.getElementById("historyList");
  const clearBtn = document.getElementById("clearBtn");

  if (state.history.length === 0) {
    list.innerHTML = '<div class="history-empty">No messages sent yet</div>';
    clearBtn.style.display = "none";
    return;
  }

  clearBtn.style.display = "inline-flex";
  list.innerHTML = state.history
    .map(
      (e) => `
    <div class="history-entry ${e.ok ? "" : "fail"}">
      <div class="history-top">
        <div class="history-tags">
          <span class="tag ${e.mode === "push" ? "tag-push" : "tag-bcast"}">
            ${e.mode === "push" ? "PUSH" : "BCAST"}
          </span>
          <span class="tag ${e.ok ? "tag-sent" : "tag-fail"}">
            ${e.ok ? "✓ SENT" : "✗ FAIL"}
          </span>
        </div>
        <span class="history-time">${escapeHtml(e.timestamp)}</span>
      </div>
      <div class="history-msg">${escapeHtml(e.message)}</div>
      ${e.imageUrl ? '<div class="history-img">🖼 Image attached</div>' : ""}
      <div class="history-meta">
        → ${e.target === "ALL" ? "All followers" : escapeHtml(e.target.slice(0, 20)) + "..."} · HTTP ${e.status}
      </div>
      ${e.error && !e.ok ? `<div class="history-err">${escapeHtml(e.error)}</div>` : ""}
    </div>
  `
    )
    .join("");
}

function clearHistory() {
  state.history = [];
  renderHistory();
  updateStats();
}

// ─── Stats ─────────────────────────────────────────────────
function updateStats() {
  document.getElementById("statTotal").textContent = state.history.length;
  document.getElementById("statSuccess").textContent = state.history.filter((h) => h.ok).length;
  document.getElementById("statFail").textContent = state.history.filter((h) => !h.ok).length;
}

// ─── Utility ───────────────────────────────────────────────
function escapeHtml(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}
