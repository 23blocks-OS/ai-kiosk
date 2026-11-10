/* Raft kiosk: emergency questions answered from a small shelf of public-domain documents.
   Sources are shown under every answer. A code check adds a red box for child doses. */
(function () {
  "use strict";

  var I18N = {
    en: {
      home: "Home", title: "Raft",
      subtitle: "Emergency answers with real sources. A small library, on this box.",
      emergency: "Demo library. Not emergency advice. In an emergency, call 911.",
      badge: "Library on this box: 9 US public documents. No internet needed to answer.",
      ex_smoke: "Wildfire smoke", ex_generator: "Generator at home", ex_water: "Safe water", ex_child: "A child's fever",
      status_idle: "Ready to help", status_thinking: "Searching the documents…",
      chat_empty: "Ask a question or tap an example. I answer only from what the documents say, and I show where I read it.",
      input_label: "Type your question", input_placeholder: "Type your question…", send: "Send",
      privacy: "Nothing is recorded. Nothing leaves this device.",
      who_you: "You", who_agent: "Raft", sources: "Sources", page: "page",
      not_authorized: "This app is not authorized to use the agent. Please tell whoever runs it.",
      offline: "I couldn't reach the agent right now. Please try again in a moment.",
      q_smoke: "Wildfire smoke is heavy outside. How do I protect my family indoors?",
      q_generator: "Is it safe to run a generator in my garage?",
      q_water: "How do I make water safe to drink in an emergency?",
      q_child: "My 4-year-old has a fever. How much ibuprofen can I give?"
    }
  };

  var lang = "en"; /* the shelf is English only, so the page is English only */
  var t = function (k) { return I18N.en[k] || k; };
  var $ = function (id) { return document.getElementById(id); };
  var params = new URLSearchParams(window.location.search);
  var chat = $("chat"), chatEmpty = $("chat-empty"), input = $("input"), statusText = $("status-text"), statusEl = $("status");
  var thinking = false;

  function apiHeaders() {
    var h = { "Content-Type": "application/json" };
    var cfg = window.KIOSK_CONFIG;
    if (cfg && cfg.apiKey) h["Authorization"] = "Bearer " + cfg.apiKey;
    return h;
  }

  async function apiPost(body) {
    try {
      var resp = await fetch(window.location.origin + "/api/chat", { method: "POST", headers: apiHeaders(), body: JSON.stringify(body) });
      if (resp.status === 401 || resp.status === 403) return { reply: t("not_authorized") };
      return await resp.json().catch(function () { return null; });
    } catch (e) { return null; }
  }

  function setStatus(state) {
    statusEl.setAttribute("data-state", state);
    statusText.textContent = t("status_" + state);
  }

  function addMessage(who, text, extra) {
    if (chatEmpty) { chatEmpty.remove(); chatEmpty = null; }
    var div = document.createElement("div");
    div.className = "chat-message " + who;
    var whoEl = document.createElement("span");
    whoEl.className = "who";
    whoEl.textContent = who === "user" ? t("who_you") : t("who_agent");
    div.appendChild(whoEl);
    if (who === "agent" && window.KioskMarkdown) window.KioskMarkdown.render(text, div);
    else div.appendChild(document.createTextNode(text));
    if (extra && extra.warn) {
      var w = document.createElement("div");
      w.className = "warn-box";
      w.setAttribute("role", "alert");
      w.textContent = extra.warn;
      div.appendChild(w);
    }
    if (extra && extra.sources && extra.sources.length) {
      var ul = document.createElement("ul");
      ul.className = "sources";
      extra.sources.forEach(function (s) {
        var li = document.createElement("li");
        var d = document.createElement("details");
        var sum = document.createElement("summary");
        sum.textContent = "[" + s.n + "] " + s.title + " — " + t("page") + " " + s.page;
        var p = document.createElement("p");
        p.textContent = s.excerpt;
        d.appendChild(sum); d.appendChild(p); li.appendChild(d); ul.appendChild(li);
      });
      div.appendChild(ul);
    }
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
  }

  async function answer(text) {
    if (thinking) return; /* one question at a time */
    thinking = true;
    try {
      addMessage("user", text);
      setStatus("thinking");
      var data = await apiPost({ message: text, lang: lang, kiosk: "raft" });
      addMessage("agent", data && data.reply ? data.reply : t("offline"), data || {});
    } finally {
      thinking = false;
      setStatus("idle");
    }
  }

  function setLang() {
    document.querySelectorAll("[data-i18n]").forEach(function (el) { el.textContent = t(el.getAttribute("data-i18n")); });
    document.querySelectorAll("[data-i18n-placeholder]").forEach(function (el) { el.setAttribute("placeholder", t(el.getAttribute("data-i18n-placeholder"))); });
    setStatus(statusEl.getAttribute("data-state") || "idle");
  }

  $("composer").addEventListener("submit", function (e) {
    e.preventDefault();
    var text = input.value.trim();
    if (!text || thinking) return;
    input.value = "";
    answer(text);
  });

  document.querySelectorAll("[data-q]").forEach(function (btn) {
    btn.addEventListener("click", function () { answer(t("q_" + btn.getAttribute("data-q"))); });
  });

  /* Home button keeps ?mode=remote; after IDLE_SECONDS without a touch the page goes home. */
  var homeUrl = "../launcher/" + window.location.search;
  $("home").setAttribute("href", homeUrl);
  var IDLE_SECONDS = Number(params.get("idle")) || 180;
  var idleTimer = null;
  function armIdle() {
    clearTimeout(idleTimer);
    idleTimer = setTimeout(function () {
      if (thinking) { armIdle(); return; }
      window.location.href = homeUrl;
    }, IDLE_SECONDS * 1000);
  }
  ["pointerdown", "keydown", "touchstart", "input"].forEach(function (ev) { document.addEventListener(ev, armIdle, true); });
  armIdle();

  setLang();
})();
