/* Intercambio kiosk — front-end prototype.
   No backend yet: replies are canned and say so honestly.
   Camera starts only on a user tap; voice uses Web Speech API when the
   browser offers it, otherwise the text box is the way in. */
(function () {
  "use strict";

  var I18N = {
    es: {
      home: "Inicio",
      title: "Ayuda con formularios",
      subtitle: "Te leo el papel, te lo explico y te ayudo con el siguiente paso.",
      status_idle: "Estoy lista para ayudarte",
      status_listening: "Te escucho…",
      status_thinking: "Estoy pensando…",
      status_speaking: "Te respondo…",
      visual_waveform: "Onda",
      visual_mascot: "Mascota · pronto",
      visual_face: "Rostro · pronto",
      visual_soon_mascot: "Próximamente: una mascota sencilla que te mira y mira tu documento. Por ahora, la onda es la cara del agente.",
      visual_soon_face: "Próximamente: un rostro amistoso con movimiento de labios. Por ahora, la onda es la cara del agente.",
      visual_look_label: "Aspecto",
      chat_empty: "Pon un formulario o una carta bajo la cámara, en la ventanita de abajo a la derecha. Luego pregúntame qué dice, o toca el micrófono y habla.",
      mic_talk: "Hablar",
      mic_stop: "Parar",
      input_label: "Escribe tu pregunta",
      input_placeholder: "Escribe tu pregunta…",
      send: "Enviar",
      privacy: "Nada se graba. Nada sale de este equipo.",
      pip_title: "Lo que estoy viendo",
      pip_source: "Cámara",
      pip_off: "Apagada",
      pip_live: "En vivo",
      pip_frozen: "Congelada",
      pip_upload: "Subir foto",
      pip_uploaded: "Foto subida",
      pip_source_upload: "Foto subida",
      pip_upload_note: "La foto se usa solo para esta respuesta, no se guarda.",
      pip_empty_remote: "Sube una foto de tu formulario o carta, y pregúntame qué dice.",
      chat_empty_remote: "Sube una foto de tu formulario o carta en la ventanita de abajo a la derecha. Luego pregúntame qué dice.",
      pip_upload_error: "No pude leer esa foto. Intenta con otra imagen.",
      pip_empty: "La cámara está apagada. Actívala para que yo pueda ver tu documento.",
      pip_enable: "Activar cámara",
      pip_freeze: "Congelar",
      pip_resume: "Reanudar",
      pip_restore: "Mostrar lo que veo",
      pip_denied: "No puedo usar la cámara: el permiso fue negado. Puedes escribir tu pregunta abajo, o permitir la cámara en los ajustes del navegador e intentarlo de nuevo.",
      pip_error: "No pude abrir la cámara en este equipo. Puedes escribir tu pregunta abajo.",
      voice_unavailable: "La voz no está disponible en este navegador: escribe tu pregunta en el cuadro de texto.",
      voice_error: "No pude escucharte. Intenta de nuevo o escribe tu pregunta.",
      who_you: "Tú",
      who_agent: "Agente",
      demo_reply: "Esto es una demostración: todavía no estoy conectado al modelo local. Cuando el Jetson esté listo, leeré el documento que se ve en la ventanita y te lo explicaré aquí."
    },
    en: {
      home: "Home",
      title: "Help with forms",
      subtitle: "I read the paper for you, explain it, and help with the next step.",
      status_idle: "I'm ready to help",
      status_listening: "Listening…",
      status_thinking: "Thinking…",
      status_speaking: "Answering…",
      visual_waveform: "Wave",
      visual_mascot: "Mascot · soon",
      visual_face: "Face · soon",
      visual_soon_mascot: "Coming soon: a simple mascot that looks at you and at your document. For now, the wave is the agent's face.",
      visual_soon_face: "Coming soon: a friendly face with lip-sync. For now, the wave is the agent's face.",
      visual_look_label: "Look",
      chat_empty: "Put a form or letter under the camera, in the small window at the bottom right. Then ask me what it says, or tap the microphone and speak.",
      mic_talk: "Speak",
      mic_stop: "Stop",
      input_label: "Type your question",
      input_placeholder: "Type your question…",
      send: "Send",
      privacy: "Nothing is recorded. Nothing leaves this device.",
      pip_title: "What I'm seeing",
      pip_source: "Camera",
      pip_off: "Off",
      pip_live: "Live",
      pip_frozen: "Frozen",
      pip_upload: "Upload a photo",
      pip_uploaded: "Photo uploaded",
      pip_source_upload: "Uploaded photo",
      pip_upload_note: "The photo is used for this answer only, it is not saved.",
      pip_empty_remote: "Upload a photo of your form or letter, then ask me what it says.",
      chat_empty_remote: "Upload a photo of your form or letter in the small window at the bottom right. Then ask me what it says.",
      pip_upload_error: "I couldn't read that photo. Try another image.",
      pip_empty: "The camera is off. Turn it on so I can see your document.",
      pip_enable: "Enable camera",
      pip_freeze: "Freeze",
      pip_resume: "Resume",
      pip_restore: "Show what I see",
      pip_denied: "I can't use the camera: permission was denied. You can type your question below, or allow the camera in the browser settings and try again.",
      pip_error: "I couldn't open the camera on this device. You can type your question below.",
      voice_unavailable: "Voice isn't available in this browser — type your question in the text box instead.",
      voice_error: "I couldn't hear you. Try again or type your question.",
      who_you: "You",
      who_agent: "Agent",
      demo_reply: "This is a demo: I'm not connected to the local model yet. When the Jetson is ready, I'll read the document in the small window and explain it to you here."
    }
  };

  var lang = "es";
  try { if (sessionStorage.getItem("kiosk-lang") === "en") lang = "en"; } catch (e) { /* storage off: Spanish */ }
  var t = function (key) { return I18N[lang][key] || I18N.es[key] || key; };

  var params = new URLSearchParams(window.location.search);
  var remoteMode = params.get("mode") === "remote";
  var uploadedImage = null; /* base64 JPEG, no data: prefix, max 1024px */
  var pipSource = "camera"; /* "camera" | "upload" */

  /* Backend: same origin when served by the backend itself (tunnel
     mode, one port), else the backend on :8001 next to a static server.
     apiPost falls back to the other base if the first one 404s. */
  function apiBases() {
    var local = window.location.hostname === "localhost" ||
      window.location.hostname === "127.0.0.1";
    var bases = local
      ? ["http://127.0.0.1:8001", window.location.origin]
      : [window.location.origin, "http://127.0.0.1:8001"];
    return bases.filter(function (b, i) { return bases.indexOf(b) === i; });
  }

  async function apiPost(path, body) {
    var bases = apiBases();
    for (var i = 0; i < bases.length; i++) {
      try {
        var resp = await fetch(bases[i] + path, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body)
        });
        if (resp.ok || resp.status === 503) return await resp.json();
        if ((resp.status === 404 || resp.status === 501) && i + 1 < bases.length) continue;
        return await resp.json().catch(function () { return null; });
      } catch (e) { /* try the next base */ }
    }
    return null;
  }

  var $ = function (id) { return document.getElementById(id); };
  var statusEl = $("status"), statusText = $("status-text");
  var chat = $("chat"), chatEmpty = $("chat-empty");
  var input = $("input"), micBtn = $("mic"), voiceNote = $("voice-note");
  var pip = $("pip"), pipVideo = $("pip-video"), pipCanvas = $("pip-canvas");
  var pipImg = $("pip-img"), pipFile = $("pip-file"), pipBadge = $("pip-badge");
  var pipEmpty = $("pip-empty"), pipLive = $("pip-live");
  var pipFreeze = $("pip-freeze"), pipEnable = $("pip-enable");
  var pipRestore = $("pip-restore");
  var stream = null, frozen = false, recognizing = false, recognition = null;
  var agentVisual = "waveform"; /* "waveform" built; "mascot"/"face" = coming soon */
  var soonMode = null;
  var visualEl = $("agent-visual"), visualSoon = $("visual-soon");
  var micLevel = null; /* {ctx, analyser, stream, raf} or null — real level only */

  function setVisualLooking() {
    /* Glance at the PiP (bottom-right) while reading a frozen frame,
       or while thinking about an uploaded photo. Subtle, not cartoonish. */
    var looking = frozen || Boolean(uploadedImage && statusEl.getAttribute("data-state") === "thinking");
    visualEl.setAttribute("data-looking", String(looking));
  }

  function setAgentVisual(mode) {
    /* Mascot/face are not built: show a plain "coming soon" panel,
       never a fake face. Waveform stays the active visual. */
    if (mode === "waveform") {
      agentVisual = "waveform";
      soonMode = null;
      visualEl.setAttribute("data-visual", "waveform");
      visualSoon.hidden = true;
      $("visual-waveform").setAttribute("aria-pressed", "true");
      $("visual-mascot").setAttribute("aria-pressed", "false");
      $("visual-face").setAttribute("aria-pressed", "false");
      return;
    }
    soonMode = mode;
    visualSoon.hidden = false;
    visualSoon.textContent = t("visual_soon_" + mode);
  }

  function setStatus(state) {
    statusEl.setAttribute("data-state", state);
    visualEl.setAttribute("data-state", state);
    statusText.textContent = t("status_" + state);
    setVisualLooking();
  }

  function setLang(next) {
    lang = next;
    try { sessionStorage.setItem("kiosk-lang", next); } catch (e) { /* ignore */ }
    document.documentElement.lang = next;
    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      el.textContent = t(el.getAttribute("data-i18n"));
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach(function (el) {
      el.setAttribute("placeholder", t(el.getAttribute("data-i18n-placeholder")));
    });
    $("lang-es").setAttribute("aria-pressed", String(next === "es"));
    $("lang-en").setAttribute("aria-pressed", String(next === "en"));
    pipFreeze.textContent = frozen ? t("pip_resume") : t("pip_freeze");
    pipBadge.textContent = pipSource === "upload" ? t("pip_source_upload") : t("pip_source");
    pipLive.textContent = pipSource === "upload" ? t("pip_uploaded")
      : (stream ? (frozen ? t("pip_frozen") : t("pip_live")) : t("pip_off"));
    if (remoteMode) {
      if (chatEmpty) chatEmpty.textContent = t("chat_empty_remote");
      if (!pipEmpty.hidden) pipEmpty.querySelector("p").textContent = t("pip_empty_remote");
      pipEnable.hidden = true;
    }
    if (soonMode) visualSoon.textContent = t("visual_soon_" + soonMode);
    setStatus(statusEl.getAttribute("data-state") || "idle");
  }

  $("lang-es").addEventListener("click", function () { setLang("es"); });
  $("lang-en").addEventListener("click", function () { setLang("en"); });
  $("visual-waveform").addEventListener("click", function () { setAgentVisual("waveform"); });
  $("visual-mascot").addEventListener("click", function () { setAgentVisual("mascot"); });
  $("visual-face").addEventListener("click", function () { setAgentVisual("face"); });

  /* Mic level for the listening ripple: a real analyser when the
     browser grants an audio stream; if it does not, the CSS ripple
     runs on its own — no fake level is ever invented. */
  function startMicLevel() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia ||
        !window.AudioContext) return;
    navigator.mediaDevices.getUserMedia({ audio: true }).then(function (s) {
      var ctx = new AudioContext();
      var analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      ctx.createMediaStreamSource(s).connect(analyser);
      var data = new Uint8Array(analyser.frequencyBinCount);
      var tick = function () {
        if (!micLevel) return;
        analyser.getByteTimeDomainData(data);
        var peak = 0;
        for (var i = 0; i < data.length; i++) peak = Math.max(peak, Math.abs(data[i] - 128) / 128);
        visualEl.style.setProperty("--level", Math.min(1, peak * 2).toFixed(2));
        micLevel.raf = requestAnimationFrame(tick);
      };
      micLevel = { ctx: ctx, stream: s, raf: requestAnimationFrame(tick) };
    }).catch(function () { /* no audio stream: CSS ripple only */ });
  }
  function stopMicLevel() {
    if (!micLevel) return;
    cancelAnimationFrame(micLevel.raf);
    micLevel.stream.getTracks().forEach(function (tr) { tr.stop(); });
    micLevel.ctx.close().catch(function () {});
    micLevel = null;
    visualEl.style.setProperty("--level", "0.35");
  }

  function addMessage(who, text) {
    if (chatEmpty) chatEmpty.remove();
    var div = document.createElement("div");
    div.className = "chat-message " + who;
    var whoEl = document.createElement("span");
    whoEl.className = "who";
    whoEl.textContent = who === "user" ? t("who_you") : t("who_agent");
    div.appendChild(whoEl);
    div.appendChild(document.createTextNode(text));
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
  }

  function speak(text) {
    if (!("speechSynthesis" in window)) { setStatus("idle"); return; }
    try {
      var utter = new SpeechSynthesisUtterance(text);
      utter.lang = lang === "es" ? "es-ES" : "en-US";
      utter.onend = function () { setStatus("idle"); };
      utter.onerror = function () { setStatus("idle"); };
      setStatus("speaking");
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(utter);
    } catch (e) { setStatus("idle"); }
  }

  async function answer(text) {
    addMessage("user", text);
    setStatus("thinking");
    /* Ask the backend (Ollama when it is up). If it cannot be reached
       at all, fall back to the honest canned demo reply — never fake
       a model answer. An uploaded photo goes to /api/vision. */
    var data = null;
    if (uploadedImage) {
      data = await apiPost("/api/vision", { message: text, lang: lang, image_base64: uploadedImage });
    } else {
      data = await apiPost("/api/chat", { message: text, lang: lang });
    }
    var reply = (data && data.reply) ? data.reply : t("demo_reply");
    addMessage("agent", reply);
    speak(reply);
  }

  $("composer").addEventListener("submit", function (e) {
    e.preventDefault();
    var text = input.value.trim();
    if (!text) return;
    input.value = "";
    answer(text);
  });

  /* --- Voice (Web Speech API, if the browser has it) --- */
  var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    micBtn.disabled = true;
    voiceNote.hidden = false;
    voiceNote.textContent = t("voice_unavailable");
  } else {
    micBtn.addEventListener("click", function () {
      if (recognizing) { try { recognition.stop(); } catch (e) {} return; }
      recognition = new SpeechRecognition();
      recognition.lang = lang === "es" ? "es-ES" : "en-US";
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;
      recognition.onresult = function (e) {
        var transcript = e.results[0][0].transcript;
        recognizing = false;
        stopMicLevel();
        micBtn.setAttribute("aria-pressed", "false");
        micBtn.querySelector("span").textContent = t("mic_talk");
        if (transcript) answer(transcript);
      };
      recognition.onerror = function () {
        recognizing = false;
        stopMicLevel();
        micBtn.setAttribute("aria-pressed", "false");
        micBtn.querySelector("span").textContent = t("mic_talk");
        voiceNote.hidden = false;
        voiceNote.textContent = t("voice_error");
        setStatus("idle");
      };
      recognition.onend = function () {
        recognizing = false;
        stopMicLevel();
        micBtn.setAttribute("aria-pressed", "false");
        micBtn.querySelector("span").textContent = t("mic_talk");
        if (statusEl.getAttribute("data-state") === "listening") setStatus("idle");
      };
      try {
        recognition.start();
        recognizing = true;
        micBtn.setAttribute("aria-pressed", "true");
        micBtn.querySelector("span").textContent = t("mic_stop");
        voiceNote.hidden = true;
        setStatus("listening");
        startMicLevel();
      } catch (e) {
        voiceNote.hidden = false;
        voiceNote.textContent = t("voice_error");
      }
    });
  }

  /* --- Picture-in-Picture camera: starts only on a user tap --- */
  function setPipLive() {
    pipLive.classList.toggle("is-off", !stream && pipSource !== "upload");
    pipLive.classList.toggle("is-frozen", Boolean(stream && frozen));
    pipLive.textContent = pipSource === "upload" ? t("pip_uploaded")
      : (stream ? (frozen ? t("pip_frozen") : t("pip_live")) : t("pip_off"));
    pipBadge.textContent = pipSource === "upload" ? t("pip_source_upload") : t("pip_source");
  }

  /* --- Upload a photo (remote mode): downscale in-browser to max
         1024px on the long edge, show it in the PiP, send it to
         /api/vision with the next question. Used for this answer
         only, never stored. --- */
  function downscaleImage(file) {
    return new Promise(function (resolve, reject) {
      var reader = new FileReader();
      reader.onerror = function () { reject(new Error("read")); };
      reader.onload = function () {
        var img = new Image();
        img.onerror = function () { reject(new Error("image")); };
        img.onload = function () {
          var scale = Math.min(1, 1024 / Math.max(img.width, img.height));
          var canvas = document.createElement("canvas");
          canvas.width = Math.round(img.width * scale);
          canvas.height = Math.round(img.height * scale);
          canvas.getContext("2d").drawImage(img, 0, 0, canvas.width, canvas.height);
          resolve(canvas.toDataURL("image/jpeg", 0.85));
        };
        img.src = reader.result;
      };
      reader.readAsDataURL(file);
    });
  }

  function showUploadedPhoto(dataUrl) {
    uploadedImage = dataUrl.split(",")[1];
    pipSource = "upload";
    pipImg.src = dataUrl;
    pipImg.hidden = false;
    pipVideo.hidden = true;
    pipEmpty.hidden = true;
    pipFreeze.disabled = true;
    setPipLive();
  }

  pipFile.addEventListener("change", function () {
    var file = pipFile.files && pipFile.files[0];
    pipFile.value = "";
    if (!file) return;
    downscaleImage(file).then(showUploadedPhoto).catch(function () {
      pipEmpty.querySelector("p").textContent = t("pip_upload_error");
    });
  });

  $("pip-upload").addEventListener("click", function () { pipFile.click(); });
  $("pip-upload-empty").addEventListener("click", function () { pipFile.click(); });

  pipEnable.addEventListener("click", function () {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      pipEmpty.querySelector("p").textContent = t("pip_error");
      return;
    }
    navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" }, audio: false })
      .then(function (s) {
        stream = s;
        pipVideo.srcObject = s;
        pipVideo.hidden = false;
        pipEmpty.hidden = true;
        pipFreeze.disabled = false;
        setPipLive();
      })
      .catch(function (err) {
        var msg = (err && err.name === "NotAllowedError") ? t("pip_denied") : t("pip_error");
        pipEmpty.querySelector("p").textContent = msg;
      });
  });

  pipFreeze.addEventListener("click", function () {
    if (!stream || pipSource === "upload") return;
    if (!frozen) {
      var w = pipVideo.videoWidth || 640, h = pipVideo.videoHeight || 480;
      pipCanvas.width = w; pipCanvas.height = h;
      pipCanvas.getContext("2d").drawImage(pipVideo, 0, 0, w, h);
      pip.classList.add("is-frozen");
      frozen = true;
    } else {
      pip.classList.remove("is-frozen");
      frozen = false;
    }
    pipFreeze.textContent = frozen ? t("pip_resume") : t("pip_freeze");
    setVisualLooking();
    setPipLive();
  });

  /* Tap the PiP body to expand / shrink; buttons inside it are exempt. */
  $("pip-body").addEventListener("click", function (e) {
    if (e.target.closest("button")) return;
    pip.classList.toggle("is-expanded");
  });
  $("pip-header").addEventListener("click", function () {
    pip.classList.toggle("is-expanded");
  });

  $("pip-close").addEventListener("click", function (e) {
    e.stopPropagation();
    if (stream) { stream.getTracks().forEach(function (tr) { tr.stop(); }); stream = null; }
    pipVideo.hidden = true;
    pipVideo.srcObject = null;
    pipImg.hidden = true;
    pipImg.src = "";
    uploadedImage = null;
    pipSource = "camera";
    pipEmpty.hidden = false;
    pipFreeze.disabled = true;
    frozen = false;
    pip.classList.remove("is-frozen", "is-expanded");
    pip.classList.add("is-hidden");
    pipRestore.hidden = false;
    setVisualLooking();
    setPipLive();
  });

  pipRestore.addEventListener("click", function () {
    pip.classList.remove("is-hidden");
    pipRestore.hidden = true;
  });

  /* Remote mode (?mode=remote): upload is the way in, the camera
     button is hidden. The camera is still available as a secondary
     option if the browser has one — setLang hides the button on
     every language switch, and the initial setLang call below
     applies the remote copy on first load too. */
  if (remoteMode) pipEnable.hidden = true;

  /* --- Back to the selector: Home button and idle reset ---
     Nothing in this page is stored, so leaving it ends the camera and
     clears the chat and the photo. After IDLE_SECONDS with no touch the
     page goes home, and the next visitor starts clean (language too).
     ?idle=N sets the delay in seconds (default 180). */
  var homeUrl = "../launcher/" + window.location.search;
  $("home").setAttribute("href", homeUrl);
  var IDLE_SECONDS = Number(params.get("idle")) || 180;
  var idleTimer = null;
  function armIdle() {
    clearTimeout(idleTimer);
    idleTimer = setTimeout(function () {
      var state = statusEl.getAttribute("data-state");
      if (state === "thinking" || state === "listening") { armIdle(); return; }
      if (window.speechSynthesis) window.speechSynthesis.cancel();
      try { sessionStorage.removeItem("kiosk-lang"); } catch (e) { /* ignore */ }
      window.location.href = homeUrl;
    }, IDLE_SECONDS * 1000);
  }
  ["pointerdown", "keydown", "touchstart", "input"].forEach(function (ev) {
    document.addEventListener(ev, armIdle, true);
  });
  armIdle();

  setLang(lang);
})();
