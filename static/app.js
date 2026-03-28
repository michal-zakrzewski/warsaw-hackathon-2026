import Vapi from "https://esm.sh/@vapi-ai/web@2";

const $ = (sel) => document.querySelector(sel);
const screens = { landing: $("#landing"), interview: $("#interview"), completed: $("#completed") };

const btnStart = $("#btn-start");
const btnEnd = $("#btn-end");
const btnMute = $("#btn-mute");
const btnRestart = $("#btn-restart");
const statusBadge = $("#status-badge");
const speakingIndicator = $("#speaking-indicator");
const speakingLabel = $("#speaking-label");
const transcriptEl = $("#transcript");
const landingError = $("#landing-error");

let vapi = null;
let config = null;
let transcript = [];
let muted = false;
let callActive = false;
let lastError = null;

function showScreen(name) {
  Object.entries(screens).forEach(([key, el]) => el.classList.toggle("active", key === name));
}

function showError(msg) {
  landingError.textContent = msg;
  landingError.classList.remove("hidden");
}

function appendMessage(role, text) {
  if (!text || !text.trim()) return;

  const last = transcript[transcript.length - 1];
  const lastBubble = transcriptEl.lastElementChild;

  if (last && last.role === role && lastBubble) {
    last.content += " " + text;
    lastBubble.querySelector(".msg-body").textContent = last.content;
    lastBubble.scrollIntoView({ behavior: "smooth", block: "end" });
    return;
  }

  transcript.push({ role, content: text, timestamp: new Date().toISOString() });

  const div = document.createElement("div");
  div.className = `msg ${role}`;

  const label = document.createElement("span");
  label.className = "msg-label";
  label.textContent = role === "assistant" ? "Advisor" : "You";

  const body = document.createElement("span");
  body.className = "msg-body";
  body.textContent = text;

  div.appendChild(label);
  div.appendChild(body);
  transcriptEl.appendChild(div);
  div.scrollIntoView({ behavior: "smooth", block: "end" });
}

async function loadConfig() {
  try {
    const res = await fetch("/api/config");
    if (!res.ok) throw new Error(`Server error ${res.status}`);
    config = await res.json();

    $("#interview-title").textContent = config.interviewTitle;
    $("#interview-header-title").textContent = config.interviewTitle;
    btnStart.textContent = "Start Assessment";
    btnStart.disabled = false;
  } catch (err) {
    showError("Failed to load config. Is the server running?");
    console.error(err);
  }
}

function initVapi() {
  vapi = new Vapi(config.publicKey);

  vapi.on("call-start", () => {
    callActive = true;
    statusBadge.textContent = "Live";
    statusBadge.classList.add("live");
  });

  vapi.on("call-end", () => {
    console.log("call-end fired. callActive:", callActive, "transcript:", transcript.length, "lastError:", lastError);
    statusBadge.textContent = "Ended";
    statusBadge.classList.remove("live");

    if (transcript.length > 0) {
      saveTranscript();
      showScreen("completed");
    } else if (lastError) {
      showScreen("landing");
      showError("Session failed: " + lastError);
      btnStart.textContent = "Start Assessment";
      btnStart.disabled = false;
    } else {
      showScreen("landing");
      showError(
        "Session ended before the conversation started. " +
        "Check the browser console (F12) for details."
      );
      btnStart.textContent = "Start Assessment";
      btnStart.disabled = false;
    }
    callActive = false;
    lastError = null;
  });

  vapi.on("speech-start", () => {
    speakingIndicator.classList.remove("hidden");
    speakingLabel.textContent = "Advisor is speaking\u2026";
  });

  vapi.on("speech-end", () => {
    speakingIndicator.classList.add("hidden");
  });

  vapi.on("message", (msg) => {
    console.log("Vapi message:", msg);
    if (msg.type === "transcript" && msg.transcriptType === "final") {
      appendMessage(msg.role, msg.transcript);
    }
  });

  vapi.on("error", (err) => {
    console.error("Vapi error:", err);
    const msg = err?.message || err?.error?.message || JSON.stringify(err);
    lastError = msg;
    statusBadge.textContent = "Error";
    statusBadge.classList.remove("live");
  });
}

async function requestMicPermission() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    stream.getTracks().forEach((t) => t.stop());
    return true;
  } catch (err) {
    console.error("Microphone permission denied:", err);
    return false;
  }
}

async function startInterview() {
  btnStart.disabled = true;
  landingError.classList.add("hidden");
  btnStart.textContent = "Requesting microphone\u2026";

  const micAllowed = await requestMicPermission();
  if (!micAllowed) {
    showError(
      "Microphone access is required. Please allow microphone permission " +
      "in your browser and try again."
    );
    btnStart.textContent = "Start Assessment";
    btnStart.disabled = false;
    return;
  }

  btnStart.textContent = "Connecting\u2026";
  transcript = [];
  transcriptEl.innerHTML = "";

  try {
    initVapi();
    await vapi.start(config.assistantConfig);
    showScreen("interview");
  } catch (err) {
    console.error("Failed to start:", err);
    showError("Could not start the session: " + (err.message || err));
    btnStart.textContent = "Start Assessment";
    btnStart.disabled = false;
  }
}

function endInterview() {
  if (vapi) {
    vapi.stop();
  }
}

function toggleMute() {
  if (!vapi) return;
  muted = !muted;
  vapi.setMuted(muted);
  $("#mic-on").classList.toggle("hidden", muted);
  $("#mic-off").classList.toggle("hidden", !muted);
}

async function saveTranscript() {
  if (transcript.length === 0) return;
  try {
    await fetch("/api/transcripts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        interviewTitle: config.interviewTitle,
        messages: transcript,
      }),
    });
  } catch (err) {
    console.error("Failed to save transcript:", err);
  }
}

function restart() {
  showScreen("landing");
  btnStart.textContent = "Start Assessment";
  btnStart.disabled = false;
}

btnStart.addEventListener("click", startInterview);
btnEnd.addEventListener("click", endInterview);
btnMute.addEventListener("click", toggleMute);
btnRestart.addEventListener("click", restart);

loadConfig();
