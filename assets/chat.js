/* Chatbot Megève par cœur : bulle « Une question ? » en bas à droite.
   1. Réponses rédigées (data/chat-kb.json → faq) cherchées dans le navigateur : gratuit, sans limite.
   2. Sinon, et si l'IA est activée (GROQ_API_KEY dans Vercel), question envoyée à /api/chat.
   3. Si l'IA est indisponible (quota gratuit atteint…), on propose les pages du site les plus proches. */
(function () {
  if (window.__mpcChat) return; window.__mpcChat = 1;
  const EN = (document.documentElement.lang || "fr").slice(0, 2) === "en";
  const T = EN ? {
    btn: "Ask a question", title: "Ask Megève par cœur", sub: "Skiing, parking, what's on, getting here…",
    hello: "Hello! 👋 Ask me anything about Megève and Combloux: lift passes, parking, what's on, snow, getting here…",
    ph: "Your question…", send: "Send", more: "More info →", close: "Close",
    note: "Automatic answers from the site's content: check important details with the tourist office.",
    think: "Looking it up…", none: "I don't have a ready answer to that. These pages may help:",
    busy: "The assistant is resting for today. These pages may help:", nolink: "Try the tourist office: <a href=\"https://www.megeve-tourisme.fr/en/\" target=\"_blank\" rel=\"noopener\">megeve-tourisme.fr</a>.",
    sug: ["Lift pass prices", "Where to park?", "What's on this weekend?", "How much snow?"], kb: "/data/chat-kb.json"
  } : {
    btn: "Une question ?", title: "Une question ?", sub: "Ski, parkings, agenda, venir…",
    hello: "Bonjour ! 👋 Posez-moi vos questions sur Megève et Combloux : forfaits, parkings, agenda, neige, venir…",
    ph: "Votre question…", send: "Envoyer", more: "En savoir plus →", close: "Fermer",
    note: "Réponses automatiques tirées du site : vérifiez les infos importantes auprès de l'office de tourisme.",
    think: "Je cherche…", none: "Je n'ai pas de réponse toute prête. Ces pages peuvent vous aider :",
    busy: "L'assistant se repose pour aujourd'hui. Ces pages peuvent vous aider :", nolink: "Essayez l'office de tourisme : <a href=\"https://www.megeve-tourisme.fr/\" target=\"_blank\" rel=\"noopener\">megeve-tourisme.fr</a>.",
    sug: ["Prix des forfaits", "Où se garer ?", "Que faire ce week-end ?", "Combien de neige ?"], kb: "/data/chat-kb.json"
  };
  const STOP = new Set("le la les un une des de du d l a au aux et ou en est il elle on je tu vous nous ce cet cette ces pour par sur dans avec sans que qui quoi quel quelle quels quelles comment y faut peut puis the an of to in on at for is are what how do does can i you it and or with from my me be there".split(" "));
  const norm = s => String(s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  const toks = s => norm(s).split(/[^a-z0-9]+/).filter(w => w.length > 1 && !STOP.has(w));
  const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  let KB = null, AI = null, H = [];
  try { H = JSON.parse(sessionStorage.getItem("mpc-chat") || "[]"); } catch (e) {}
  const save = () => { try { sessionStorage.setItem("mpc-chat", JSON.stringify(H.slice(-12))); } catch (e) {} };

  const css = `
#mpc-chat-btn{position:fixed;right:18px;bottom:18px;z-index:70;display:flex;align-items:center;gap:8px;background:#c8323d;color:#fff;border:0;border-radius:999px;padding:12px 16px 12px 14px;font:800 .95rem "Nunito Sans",system-ui,sans-serif;box-shadow:0 10px 30px rgba(10,20,40,.3);cursor:pointer;transition:transform .2s}
#mpc-chat-btn:hover{transform:translateY(-2px)}#mpc-chat-btn span{font-size:1.25rem;line-height:1}
body:has(#mpc-inst) #mpc-chat-btn{bottom:96px}
#mpc-chat{position:fixed;right:18px;bottom:18px;z-index:80;width:370px;max-width:calc(100vw - 24px);height:560px;max-height:calc(100vh - 36px);display:none;flex-direction:column;background:#fff;color:#1c2533;border-radius:22px;box-shadow:0 20px 60px rgba(10,20,40,.35);overflow:hidden;font:400 .95rem/1.45 "Nunito Sans",system-ui,sans-serif}
#mpc-chat.on{display:flex}
#mpc-chat header{background:linear-gradient(120deg,#0b1c36,#1f3d7a);color:#fff;padding:14px 16px;display:flex;align-items:center;gap:10px}
#mpc-chat header img{width:36px;height:36px;border-radius:50%}#mpc-chat header b{display:block;font-size:1.02rem}#mpc-chat header small{opacity:.8}
#mpc-chat header button{margin-left:auto;background:transparent;border:0;color:#fff;font-size:1.3rem;cursor:pointer;opacity:.8;padding:4px 8px}
#mpc-chat .msgs{flex:1;overflow-y:auto;padding:14px;display:flex;flex-direction:column;gap:10px;background:#f1f4f9}
#mpc-chat .m{max-width:86%;padding:10px 13px;border-radius:16px;word-wrap:break-word}
#mpc-chat .m.b{background:#fff;border:1px solid #dbe3ee;border-bottom-left-radius:6px;align-self:flex-start}
#mpc-chat .m.u{background:#1f3d7a;color:#fff;border-bottom-right-radius:6px;align-self:flex-end}
#mpc-chat .m a{color:#c8323d;font-weight:700}#mpc-chat .m.u a{color:#fff}
#mpc-chat .m .more{display:inline-block;margin-top:6px}
#mpc-chat .m ul{margin:6px 0 0;padding-left:18px}
#mpc-chat .m.t{color:#5d6878;font-style:italic}
#mpc-chat .sug{display:flex;flex-wrap:wrap;gap:6px}
#mpc-chat .sug button{border:1.5px solid #dbe3ee;background:#fff;color:#1c2533;border-radius:999px;padding:6px 11px;font:700 .82rem inherit;cursor:pointer}
#mpc-chat .sug button:hover{border-color:#c8323d;color:#c8323d}
#mpc-chat form{display:flex;gap:8px;padding:10px;border-top:1px solid #dbe3ee;background:#fff}
#mpc-chat input{flex:1;border:1.5px solid #dbe3ee;border-radius:999px;padding:10px 14px;font:inherit;color:inherit;background:#fff;min-width:0}
#mpc-chat input:focus{outline:none;border-color:#1f3d7a}
#mpc-chat form button{background:#c8323d;color:#fff;border:0;border-radius:999px;padding:0 16px;font:800 .9rem inherit;cursor:pointer}
#mpc-chat .note{font-size:.72rem;color:#5d6878;padding:0 14px 10px;background:#fff}
@media (prefers-color-scheme:dark){#mpc-chat{background:#162133;color:#e9eef6}#mpc-chat .msgs{background:#0e1522}#mpc-chat .m.b{background:#162133;border-color:#26344a}
#mpc-chat form,#mpc-chat .note{background:#162133;border-color:#26344a}#mpc-chat input{background:#0e1522;border-color:#26344a}#mpc-chat .sug button{background:#162133;color:#e9eef6;border-color:#26344a}#mpc-chat .note{color:#a3b0c2}}
@media (max-width:520px){#mpc-chat{right:0;bottom:0;width:100vw;max-width:100vw;height:100%;max-height:100%;border-radius:0}#mpc-chat-btn{right:12px;bottom:12px}body:has(#mpc-inst) #mpc-chat-btn{bottom:92px}}
@media print{#mpc-chat-btn,#mpc-chat{display:none!important}}`;
  const st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);
  const btn = document.createElement("button"); btn.id = "mpc-chat-btn"; btn.type = "button"; btn.setAttribute("aria-haspopup", "dialog");
  btn.innerHTML = `<span aria-hidden="true">💬</span>${T.btn}`;
  const box = document.createElement("section"); box.id = "mpc-chat"; box.setAttribute("role", "dialog"); box.setAttribute("aria-label", T.title);
  box.innerHTML = `<header><img src="/img/logo.png" alt=""><div><b>${T.title}</b><small>${T.sub}</small></div><button type="button" aria-label="${T.close}">✕</button></header>
<div class="msgs" aria-live="polite"></div><form><input type="text" maxlength="400" placeholder="${T.ph}" aria-label="${T.ph}" autocomplete="off"><button type="submit">${T.send}</button></form><div class="note">${T.note}</div>`;
  document.body.appendChild(btn); document.body.appendChild(box);
  const msgs = box.querySelector(".msgs"), input = box.querySelector("input");

  function md(s) { // texte de l'IA → HTML sûr (liens [titre](url) et **gras** seulement)
    let h = esc(s).replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>");
    h = h.replace(/\[([^\]]+)\]\(((?:https?:\/\/|\/)[^\s)]+)\)/g, (m, t, u) => {
      const ext = /^https?:/.test(u) && !/^https:\/\/(www\.)?megeveparcoeur\.fr/.test(u);
      return `<a href="${u.replace(/"/g, "%22")}"${ext ? ' target="_blank" rel="noopener"' : ""}>${t}</a>`;
    });
    return h.replace(/\n/g, "<br>");
  }
  function add(cls, html) { const d = document.createElement("div"); d.className = "m " + cls; d.innerHTML = html; msgs.appendChild(d); msgs.scrollTop = msgs.scrollHeight; return d; }
  function render() {
    msgs.innerHTML = ""; add("b", esc(T.hello));
    for (const m of H) add(m.r === "u" ? "u" : "b", m.r === "u" ? esc(m.t) : (m.html || md(m.t)));
    if (!H.length) { const s = document.createElement("div"); s.className = "sug"; for (const q of T.sug) { const b = document.createElement("button"); b.type = "button"; b.textContent = q; b.onclick = () => ask(q); s.appendChild(b); } msgs.appendChild(s); }
    msgs.scrollTop = msgs.scrollHeight;
  }
  async function load() {
    if (!KB) { try { KB = await (await fetch(T.kb)).json(); } catch (e) { KB = { faq: [], chunks: { fr: [], en: [] } }; } }
    if (AI === null) { try { AI = !!(await (await fetch("/api/chat")).json()).enabled; } catch (e) { AI = false; } }
  }
  function local(q) {
    const qt = toks(q); let best = null;
    for (const f of KB.faq) {
      let s = 0;
      for (const k0 of f.kw) { const half = k0[0] === "~", k = half ? k0.slice(1) : k0, p = k.endsWith("*"), w = p ? k.slice(0, -1) : k; if (STOP.has(w)) continue; if (qt.some(t => p ? t.startsWith(w) : t === w)) s += half ? .5 : 1; }
      if (s && (!best || s > best.s)) best = { f, s };
    }
    return best;
  }
  function pages(q) {
    const qt = toks(q), seen = new Set(), out = [];
    const sc = (KB.chunks[EN ? "en" : "fr"] || []).map(c => { const t = norm(c.t + " " + c.x); return { c, s: qt.reduce((a, w) => a + (t.includes(w.length > 4 ? w.slice(0, -1) : w) ? 1 : 0), 0) }; }).filter(x => x.s).sort((a, b) => b.s - a.s);
    for (const { c } of sc) { if (seen.has(c.u)) continue; seen.add(c.u); out.push(c); if (out.length === 3) break; }
    return out;
  }
  const faqHtml = f => `${EN ? f.en : f.fr}<br><a class="more" href="${EN ? f.u_en : f.u_fr}">${T.more}</a>`;
  function links(q, head) {
    const p = pages(q);
    return p.length ? `${head}<ul>${p.map(c => `<li><a href="${c.u}">${esc(c.t.split(" — ").pop())}</a></li>`).join("")}</ul>` : T.nolink;
  }
  function reply(html, t) { H.push({ r: "b", t: t || html.replace(/<[^>]+>/g, ""), html }); save(); add("b", html); }

  let busy = false;
  async function ask(q) {
    q = String(q || "").trim(); if (!q || busy) return; busy = true;
    const sug = msgs.querySelector(".sug"); if (sug) sug.remove();
    H.push({ r: "u", t: q }); save(); add("u", esc(q)); input.value = "";
    const wait = add("b t", T.think);
    try {
      await load();
      const m = local(q);
      if (m && (!AI || (m.s >= 2 && !m.f.live))) { wait.remove(); reply(faqHtml(m.f)); return; }
      if (AI) {
        try {
          const r = await fetch("/api/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ q, lang: EN ? "en" : "fr", h: H.slice(-5, -1).map(x => ({ r: x.r, t: x.t })) }) });
          const j = await r.json();
          if (j.ok && j.a) { wait.remove(); H.push({ r: "b", t: j.a }); save(); add("b", md(j.a)); return; }
          wait.remove(); reply(m ? faqHtml(m.f) : links(q, j.error === "limit" || j.error === "busy" ? T.busy : T.none)); return;
        } catch (e) { /* réseau : on retombe sur la FAQ */ }
      }
      wait.remove(); reply(m ? faqHtml(m.f) : links(q, T.none));
    } finally { busy = false; input.focus(); }
  }
  function open() { box.classList.add("on"); btn.style.display = "none"; render(); load(); setTimeout(() => input.focus(), 50); }
  function close() { box.classList.remove("on"); btn.style.display = ""; btn.focus(); }
  btn.onclick = open; box.querySelector("header button").onclick = close;
  box.addEventListener("keydown", e => { if (e.key === "Escape") close(); });
  box.querySelector("form").onsubmit = e => { e.preventDefault(); ask(input.value); };
})();
