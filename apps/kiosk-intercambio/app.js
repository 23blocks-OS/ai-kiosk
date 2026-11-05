/* Intercambio kiosk — front-end prototype.
   No backend yet: replies are canned and say so honestly.
   Camera starts only on a user tap; voice uses Web Speech API when the
   browser offers it, otherwise the text box is the way in. */
(function () {
  "use strict";

  var I18N = {
    es: {
      title: "Ayuda con formularios",
      subtitle: "Te leo el papel, te lo explico y te ayudo con el siguiente paso.",
      status_idle: "Estoy lista para ayudarte",
      status_listening: "Te escucho…",
      status_thinking: "Estoy pensando…",
      status_speaking: "Te respondo…",
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
      title: "Help with forms",
      subtitle: "I read the paper for you, explain it, and help with the next step.",
      status_idle: "I'm ready to help",
      status_listening: "Listening…",
      status_thinking: "Thinking…",
      status_speaking: "Answering…",
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
  var t = function (key) { return I18N[lang][key] || I18N.es[key] || key; };

  var $ = function (id) { return document.getElementById(id); };
  var statusEl = $("status"), statusText = $("status-text");
  var chat = $("chat"), chatEmpty = $("chat-empty");
  var input = $("input"), micBtn = $("mic"), voiceNote = $("voice-note");
  var pip = $("pip"), pipVideo = $("pip-video"), pipCanvas = $("pip-canvas");
  var pipEmpty = $("pip-empty"), pipLive = $("pip-live");
  var pipFreeze = $("pip-freeze"), pipEnable = $("pip-enable");
  var pipRestore = $("pip-restore");
  var stream = null, frozen = false, recognizing = false, recognition = null;

  function setStatus(state) {
    statusEl.setAttribute("data-state", state);
    statusText.textContent = t("status_" + state);
  }

  function setLang(next) {
    lang = next;
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
    pipLive.textContent = stream ? (frozen ? t("pip_frozen") : t("pip_live")) : t("pip_off");
    setStatus(statusEl.getAttribute("data-state") || "idle");
  }

  $("lang-es").addEventListener("click", function () { setLang("es"); });
  $("lang-en").addEventListener("click", function () { setLang("en"); });

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

  function answer(text) {
    addMessage("user", text);
    setStatus("thinking");
    window.setTimeout(function () {
      var reply = t("demo_reply");
      addMessage("agent", reply);
      speak(reply);
    }, 900);
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
        micBtn.setAttribute("aria-pressed", "false");
        micBtn.querySelector("span").textContent = t("mic_talk");
        if (transcript) answer(transcript);
      };
      recognition.onerror = function () {
        recognizing = false;
        micBtn.setAttribute("aria-pressed", "false");
        micBtn.querySelector("span").textContent = t("mic_talk");
        voiceNote.hidden = false;
        voiceNote.textContent = t("voice_error");
        setStatus("idle");
      };
      recognition.onend = function () {
        recognizing = false;
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
      } catch (e) {
        voiceNote.hidden = false;
        voiceNote.textContent = t("voice_error");
      }
    });
  }

  /* --- Picture-in-Picture camera: starts only on a user tap --- */
  function setPipLive() {
    pipLive.classList.toggle("is-off", !stream);
    pipLive.classList.toggle("is-frozen", Boolean(stream && frozen));
    pipLive.textContent = stream ? (frozen ? t("pip_frozen") : t("pip_live")) : t("pip_off");
  }

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
    if (!stream) return;
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
    pipEmpty.hidden = false;
    pipFreeze.disabled = true;
    frozen = false;
    pip.classList.remove("is-frozen", "is-expanded");
    pip.classList.add("is-hidden");
    pipRestore.hidden = false;
    setPipLive();
  });

  pipRestore.addEventListener("click", function () {
    pip.classList.remove("is-hidden");
    pipRestore.hidden = true;
  });

  setStatus("idle");
})();
