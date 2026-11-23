// Bouton « Partager sur Instagram » des pages Météo & neige et Webcams.
// L'image est dessinée dans le navigateur (canvas), puis « Partager » ouvre la feuille de partage
// du téléphone (Instagram → Story ou Publication). Sur ordinateur, on télécharge l'image.
// - Météo : les 4 villages — maintenant, les 24 h à venir, la neige au sol et la neige prévue sur 7 j
//   (story 1080×1920 ou publication 1080×1350), au village ou en altitude selon le choix de la page.
// - Webcams : la dernière image de chaque webcam (via /api/webcam), les unes sous les autres, en story.
// Stories : fond bleu nuit uni. Aucune photo d'abonné : seulement nos données et les webcams publiques.
(function () {
  const P = location.pathname, CAMS = /\/webcams\//.test(P), METEO = /\/meteo\//.test(P);
  if (!CAMS && !METEO) return;
  const EN = document.documentElement.lang === "en", LOC = EN ? "en-GB" : "fr-FR";
  const T = EN ? {
    btn: "Share on Instagram", h: "Share on Instagram", story: "Story", post: "Post",
    share: "Share", dl: "Download the image", close: "Close", making: "Preparing the image…",
    err: "The image could not be prepared. Please try again in a moment.",
    hintShare: f => `Tap “Share”, then choose Instagram → ${f}.`, hintDl: "Download the image, then post it from the Instagram app.",
    mTitle: "Snow & weather", village: "In the village", alt: "Up the mountain", vil: "Village", alti: "Altitude",
    now: "Now", h24: "Next 24 h", sol: "On the ground", prev: "Next 7 days", snow24: n => `+${n} cm of snow`,
    mSrc: "Open-Meteo forecasts · model estimates", mUrl: "megeveparcoeur.fr/meteo",
    cTitle: "The webcams, live", cSrc: "Skaping webcams", cUrl: "megeveparcoeur.fr/webcams", pick: "Webcams in the story:",
    none: "Pick at least one webcam.", miss: n => `${n} webcam${n > 1 ? "s" : ""} unavailable right now, left out.`,
  } : {
    btn: "Partager sur Instagram", h: "Partager sur Instagram", story: "Story", post: "Publication",
    share: "Partager", dl: "Télécharger l'image", close: "Fermer", making: "Préparation de l'image…",
    err: "L'image n'a pas pu être préparée. Réessayez dans un instant.",
    hintShare: f => `Touchez « Partager », puis choisissez Instagram → ${f}.`, hintDl: "Téléchargez l'image, puis publiez-la depuis l'application Instagram.",
    mTitle: "Météo & neige", village: "Au village", alt: "En altitude", vil: "Village", alti: "Altitude",
    now: "Maintenant", h24: "Prochaines 24 h", sol: "Au sol", prev: "Prévu 7 j", snow24: n => `+${n} cm de neige`,
    mSrc: "Prévisions Open-Meteo · estimations des modèles", mUrl: "megeveparcoeur.fr/meteo",
    cTitle: "Les webcams, en direct", cSrc: "Webcams Skaping", cUrl: "megeveparcoeur.fr/webcams", pick: "Webcams dans la story :",
    none: "Choisissez au moins une webcam.", miss: n => `${n} webcam${n > 1 ? "s" : ""} indisponible${n > 1 ? "s" : ""} pour l'instant, laissée${n > 1 ? "s" : ""} de côté.`,
  };
  const LIST = [
    { id: "village", t: EN ? "Megève village" : "Megève village", v: "Megève", c: "#1f3d7a" },
    { id: "rochebrune", t: "Rochebrune", v: "Megève", c: "#1f3d7a" },
    { id: "mont-d-arbois", t: "Mont d'Arbois", v: "Megève", c: "#1f3d7a" },
    { id: "combloux", t: EN ? "Combloux summit" : "Sommet de Combloux", v: "Combloux", c: "#2f5a44" },
    { id: "jaillet", t: EN ? "Le Jaillet summit" : "Sommet du Jaillet", v: "Le Jaillet", c: "#5b4a86" },
  ];

  // ------------------------------------------------------------------ interface
  const css = `
.ig-btn{display:inline-flex;align-items:center;gap:8px;font:800 .92rem var(--body);color:#fff;border:0;border-radius:999px;padding:10px 18px;cursor:pointer;
  background:linear-gradient(45deg,#f09433,#e6683c 25%,#dc2743 50%,#cc2366 75%,#bc1888);box-shadow:0 10px 24px rgba(188,24,136,.25)}
.ig-btn svg{width:18px;height:18px;flex:none}
.ig-btn:hover{filter:brightness(1.07)}
.ig-dlg{border:0;border-radius:24px;padding:0;width:min(440px,94vw);max-height:94vh;background:var(--card);color:var(--ink);box-shadow:0 30px 80px rgba(0,0,0,.45)}
.ig-dlg::backdrop{background:rgba(5,12,24,.7)}
.ig-in{padding:18px 18px 20px;display:flex;flex-direction:column;gap:12px}
.ig-hd{display:flex;justify-content:space-between;align-items:center;gap:10px}
.ig-hd b{font-family:var(--display);font-size:1.35rem;font-weight:600}
.ig-x{border:0;background:transparent;color:var(--ink);font-size:1.6rem;line-height:1;cursor:pointer;padding:4px 8px}
.ig-seg{display:inline-flex;align-self:center;background:var(--wool);border-radius:999px;padding:4px}
.ig-seg button{font:700 .9rem var(--body);border:0;background:transparent;color:var(--ink);padding:7px 16px;border-radius:999px;cursor:pointer}
.ig-seg button[aria-pressed="true"]{background:#0a1424;color:#fff}
.ig-pv{display:flex;justify-content:center;align-items:center;min-height:200px;background:#0a1424;border-radius:16px;overflow:hidden}
.ig-pv img{display:block;max-width:100%;max-height:54vh;height:auto}
.ig-pv p{color:#bcd3f2;font-weight:700;margin:0;padding:30px;text-align:center}
.ig-cams{display:flex;flex-wrap:wrap;gap:6px}
.ig-cams small{width:100%;color:var(--muted);font-weight:700;font-size:.8rem}
.ig-cams label{font:700 .8rem var(--body);border:1.5px solid var(--line);border-radius:999px;padding:5px 10px;cursor:pointer;user-select:none}
.ig-cams input{position:absolute;opacity:0;pointer-events:none}
.ig-cams label:has(input:checked){background:#0a1424;border-color:#0a1424;color:#fff}
.ig-cams label:has(input:focus-visible){outline:3px solid var(--glow);outline-offset:2px}
.ig-act{display:flex;gap:8px;flex-wrap:wrap}
.ig-act button{flex:1 1 160px;font:800 .95rem var(--body);border-radius:999px;padding:12px 14px;cursor:pointer}
.ig-act .go{border:0;color:#fff;background:linear-gradient(45deg,#f09433,#dc2743 50%,#bc1888)}
.ig-act .dl{border:1.5px solid var(--line);background:transparent;color:var(--ink)}
.ig-act button:disabled{opacity:.5;cursor:default}
.ig-hint{margin:0;color:var(--muted);font-size:.85rem;text-align:center}
.ig-msg{margin:0;color:var(--heart);font-size:.85rem;font-weight:700;text-align:center}
.tools .ig-btn{color:#fff;padding:11px 18px;background:linear-gradient(45deg,#f09433,#e6683c 25%,#dc2743 50%,#cc2366 75%,#bc1888);box-shadow:0 12px 30px rgba(10,20,40,.15)}
@media(max-width:560px){.ig-pv img{max-height:44vh}.ig-in{gap:10px}}`;
  const st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);
  const ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor"/></svg>';
  const btn = document.createElement("button");
  btn.type = "button"; btn.className = "ig-btn"; btn.innerHTML = ICON + T.btn;
  const host = METEO ? document.querySelector(".hero .ctrl") : document.querySelector(".tools");
  if (!host) return;
  if (CAMS) host.insertBefore(btn, host.querySelector(".meteo")); else host.appendChild(btn);

  const dlg = document.createElement("dialog"); dlg.className = "ig-dlg"; dlg.setAttribute("aria-label", T.h);
  dlg.innerHTML = `<div class="ig-in">
    <div class="ig-hd"><b>${T.h}</b><button type="button" class="ig-x" aria-label="${T.close}">×</button></div>
    ${METEO ? `<div class="ig-seg" role="group"><button type="button" data-f="story" aria-pressed="true">${T.story}</button><button type="button" data-f="post" aria-pressed="false">${T.post}</button></div>` : ""}
    <div class="ig-pv" aria-live="polite"><p>${T.making}</p></div>
    ${CAMS ? `<div class="ig-cams"><small>${T.pick}</small>${LIST.map(c => `<label><input type="checkbox" value="${c.id}" checked>${c.t}</label>`).join("")}</div>` : ""}
    <p class="ig-msg" hidden></p>
    <div class="ig-act"><button type="button" class="go" hidden>${T.share}</button><button type="button" class="dl">${T.dl}</button></div>
    <p class="ig-hint"></p></div>`;
  document.body.appendChild(dlg);
  const q = s => dlg.querySelector(s), pv = q(".ig-pv"), go = q(".go"), dl = q(".dl"), hint = q(".ig-hint"), msg = q(".ig-msg");
  let fmt = "story", file = null, url = null, run = 0;
  const canFiles = (() => { try { return !!(navigator.canShare && navigator.canShare({ files: [new File(["x"], "x.png", { type: "image/png" })] })); } catch (_) { return false; } })();
  const setHint = () => { hint.textContent = canFiles ? T.hintShare(fmt === "post" ? T.post : T.story) : T.hintDl; };
  go.hidden = !canFiles;

  async function refresh() {
    const me = ++run; file = null; go.disabled = dl.disabled = true; msg.hidden = true; setHint();
    pv.innerHTML = `<p>${T.making}</p>`;
    try {
      const { canvas, note } = METEO ? await drawMeteo(fmt) : await drawCams();
      const blob = await new Promise((ok, ko) => canvas.toBlob(b => b ? ok(b) : ko(new Error("toBlob")), "image/jpeg", 0.92));
      if (me !== run) return;
      const day = new Date().toLocaleDateString("sv-SE");
      file = new File([blob], `megeveparcoeur-${METEO ? "meteo" : "webcams"}-${day}${METEO && fmt === "post" ? "-post" : ""}.jpg`, { type: "image/jpeg" });
      if (url) URL.revokeObjectURL(url); url = URL.createObjectURL(blob);
      pv.innerHTML = ""; const im = new Image(); im.src = url; im.alt = METEO ? T.mTitle : T.cTitle; pv.appendChild(im);
      if (note) { msg.textContent = note; msg.hidden = false; }
      go.disabled = dl.disabled = false;
    } catch (e) {
      if (me !== run) return;
      pv.innerHTML = `<p>${e && e.userMsg ? e.userMsg : T.err}</p>`;
    }
  }
  function track(how) { try { window.va && window.va("event", { name: "partage_instagram", data: { page: METEO ? "meteo" : "webcams", format: fmt, via: how } }); } catch (_) {} }
  function download() {
    if (!file) return; const a = document.createElement("a");
    a.href = url; a.download = file.name; document.body.appendChild(a); a.click(); a.remove(); track("telechargement");
  }
  go.onclick = () => {
    if (!file) return;
    navigator.share({ files: [file] }).then(() => track("partage")).catch(e => { if (e && e.name !== "AbortError") download(); });
  };
  dl.onclick = download;
  q(".ig-x").onclick = () => dlg.close();
  dlg.addEventListener("click", e => { if (e.target === dlg) dlg.close(); });
  dlg.querySelectorAll("[data-f]").forEach(b => b.onclick = () => {
    fmt = b.dataset.f; dlg.querySelectorAll("[data-f]").forEach(x => x.setAttribute("aria-pressed", x === b)); refresh();
  });
  dlg.querySelectorAll(".ig-cams input").forEach(i => i.onchange = refresh);
  btn.onclick = () => { if (dlg.showModal) dlg.showModal(); else dlg.setAttribute("open", ""); refresh(); };

  // ------------------------------------------------------------------ dessin
  const NAVY = "#0a1424", INK = "#0c1a34", MUTED = "#55657e", BLUE = "#1f4f9a", ICE = "#bcd3f2", RED = "#c8323d";
  const FR = (w, s) => `${w} ${s}px Fraunces, Georgia, serif`;
  const NU = (w, s) => `${w} ${s}px "Nunito Sans", system-ui, -apple-system, "Segoe UI", sans-serif`;
  const EMO = s => `${s}px "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", sans-serif`;
  let fontsReady = null, logo = null;
  function ready() {
    fontsReady = fontsReady || Promise.all([
      document.fonts && document.fonts.load(FR(600, 60)), document.fonts && document.fonts.load(FR(500, 40)),
      document.fonts && document.fonts.load(NU(800, 30)), document.fonts && document.fonts.load(NU(700, 30)),
      new Promise(ok => { const i = new Image(); i.onload = () => { logo = i; ok(); }; i.onerror = ok; i.src = "/img/logo-rond.png"; }),
    ]).catch(() => {});
    return fontsReady;
  }
  function canvas(H) { const c = document.createElement("canvas"); c.width = 1080; c.height = H; const x = c.getContext("2d"); x.fillStyle = NAVY; x.fillRect(0, 0, 1080, H); return [c, x]; }
  function rr(x, X, Y, W, H, R) {
    x.beginPath();
    if (x.roundRect) { x.roundRect(X, Y, W, H, R); return; }
    x.moveTo(X + R, Y); x.arcTo(X + W, Y, X + W, Y + H, R); x.arcTo(X + W, Y + H, X, Y + H, R); x.arcTo(X, Y + H, X, Y, R); x.arcTo(X, Y, X + W, Y, R); x.closePath();
  }
  function fit(x, text, maxW, font, size) { let s = size; x.font = font(s); while (s > 12 && x.measureText(text).width > maxW) { s -= 2; x.font = font(s); } return s; }
  function center(x, text, y) { x.textAlign = "center"; x.fillText(text, 540, y); x.textAlign = "left"; }
  function brand(x, y, L) {
    x.font = FR(500, Math.round(L * 0.46)); const txt = "Megève par cœur", tw = x.measureText(txt).width, gap = 18;
    const w = (logo ? L + gap : 0) + tw, x0 = 540 - w / 2;
    if (logo) x.drawImage(logo, x0, y, L, L);
    x.fillStyle = "#fbf3e6"; x.textBaseline = "middle"; x.fillText(txt, x0 + (logo ? L + gap : 0), y + L / 2); x.textBaseline = "alphabetic";
  }
  const today = () => { const s = new Date().toLocaleDateString(LOC, { weekday: "long", day: "numeric", month: "long" }); return s.charAt(0).toUpperCase() + s.slice(1); };
  const deg = t => `${Math.round(t)}°`.replace("-", "−");

  // ---- météo
  function next24(d) {
    const H = d.hourly, now = d.current.time.slice(0, 13);
    let i = H.time.findIndex(t => t.slice(0, 13) === now); if (i < 0) i = 0;
    const TT = H.temperature_2m || [], CC = H.weather_code || [];
    let mn = Infinity, mx = -Infinity, sn = 0; const all = {}, wet = {};
    for (let k = i + 1; k <= i + 24 && k < H.time.length; k++) {
      if (TT[k] != null) { mn = Math.min(mn, TT[k]); mx = Math.max(mx, TT[k]); }
      sn += H.snowfall[k] || 0;
      const c = CC[k]; if (c == null) continue;
      all[c] = (all[c] || 0) + 1; if (c >= 51) wet[c] = (wet[c] || 0) + 1;
    }
    const top = o => Object.keys(o).sort((a, b) => o[b] - o[a] || b - a)[0];
    const wetH = Object.values(wet).reduce((a, b) => a + b, 0);
    const code = wetH >= 3 ? +top(wet) : (top(all) != null ? +top(all) : d.current.weather_code);
    return { mn: isFinite(mn) ? mn : null, mx: isFinite(mx) ? mx : null, sn, code };
  }
  function card(x, X, Y, W, H, v, s, n, zone, wc) {
    const k = H / 240, Yk = a => Y + a * k;
    x.fillStyle = "#fff"; rr(x, X, Y, W, H, 28); x.fill();
    // village + maintenant
    const ax = X + 38;
    x.fillStyle = INK; fit(x, v.n, 290, z => FR(600, z), 48); x.fillText(v.n, ax, Yk(64));
    x.fillStyle = MUTED; x.font = NU(700, 22);
    x.fillText(`${zone === "v" ? T.vil : T.alti} · ${(zone === "v" ? v.v : v.a).toLocaleString(LOC)} m`, ax, Yk(98));
    const [ic] = wc(s.cur.weather_code);
    x.font = EMO(60); x.fillText(ic, ax, Yk(196));
    x.fillStyle = INK; x.font = FR(600, 70); x.fillText(deg(s.cur.temperature_2m), ax + 84, Yk(196));
    x.fillStyle = MUTED; x.font = NU(800, 17); x.fillText(T.now.toUpperCase(), ax + 88, Yk(218));
    // 24 h à venir
    const bx = X + 345, bw = 290;
    x.fillStyle = MUTED; x.font = NU(800, 19); x.fillText(T.h24.toUpperCase(), bx, Yk(56));
    const [ic2, lb2] = wc(n.code);
    x.font = EMO(52); x.fillText(ic2, bx, Yk(126));
    x.fillStyle = INK; x.font = NU(800, 38);
    x.fillText(n.mn != null ? `${deg(n.mn)} / ${deg(n.mx)}` : "—", bx + 70, Yk(122));
    fit(x, lb2, bw, z => NU(700, z), 25); x.fillText(lb2, bx, Yk(166));
    if (n.sn >= 0.5) { x.fillStyle = BLUE; fit(x, T.snow24(Math.round(n.sn)), bw, z => NU(800, z), 25); x.fillText(T.snow24(Math.round(n.sn)), bx, Yk(204)); }
    // neige au sol / prévue 7 j
    const cw = 244, cx = X + W - 30 - cw, pad = 22 * k, gap = 12 * k, ch = (H - 2 * pad - gap) / 2;
    const box = (yy, bg, fg, lab, val) => {
      x.fillStyle = bg; rr(x, cx, yy, cw, ch, 18); x.fill();
      x.fillStyle = fg; x.globalAlpha = .8; x.font = NU(800, 18); x.fillText(lab.toUpperCase(), cx + 20, yy + 32 * k); x.globalAlpha = 1;
      x.font = NU(800, 42); x.fillText(val, cx + 20, yy + ch - 18 * k);
    };
    box(Y + pad, "#eef2f8", INK, T.sol, `${Math.round(s.depth)} cm`);
    box(Y + pad + ch + gap, BLUE, "#fff", T.prev, `+${Math.round(s.week)} cm`);
  }
  async function drawMeteo(f) {
    const M = window.mpcMeteo && window.mpcMeteo();
    if (!M) throw new Error("page");
    const data = M.data || await M.load(M.zone);
    await ready();
    const story = f === "story", H = story ? 1920 : 1350, [c, x] = canvas(H);
    const S = data.map(M.summarize), N = data.map(next24);
    brand(x, story ? 168 : 56, story ? 80 : 64);
    x.fillStyle = "#fff"; x.font = FR(600, story ? 86 : 70); center(x, T.mTitle, story ? 352 : 212);
    x.fillStyle = ICE; x.font = NU(700, story ? 34 : 28);
    center(x, `${today()} · ${M.zone === "v" ? T.village : T.alt}`, story ? 408 : 256);
    let y0 = story ? 456 : 290;
    if (story) { // la phrase du moment (« De la neige attendue demain »…), comme sur la page
      const a = document.getElementById("aT"), t = a && a.textContent.trim();
      if (t) {
        x.font = NU(800, 32); const tw = Math.min(900, x.measureText(t).width) + 64;
        x.fillStyle = RED; rr(x, 540 - tw / 2, y0, tw, 64, 32); x.fill();
        x.fillStyle = "#fff"; fit(x, t, 900, z => NU(800, z), 32); x.textBaseline = "middle"; center(x, t, y0 + 33); x.textBaseline = "alphabetic";
      }
      y0 += 92;
    }
    const ch = story ? 240 : 232, gap = story ? 22 : 14;
    M.V.forEach((v, i) => card(x, 60, y0 + i * (ch + gap), 960, ch, v, S[i], N[i], M.zone, M.wc));
    const yb = y0 + 4 * ch + 3 * gap;
    x.fillStyle = ICE; x.font = NU(600, story ? 24 : 20); center(x, T.mSrc, yb + (story ? 62 : 32));
    x.fillStyle = "#fff"; x.font = NU(800, story ? 36 : 28); center(x, T.mUrl, yb + (story ? 112 : 64));
    return { canvas: c };
  }

  // ---- webcams
  const shots = new Map();
  function getCam(id) {
    if (!shots.has(id)) shots.set(id, fetch("/api/webcam?c=" + encodeURIComponent(id))
      .then(r => { if (!r.ok) throw new Error(r.status); return r.blob().then(b => ({ b, t: r.headers.get("X-Shot") })); })
      .then(({ b, t }) => new Promise((ok, ko) => { const i = new Image(); i.onload = () => ok({ img: i, t }); i.onerror = ko; i.src = URL.createObjectURL(b); }))
      .catch(e => { shots.delete(id); throw e; }));
    return shots.get(id);
  }
  async function drawCams() {
    const ids = [...dlg.querySelectorAll(".ig-cams input:checked")].map(i => i.value);
    if (!ids.length) throw Object.assign(new Error("none"), { userMsg: T.none });
    const [res] = await Promise.all([Promise.allSettled(ids.map(getCam)), ready()]);
    const ok = ids.map((id, i) => ({ cam: LIST.find(c => c.id === id), r: res[i] })).filter(o => o.r.status === "fulfilled").map(o => ({ cam: o.cam, ...o.r.value }));
    if (!ok.length) throw new Error("webcams");
    const [c, x] = canvas(1920);
    brand(x, 150, 76);
    x.fillStyle = "#fff"; x.font = FR(600, 74); center(x, T.cTitle, 318);
    const last = ok.map(o => o.t).filter(Boolean).sort().pop();
    const hr = last ? new Date(last + ":00").toLocaleTimeString(LOC, { hour: "2-digit", minute: "2-digit" }) : new Date().toLocaleTimeString(LOC, { hour: "2-digit", minute: "2-digit" });
    x.fillStyle = ICE; x.font = NU(700, 32); center(x, `${today()} · ${hr}`, 372);
    const top = 412, bottom = 1630, gap = 16, n = ok.length;
    const h = Math.min(560, (bottom - top - gap * (n - 1)) / n), y0 = top + ((bottom - top) - (h * n + gap * (n - 1))) / 2;
    ok.forEach((o, i) => {
      const X = 40, W = 1000, Y = y0 + i * (h + gap), im = o.img;
      x.save(); rr(x, X, Y, W, h, 24); x.clip();
      const s = Math.max(W / im.naturalWidth, h / im.naturalHeight), dw = im.naturalWidth * s, dh = im.naturalHeight * s;
      x.drawImage(im, X + (W - dw) / 2, Y + (h - dh) / 2, dw, dh);
      const g = x.createLinearGradient(0, Y + h * 0.45, 0, Y + h); g.addColorStop(0, "rgba(5,12,24,0)"); g.addColorStop(1, "rgba(5,12,24,.78)");
      x.fillStyle = g; x.fillRect(X, Y, W, h);
      x.restore();
      const fs = Math.max(26, Math.min(40, h * 0.17)), by = Y + h - fs * 0.7;
      x.fillStyle = "#fff"; x.font = NU(800, fs); x.shadowColor = "rgba(0,0,0,.5)"; x.shadowBlur = 8;
      x.fillText(o.cam.t, X + 26, by); const tw = x.measureText(o.cam.t).width; x.shadowBlur = 0;
      if (o.cam.t.indexOf(o.cam.v) < 0) { // pastille du village
        x.font = NU(800, fs * 0.5); const pw = x.measureText(o.cam.v.toUpperCase()).width + 24, ph = fs * 0.85;
        x.fillStyle = o.cam.c; rr(x, X + 40 + tw, by - ph * 0.78, pw, ph, ph / 2); x.fill();
        x.fillStyle = "#fff"; x.fillText(o.cam.v.toUpperCase(), X + 52 + tw, by - ph * 0.78 + ph * 0.68);
      }
      if (o.t) {
        const tt = new Date(o.t + ":00").toLocaleTimeString(LOC, { hour: "2-digit", minute: "2-digit" });
        x.font = NU(800, 22); const pw = x.measureText(tt).width + 28;
        x.fillStyle = "rgba(10,20,36,.72)"; rr(x, X + W - 18 - pw, Y + 16, pw, 38, 19); x.fill();
        x.fillStyle = "#fff"; x.fillText(tt, X + W - 18 - pw + 14, Y + 43);
      }
    });
    x.fillStyle = ICE; x.font = NU(600, 24); center(x, T.cSrc, 1680);
    x.fillStyle = "#fff"; x.font = NU(800, 36); center(x, T.cUrl, 1730);
    const miss = ids.length - ok.length;
    return { canvas: c, note: miss ? T.miss(miss) : "" };
  }
})();
