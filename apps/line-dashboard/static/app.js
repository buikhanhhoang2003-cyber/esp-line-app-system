const statusEl = document.getElementById("status");
const resultEl = document.getElementById("result");
const form = document.getElementById("notify-form");
const messageInput = document.getElementById("message");
const targetTypeEl = document.getElementById("target-type");
const targetIdEl = document.getElementById("target-id");
const targetLabel = document.getElementById("target-label");
const toggleCustomBtn = document.getElementById("toggle-custom");
const customPanel = document.getElementById("custom-panel");
const customUserEl = document.getElementById("custom-user-id");
const customGroupEl = document.getElementById("custom-group-id");
const customTokenEl = document.getElementById("custom-token");

async function fetchStatus() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    statusEl.textContent = data.tokenConfigured
      ? "LINE Notify token is configured. Ready to send messages."
      : "LINE Notify token is not configured. Copy .env.example to .env and set LINE_NOTIFY_TOKEN.";
  } catch (error) {
    statusEl.textContent = "Unable to read status. Check server logs.";
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  resultEl.textContent = "Sending...";
  const message = messageInput.value.trim();
  const targetType = targetTypeEl.value;
  const targetId = targetIdEl.value.trim();
  if (!message) {
    resultEl.textContent = "Please enter a message.";
    return;
  }

  // Determine endpoint and payload
  let url = "/api/line/push";
  let body = {};
  if (targetType === "broadcast") {
    url = "/api/line/broadcast";
    body = { message };
  } else {
    // Determine final target id: prefer custom override when provided
    let finalTarget = targetId;
    if (customPanel.style.display !== "none") {
      if (targetType === "user" && customUserEl.value.trim()) {
        finalTarget = customUserEl.value.trim();
      }
      if (targetType === "group" && customGroupEl.value.trim()) {
        finalTarget = customGroupEl.value.trim();
      }
    }
    if (!finalTarget) {
      resultEl.textContent = "Please enter a target User/Group ID (or provide one in Custom settings).";
      return;
    }
    body = { user_id: finalTarget, message };
  }
  // Attach token override if supplied in custom panel
  if (customPanel.style.display !== "none" && customTokenEl.value.trim()) {
    body.token = customTokenEl.value.trim();
  }

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const data = await res.json();
    if (!res.ok) {
      resultEl.textContent = data.detail || JSON.stringify(data) || "Failed to send notification.";
      return;
    }

    resultEl.textContent = "Message sent successfully.";
    messageInput.value = "";
    targetIdEl.value = "";
    customUserEl.value = customUserEl.value; // keep if user wants
  } catch (error) {
    resultEl.textContent = "Request failed. Check network or server.";
  }
});

// Show/hide target id depending on selected type
function updateTargetField() {
  if (targetTypeEl.value === "broadcast") {
    targetIdEl.style.display = "none";
    targetLabel.style.display = "none";
  } else {
    targetIdEl.style.display = "block";
    targetLabel.style.display = "block";
  }
}

// Toggle custom panel
toggleCustomBtn.addEventListener("click", () => {
  if (customPanel.style.display === "none") {
    customPanel.style.display = "block";
    toggleCustomBtn.textContent = "Hide custom settings";
  } else {
    customPanel.style.display = "none";
    toggleCustomBtn.textContent = "Custom settings";
  }
});

targetTypeEl.addEventListener("change", updateTargetField);
updateTargetField();

// Show/hide target id depending on selected type
function updateTargetField() {
  if (targetTypeEl.value === "broadcast") {
    targetIdEl.style.display = "none";
    targetLabel.style.display = "none";
  } else {
    targetIdEl.style.display = "block";
    targetLabel.style.display = "block";
  }
}

targetTypeEl.addEventListener("change", updateTargetField);
updateTargetField();

fetchStatus();
