/* Shows the model's Markdown as plain HTML. Builds DOM nodes, never innerHTML, so model text cannot inject markup. */
(function () {
  function inline(parent, text) {
    var re = /(\*\*\*|\*\*|__|\*|_|`)(.+?)\1/g, last = 0, m;
    while ((m = re.exec(text))) {
      /* an underscore inside a word (snake_case) is not emphasis */
      if ((m[1][0] === "_") && (/\w/.test(text.charAt(m.index - 1)) || /\w/.test(text.charAt(m.index + m[0].length)))) continue;
      if (m.index > last) parent.appendChild(document.createTextNode(text.slice(last, m.index)));
      var tag = m[1] === "`" ? "code" : m[1] === "***" ? "strong" : (m[1].length === 2 ? "strong" : "em");
      var el = document.createElement(tag);
      if (m[1] === "***") { var e2 = document.createElement("em"); e2.textContent = m[2]; el.appendChild(e2); }
      else el.textContent = m[2];
      parent.appendChild(el);
      last = m.index + m[0].length;
    }
    if (last < text.length) parent.appendChild(document.createTextNode(text.slice(last)));
  }

  function render(text, into) {
    var lines = String(text).replace(/\r/g, "").split("\n"), list = null, para = null;
    function close() { list = null; para = null; }
    lines.forEach(function (line) {
      var l = line.trim(), b = /^[-*•]\s+(.*)/.exec(l), n = /^\d+[.)]\s+(.*)/.exec(l), h = /^#{1,6}\s+(.*)/.exec(l);
      if (!l || /^([-*_]\s*){3,}$/.test(l)) { close(); return; }
      if (b || n) {
        var kind = b ? "ul" : "ol";
        if (!list || list.tagName.toLowerCase() !== kind) { list = document.createElement(kind); into.appendChild(list); }
        para = null;
        var li = document.createElement("li");
        inline(li, (b || n)[1]);
        list.appendChild(li);
        return;
      }
      list = null;
      if (h) { para = null; var s = document.createElement("p"), st = document.createElement("strong"); inline(st, h[1]); s.appendChild(st); into.appendChild(s); return; }
      if (!para) { para = document.createElement("p"); into.appendChild(para); }
      else para.appendChild(document.createElement("br"));
      inline(para, l);
    });
  }

  /* what the voice should read: no asterisks, hashes or backticks */
  function plain(text) {
    return String(text).replace(/^\s*#{1,6}\s+/gm, "").replace(/^\s*[-*•]\s+/gm, "").replace(/(\*\*\*|\*\*|\*|`)/g, "").replace(/(^|\s)_+|_+(\s|$)/g, "$1$2");
  }

  window.KioskMarkdown = { render: render, plain: plain };
})();
