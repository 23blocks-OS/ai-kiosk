/* Kiosk selector. Two jobs: ES/EN text, and carry the page's query string
   (for example ?mode=remote) to the kiosk the visitor picks. */
(function () {
  "use strict";
  var I18N = {
    es: {
      title: "Elige una experiencia",
      subtitle: "Un equipo, un agente. Todo corre en este equipo. Toca una opción para empezar.",
      nonprofit_name: "Organización sin fines de lucro",
      nonprofit_desc: "Ayuda con formularios y cartas para personas recién llegadas. Lee el papel, lo explica y lo traduce.",
      shop_name: "Operador de tienda",
      shop_desc: "Ayuda a pequeños negocios con su programa de Windows de siempre.",
      lifeboat_name: "Raft",
      lifeboat_desc: "Pasos de emergencia tomados de manuales reales. Solo en inglés.",
      live: "Disponible",
      soon: "Próximamente",
      privacy: "Nada se graba. Nada sale de este equipo."
    },
    en: {
      title: "Choose an experience",
      subtitle: "One box, one agent. Everything runs on this device. Tap an option to begin.",
      nonprofit_name: "Nonprofit",
      nonprofit_desc: "Help with forms and letters for people new to the country. It reads the paper, explains it and translates it.",
      shop_name: "Shop Operator",
      shop_desc: "Helps small shops with their everyday Windows software.",
      lifeboat_name: "Raft",
      lifeboat_desc: "Emergency steps taken from real manuals, when everything else is down.",
      live: "Available",
      soon: "Coming soon",
      privacy: "Nothing is recorded. Nothing leaves this device."
    }
  };

  function setLang(lang) {
    document.documentElement.lang = lang;
    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      el.textContent = I18N[lang][el.getAttribute("data-i18n")];
    });
    document.getElementById("lang-es").setAttribute("aria-pressed", String(lang === "es"));
    document.getElementById("lang-en").setAttribute("aria-pressed", String(lang === "en"));
    try { sessionStorage.setItem("kiosk-lang", lang); } catch (e) { /* storage may be off */ }
  }

  document.getElementById("lang-es").addEventListener("click", function () { setLang("es"); });
  document.getElementById("lang-en").addEventListener("click", function () { setLang("en"); });

  document.querySelectorAll("a[data-keep-query]").forEach(function (a) {
    a.setAttribute("href", a.getAttribute("href") + window.location.search);
  });

  var saved = "es";
  try { saved = sessionStorage.getItem("kiosk-lang") || "es"; } catch (e) { /* ignore */ }
  setLang(saved === "en" ? "en" : "es");
})();
