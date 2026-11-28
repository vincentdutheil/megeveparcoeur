// Bouton « Partager ce tableau en Reel » (page Météo & neige, réservé à Vincent).
// Visible seulement dans un navigateur connecté à l'admin (clé GitHub enregistrée par /admin/, « mpc_tok »).
// 1. Le Reel (1080×1920, 15 s, 30 i/s) est fabriqué dans le navigateur : neige qui tombe sur les sapins,
//    le classement « La neige cette semaine » (données /api/neige) qui apparaît station par station,
//    et la chanson d'Akhilleus « Megève c'est le rêve » (extrait déjà encodé en AAC : /sons/reel-neige.aac).
//    Encodage H.264 avec WebCodecs + mp4-muxer (MP4 « faststart », comme le demande Instagram).
// 2. « Publier sur Instagram » : la vidéo, sa couverture et instagram/reels/<clé>.json (légende, 7 comptes
//    identifiés, lieu Megève) sont envoyés dans le dépôt avec la clé GitHub de l'admin ; une fois le site
//    redéployé, /api/reel?key=<clé> publie le Reel sur @megeveparcoeur (comme les reels webcams).
// Autres choix : « Partager… » (feuille de partage du téléphone) ou « Télécharger ».
(function () {
  if (!/\/meteo\//.test(location.pathname) || document.documentElement.lang === "en") return;
  const get = k => { try { return localStorage.getItem(k); } catch (_) { return null; } };
  const put = (k, v) => { try { v == null ? localStorage.removeItem(k) : localStorage.setItem(k, v); } catch (_) {} };
  const TOK = get("mpc_tok");
  if (!TOK) return;

  const OWNER = "vincentdutheil", REPO = "megeveparcoeur", BRANCH = "main", SITE = "https://www.megeveparcoeur.fr";
  const HOME = ["Megève", "Combloux", "Demi-Quartier", "Praz-sur-Arly"];
  const TAGS = ["megeve_officiel", "skimegeve", "megeve_afterski", "lepalaismegeve", "comblouxtourisme", "esfcombloux", "comblouxparcoeur"];
  const LOCATION = "24274852196"; // Megève (instagram/lieu-megeve.json)
  const W = 1080, H = 1920, FPS = 30, DUR = 15, NF = FPS * DUR;

  // ------------------------------------------------------------------ interface
  const css = `
.rn-btn{display:inline-flex;align-items:center;gap:8px;margin-top:14px;font:800 .95rem var(--body);color:#fff;border:0;border-radius:999px;padding:11px 18px;cursor:pointer;
  background:linear-gradient(45deg,#f09433,#e6683c 25%,#dc2743 50%,#cc2366 75%,#bc1888);box-shadow:0 10px 24px rgba(188,24,136,.25)}
.rn-btn:hover{filter:brightness(1.07)}
.rn-dlg{border:0;border-radius:24px;padding:0;width:min(460px,94vw);max-height:94vh;background:var(--card);color:var(--ink);box-shadow:0 30px 80px rgba(0,0,0,.45)}
.rn-dlg::backdrop{background:rgba(5,12,24,.7)}
.rn-in{padding:16px 16px 18px;display:flex;flex-direction:column;gap:10px}
.rn-hd{display:flex;justify-content:space-between;align-items:center;gap:10px}.rn-hd b{font-family:var(--display);font-size:1.25rem;font-weight:600}
.rn-x{border:0;background:transparent;color:var(--ink);font-size:1.6rem;line-height:1;cursor:pointer;padding:4px 8px}
.rn-pv{display:flex;justify-content:center;background:#0a1424;border-radius:16px;overflow:hidden}
.rn-pv canvas,.rn-pv video{display:block;height:46vh;max-height:520px;width:auto;max-width:100%;aspect-ratio:9/16}
.rn-st{margin:0;font-weight:800;font-size:.9rem;text-align:center}.rn-st.err{color:var(--heart)}
.rn-bar{height:6px;border-radius:6px;background:var(--wool);overflow:hidden}.rn-bar i{display:block;height:100%;width:0;background:linear-gradient(90deg,#dc2743,#bc1888)}
.rn-cap{width:100%;min-height:150px;font:500 .85rem/1.4 var(--body);border:1.5px solid var(--line);border-radius:12px;padding:9px;background:transparent;color:var(--ink);resize:vertical}
.rn-meta{margin:0;color:var(--muted);font-size:.78rem;line-height:1.4}
.rn-act{display:flex;gap:8px;flex-wrap:wrap}.rn-act button{flex:1 1 130px;font:800 .9rem var(--body);border-radius:999px;padding:11px 12px;cursor:pointer}
.rn-act .go{border:0;color:#fff;background:linear-gradient(45deg,#f09433,#dc2743 50%,#bc1888)}
.rn-act .sec{border:1.5px solid var(--line);background:transparent;color:var(--ink)}
.rn-act button:disabled{opacity:.45;cursor:default}
@media(max-width:560px){.rn-pv canvas,.rn-pv video{height:38vh}}`;
  const st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);

  const btn = document.createElement("button");
  btn.type = "button"; btn.className = "rn-btn"; btn.innerHTML = "🎬 Partager ce tableau en Reel";
  const place = () => { const cl = document.getElementById("classement"); if (!cl || cl.hidden || btn.isConnected) return !!btn.isConnected; cl.appendChild(btn); return true; };
  if (!place()) { const cl = document.getElementById("classement"); if (cl) new MutationObserver((m, o) => { if (place()) o.disconnect(); }).observe(cl, { attributes: true, childList: true }); }

  const dlg = document.createElement("dialog"); dlg.className = "rn-dlg"; dlg.setAttribute("aria-label", "Reel La neige cette semaine");
  dlg.innerHTML = `<div class="rn-in">
    <div class="rn-hd"><b>Reel « La neige cette semaine »</b><button type="button" class="rn-x" aria-label="Fermer">×</button></div>
    <div class="rn-pv"></div>
    <div class="rn-bar"><i></i></div>
    <p class="rn-st" aria-live="polite"></p>
    <textarea class="rn-cap" aria-label="Légende du Reel" hidden></textarea>
    <p class="rn-meta">🎵 Megève c'est le rêve – Akhilleus · 📍 Megève<br>Identifiés : ${TAGS.map(t => "@" + t).join(" ")}</p>
    <div class="rn-act"><button type="button" class="go" disabled>Publier sur Instagram</button><button type="button" class="sec sh" hidden disabled>Partager…</button><button type="button" class="sec dl" disabled>Télécharger</button></div>
  </div>`;
  document.body.appendChild(dlg);
  const q = s => dlg.querySelector(s), pv = q(".rn-pv"), bar = q(".rn-bar i"), stx = q(".rn-st"), cap = q(".rn-cap");
  const bGo = q(".go"), bSh = q(".sh"), bDl = q(".dl");
  const status = (t, err) => { stx.textContent = t; stx.className = "rn-st" + (err ? " err" : ""); };
  const prog = f => { bar.style.width = Math.round(f * 100) + "%"; };
  let made = null, busy = false; // made = { mp4: Blob, cover: Blob, key, data }

  q(".rn-x").onclick = () => dlg.close();
  dlg.addEventListener("cancel", e => { if (busy) e.preventDefault(); });
  btn.onclick = () => {
    if (dlg.showModal) dlg.showModal(); else dlg.setAttribute("open", "");
    const pending = get("mpc_reel_neige");
    if (pending && !made) { status("Une publication était en cours (" + pending + ") : reprise…"); publishStep(pending); return; }
    if (!made && !busy) build();
  };

  // ------------------------------------------------------------------ outils
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const pad = n => String(n).padStart(2, "0");
  const dd = s => new Date(s + "T12:00:00");
  const dLong = s => dd(s).toLocaleDateString("fr-FR", { day: "numeric", month: "long" });
  const jour = s => dd(s).toLocaleDateString("fr-FR", { weekday: "long" });
  const ease = t => t <= 0 ? 0 : t >= 1 ? 1 : 1 - Math.pow(1 - t, 3);
  const FR = (w, s) => `${w} ${s}px Fraunces, Georgia, serif`;
  const NU = (w, s) => `${w} ${s}px "Nunito Sans", system-ui, -apple-system, "Segoe UI", sans-serif`;
  function rr(x, X, Y, w, h, r) { x.beginPath(); if (x.roundRect) x.roundRect(X, Y, w, h, r); else x.rect(X, Y, w, h); }
  function fitText(x, t, maxW, font, size) { let s = size; x.font = font(s); while (s > 14 && x.measureText(t).width > maxW) { s -= 1; x.font = font(s); } }
  function rand(seed) { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }
  function loadScript(src) { return new Promise(ok => { if (typeof Mp4Muxer !== "undefined") return ok(); const e = document.createElement("script"); e.src = src; e.onload = e.onerror = () => ok(); document.head.appendChild(e); }); }
  function loadImg(src) { return new Promise(ok => { const i = new Image(); i.onload = () => ok(i); i.onerror = () => ok(null); i.src = src; }); }

  // ------------------------------------------------------------------ décor : sapins enneigés (dessiné une fois)
  function drawFir(x, cx, base, h, col, rnd) {
    const w = h * 0.52, tiers = 5, th = h / (tiers + 0.6);
    x.fillStyle = "#3a2a22"; x.fillRect(cx - h * 0.03, base - th * 0.6, h * 0.06, th * 0.6);
    for (let k = 0; k < tiers; k++) {
      const top = base - h + k * th * 0.82, bot = top + th * 1.35, half = (w / 2) * (0.35 + 0.65 * (k + 1) / tiers);
      x.fillStyle = col; x.beginPath(); x.moveTo(cx, top); x.lineTo(cx + half, bot); x.lineTo(cx - half, bot); x.closePath(); x.fill();
      // neige posée sur l'étage : une calotte en haut et un liseré festonné sur le bord inférieur
      x.fillStyle = "rgba(240,246,255,.96)";
      const ch = (bot - top) * 0.28, chw = half * 0.28;
      x.beginPath(); x.moveTo(cx, top); x.lineTo(cx + chw, top + ch); x.quadraticCurveTo(cx, top + ch * 0.7, cx - chw, top + ch); x.closePath(); x.fill();
      x.beginPath(); x.moveTo(cx - half, bot); x.lineTo(cx + half, bot);
      const n = 4 + Math.floor(rnd() * 3), bh = th * 0.13;
      for (let i = n; i > 0; i--) { const x1 = cx - half + (2 * half) * (i - 1) / n, xm = (x1 + cx - half + (2 * half) * i / n) / 2; x.quadraticCurveTo(xm, bot - bh * (1.6 + rnd()), x1, bot - bh * 0.4); }
      x.closePath(); x.fill();
    }
  }
  function scene() {
    const c = document.createElement("canvas"); c.width = W; c.height = H; const x = c.getContext("2d");
    const g = x.createLinearGradient(0, 0, 0, H); g.addColorStop(0, "#081326"); g.addColorStop(0.55, "#132a52"); g.addColorStop(1, "#28497d");
    x.fillStyle = g; x.fillRect(0, 0, W, H);
    const r = rand(7);
    x.fillStyle = "#fff"; for (let i = 0; i < 90; i++) { x.globalAlpha = 0.15 + r() * 0.45; x.beginPath(); x.arc(r() * W, r() * 900, 0.6 + r() * 1.4, 0, 6.283); x.fill(); }
    x.globalAlpha = 1;
    // montagnes enneigées au loin
    x.fillStyle = "#c9d8ee"; x.beginPath(); x.moveTo(0, 1500);
    [[90, 1420], [220, 1460], [380, 1350], [470, 1400], [600, 1300], [700, 1370], [820, 1330], [960, 1410], [1080, 1380]].forEach(([a, b]) => x.lineTo(a, b));
    x.lineTo(1080, 1600); x.lineTo(0, 1600); x.closePath(); x.fill();
    x.fillStyle = "#8fa6c8"; x.beginPath(); x.moveTo(0, 1560); x.quadraticCurveTo(300, 1470, 560, 1540); x.quadraticCurveTo(820, 1600, 1080, 1520); x.lineTo(1080, 1650); x.lineTo(0, 1650); x.fill();
    // trois rangées de sapins (lointaine → proche)
    const rows = [
      { y: 1660, h: [150, 230], col: "#2b5652", n: 14 },
      { y: 1790, h: [230, 330], col: "#1f473d", n: 10 },
      { y: 1970, h: [380, 520], col: "#163a30", n: 7 },
    ];
    rows.forEach((L, li) => {
      // sol enneigé de la rangée
      x.fillStyle = li === 0 ? "#dfe9f7" : li === 1 ? "#edf3fb" : "#f7faff";
      x.beginPath(); x.moveTo(0, L.y - 30); x.quadraticCurveTo(W / 2, L.y - 70 + li * 10, W, L.y - 30); x.lineTo(W, H); x.lineTo(0, H); x.fill();
      for (let i = 0; i < L.n; i++) {
        let cx = (i + 0.2 + r() * 0.6) * (W / L.n);
        if (li === 2) cx = [-40, 120, 260, 820, 960, 1110, 560][i];
        drawFir(x, cx, L.y + r() * 30, L.h[0] + r() * (L.h[1] - L.h[0]), L.col, r);
      }
    });
    // voile sombre derrière le tableau pour la lisibilité
    const v = x.createLinearGradient(0, 0, 0, H); v.addColorStop(0, "rgba(6,14,30,.35)"); v.addColorStop(0.75, "rgba(6,14,30,.25)"); v.addColorStop(0.85, "rgba(6,14,30,0)");
    x.fillStyle = v; x.fillRect(0, 0, W, H);
    return c;
  }
  function flakes() {
    const r = rand(42), L = [];
    for (let i = 0; i < 260; i++) { const z = r(); L.push({ x: r() * W, y: r() * H, z, r: 1.2 + z * z * 6, s: 40 + z * 170, a: 0.35 + z * 0.6, ph: r() * 6.283, sw: 10 + r() * 30 }); }
    return L;
  }
  function snow(x, L, t, front) {
    x.fillStyle = "#fff";
    for (const f of L) {
      if ((f.z > 0.78) !== front) continue;
      const y = (f.y + f.s * t) % (H + 40) - 20, X = (f.x + Math.sin(f.ph + t * 1.3) * f.sw + t * 12 * f.z + W) % W;
      x.globalAlpha = f.a * (front ? 0.85 : 1); x.beginPath(); x.arc(X, y, f.r, 0, 6.283); x.fill();
    }
    x.globalAlpha = 1;
  }

  // ------------------------------------------------------------------ une image du Reel à l'instant t
  function frame(x, t, A) {
    const { bg, fl, logo, data } = A, S = data.stations.slice().sort((a, b) => b.prevu - a.prevu).slice(0, 13), n = S.length;
    x.drawImage(bg, 0, 0);
    snow(x, fl, t, false);
    // en-tête
    const a0 = ease((t - 0.15) / 0.8);
    x.globalAlpha = a0; x.textBaseline = "alphabetic";
    x.font = FR(500, 34); const bt = "Megève par cœur", bw = x.measureText(bt).width, L = 70, bx = 540 - (L + 16 + bw) / 2;
    if (logo) x.drawImage(logo, bx, 150, L, L);
    x.fillStyle = "#fbf3e6"; x.textBaseline = "middle"; x.fillText(bt, bx + L + 16, 150 + L / 2); x.textBaseline = "alphabetic";
    x.fillStyle = "#fff"; x.textAlign = "center"; x.font = FR(600, 80); x.fillText("La neige cette semaine", 540, 318 + (1 - a0) * 20);
    x.fillStyle = "#bcd3f2"; x.font = NU(700, 32); x.fillText(`du ${dLong(data.du)} au ${dLong(data.au)} · station par station`, 540, 372);
    x.font = NU(800, 22); x.fillStyle = "#e6eefb";
    x.fillText("AU SOL", 70 + 940 - 190 - 12 - 95 - 14, 438); x.fillText("PRÉVU 7 J", 70 + 940 - 95 - 14, 438);
    x.textAlign = "left"; x.globalAlpha = 1;
    // lignes : de la dernière à la première (suspense)
    const RH = 62, GAP = 9, Y0 = 458, start = 1.1, step = 0.3;
    S.forEach((s, i) => {
      const t0 = start + (n - 1 - i) * step, p = ease((t - t0) / 0.4);
      if (p <= 0) return;
      const home = HOME.includes(s.nom), Y = Y0 + i * (RH + GAP), X = 70 + (1 - p) * 120, w = 940;
      x.globalAlpha = p;
      x.shadowColor = "rgba(0,0,0,.28)"; x.shadowBlur = 16; x.shadowOffsetY = 6;
      x.fillStyle = home ? "#c8323d" : "rgba(255,255,255,.96)"; rr(x, X, Y, w, RH, 16); x.fill();
      x.shadowColor = "transparent"; x.shadowBlur = 0; x.shadowOffsetY = 0;
      const bW = 190, bP = X + w - 12 - bW, bS = bP - 14 - bW;
      x.fillStyle = home ? "rgba(255,255,255,.22)" : "#eef2f8"; rr(x, bS, Y + 8, bW, RH - 16, 12); x.fill();
      x.fillStyle = home ? "#fff" : "#1f4f9a"; rr(x, bP, Y + 8, bW, RH - 16, 12); x.fill();
      x.textBaseline = "middle";
      x.fillStyle = home ? "rgba(255,255,255,.7)" : "rgba(12,26,52,.5)"; x.font = NU(700, 32); const k = (i + 1) + ".";
      x.fillText(k, X + 22, Y + RH / 2 + 1); const kw = x.measureText(k + " ").width;
      x.fillStyle = home ? "#fff" : "#0c1a34"; fitText(x, s.nom, bS - (X + 22 + kw) - 14, z => NU(800, z), 33); x.fillText(s.nom, X + 22 + kw, Y + RH / 2 + 1);
      x.textAlign = "center"; x.font = NU(800, 32);
      x.fillStyle = home ? "#fff" : "#55657e"; x.fillText(`${s.sol} cm`, bS + bW / 2, Y + RH / 2 + 1);
      const cnt = Math.round(s.prevu * ease((t - t0) / 0.9));
      x.fillStyle = home ? "#c8323d" : "#fff"; x.fillText(`+${cnt} cm`, bP + bW / 2, Y + RH / 2 + 1);
      x.textAlign = "left"; x.textBaseline = "alphabetic"; x.globalAlpha = 1;
    });
    // pied
    const yb = Y0 + n * (RH + GAP) + 26, a1 = ease((t - (start + n * step + 0.3)) / 0.6);
    x.globalAlpha = a1; x.textAlign = "center";
    x.fillStyle = "rgba(8,19,38,.78)"; rr(x, 90, yb - 22, 900, 108, 24); x.fill();
    x.fillStyle = "#e6eefb"; x.font = NU(700, 25); x.fillText("Nos 4 villages en rouge · prévisions Open-Meteo, susceptibles d'évoluer", 540, yb + 10);
    x.fillStyle = "#fff"; x.font = NU(800, 40); x.fillText("megeveparcoeur.fr/meteo", 540, yb + 62);
    x.textAlign = "left"; x.globalAlpha = 1;
    snow(x, fl, t, true);
  }

  // ------------------------------------------------------------------ musique (AAC déjà encodé, découpé en trames ADTS)
  async function music() {
    const r = await fetch("/sons/reel-neige.aac"); if (!r.ok) throw new Error("musique " + r.status);
    const b = new Uint8Array(await r.arrayBuffer()), out = []; let i = 0, cfg = null;
    const RATES = [96000, 88200, 64000, 48000, 44100, 32000, 24000, 22050, 16000, 12000, 11025, 8000, 7350];
    while (i + 7 <= b.length) {
      if (b[i] !== 0xff || (b[i + 1] & 0xf6) !== 0xf0) { i++; continue; }
      const prot = b[i + 1] & 1, obj = ((b[i + 2] >> 6) & 3) + 1, fi = (b[i + 2] >> 2) & 15, ch = ((b[i + 2] & 1) << 2) | (b[i + 3] >> 6);
      const len = ((b[i + 3] & 3) << 11) | (b[i + 4] << 3) | (b[i + 5] >> 5), hl = prot ? 7 : 9;
      if (len < hl || i + len > b.length) break;
      if (!cfg) cfg = { sampleRate: RATES[fi], numberOfChannels: ch, asc: new Uint8Array([(obj << 3) | (fi >> 1), ((fi & 1) << 7) | (ch << 3)]) };
      out.push(b.slice(i + hl, i + len)); i += len;
    }
    if (!cfg || !out.length) throw new Error("musique illisible");
    return { ...cfg, frames: out };
  }

  // ------------------------------------------------------------------ fabrication du MP4
  async function pickCodec() {
    if (typeof VideoEncoder === "undefined") return null;
    for (const codec of ["avc1.640028", "avc1.4d0028", "avc1.42003e", "avc1.420034"]) {
      const c = { codec, width: W, height: H, bitrate: 7_000_000, framerate: FPS, avc: { format: "avc" } };
      try { if ((await VideoEncoder.isConfigSupported(c)).supported) return c; } catch (_) {}
    }
    return null;
  }
  async function build() {
    busy = true; made = null; bGo.disabled = bSh.disabled = bDl.disabled = true; cap.hidden = true; prog(0);
    try {
      status("Chargement des données…");
      const [data, logo, mus, vcfg] = await Promise.all([
        fetch("/api/neige").then(r => r.json()), loadImg("/img/logo-rond.png"), music(), pickCodec(), loadScript("/assets/mp4-muxer.min.js"),
        document.fonts ? Promise.all([document.fonts.load(FR(600, 80)), document.fonts.load(FR(500, 34)), document.fonts.load(NU(800, 32)), document.fonts.load(NU(700, 32))]) : null,
      ]);
      if (!data || !data.stations) throw new Error("prévisions indisponibles");
      if (!vcfg || typeof Mp4Muxer === "undefined") throw Object.assign(new Error("codec"), { msg: "Ce navigateur ne sait pas fabriquer de vidéo MP4. Ouvrez la page dans Chrome (Android) ou Safari récent." });
      const A = { bg: scene(), fl: flakes(), logo, data };
      const c = document.createElement("canvas"); c.width = W; c.height = H; const x = c.getContext("2d");
      pv.innerHTML = ""; pv.appendChild(c);
      const muxer = new Mp4Muxer.Muxer({
        target: new Mp4Muxer.ArrayBufferTarget(), fastStart: "in-memory", firstTimestampBehavior: "offset",
        video: { codec: "avc", width: W, height: H, frameRate: FPS },
        audio: { codec: "aac", numberOfChannels: mus.numberOfChannels, sampleRate: mus.sampleRate },
      });
      let encErr = null;
      const enc = new VideoEncoder({ output: (ch, meta) => muxer.addVideoChunk(ch, meta), error: e => { encErr = e; } });
      enc.configure(vcfg);
      let cover = null;
      for (let f = 0; f < NF; f++) {
        if (encErr) throw encErr;
        const t = f / FPS; frame(x, t, A);
        const vf = new VideoFrame(c, { timestamp: Math.round(f * 1e6 / FPS), duration: Math.round(1e6 / FPS) });
        enc.encode(vf, { keyFrame: f % (FPS * 2) === 0 }); vf.close();
        if (f === FPS * 12) cover = await new Promise(ok => c.toBlob(ok, "image/jpeg", 0.9));
        if (f % 5 === 0) { prog(f / NF); status(`Fabrication du Reel… ${Math.round(f / NF * 100)} %`); }
        while (enc.encodeQueueSize > 3) await sleep(5);
        if (f % 10 === 0) await sleep(0);
      }
      await enc.flush(); enc.close();
      if (encErr) throw encErr;
      // musique : trames AAC de 1024 échantillons, jusqu'à la fin de la vidéo
      const fd = 1024 / mus.sampleRate;
      const meta = { decoderConfig: { codec: "mp4a.40.2", numberOfChannels: mus.numberOfChannels, sampleRate: mus.sampleRate, description: mus.asc } };
      for (let k = 0; k < mus.frames.length && k * fd < DUR; k++)
        muxer.addAudioChunkRaw(mus.frames[k], "key", Math.round(k * fd * 1e6), Math.round(fd * 1e6), k === 0 ? meta : undefined);
      muxer.finalize();
      const mp4 = new Blob([muxer.target.buffer], { type: "video/mp4" });
      const now = new Date(), day = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
      const key = `neige-${day}-${pad(now.getHours())}${pad(now.getMinutes())}`;
      made = { mp4, cover, key, data };
      pv.innerHTML = ""; const v = document.createElement("video");
      v.src = URL.createObjectURL(mp4); if (cover) v.poster = URL.createObjectURL(cover); v.controls = true; v.playsInline = true; v.loop = true; pv.appendChild(v);
      cap.value = caption(data); cap.hidden = false; prog(1);
      status(`Reel prêt (${(mp4.size / 1e6).toFixed(1)} Mo). Vérifiez-le, puis publiez.`);
      bGo.disabled = bDl.disabled = false;
      try { const fl = new File([mp4], key + ".mp4", { type: "video/mp4" }); if (navigator.canShare && navigator.canShare({ files: [fl] })) { bSh.hidden = false; bSh.disabled = false; } } catch (_) {}
    } catch (e) {
      status(e.msg || "Le Reel n'a pas pu être fabriqué : " + (e.message || e), true);
    } finally { busy = false; }
  }

  // ------------------------------------------------------------------ légende
  function caption(d) {
    const V = HOME.map(n => d.stations.find(s => s.nom === n)).filter(Boolean).sort((a, b) => b.prevu - a.prevu);
    const any = V.some(s => s.prevu > 0), L = ["❄️ La neige cette semaine, station par station", ""];
    if (any) {
      V.forEach(s => L.push(`• ${s.nom} : +${s.prevu} cm attendus d'ici le ${dLong(d.au)} (${s.sol} cm au sol)`));
      const m = d.stations.find(s => s.nom === "Megève"), best = m && m.jours && m.jours.slice().sort((a, b) => b.neige - a.neige)[0];
      if (best && best.neige >= 2) L.push("", `Le plus gros des chutes à Megève : ${jour(best.date)} (environ ${Math.round(best.neige)} cm).`);
      L.push("Ce sont des prévisions : elles peuvent encore évoluer.", "", "Vous montez quand ? ⛷️");
    } else {
      V.forEach(s => L.push(`• ${s.nom} : ${s.sol} cm au sol`));
      L.push("", `Pas de nouvelle neige annoncée d'ici le ${dLong(d.au)}… on croise les doigts pour la suite ! 🤞`, "", "Et vous, vous montez quand ? ⛷️");
    }
    L.push("", "🎵 Megève c'est le rêve – Akhilleus", "👉 Le classement mis à jour en continu sur megeveparcoeur.fr/meteo (lien en bio)",
      "📍 Megève · Combloux · Demi-Quartier · Praz-sur-Arly", "", "#megeve #combloux #prazsurarly #demiquartier #neige #ski #poudreuse #hautesavoie #montblanc #alpes");
    return L.join("\n");
  }

  // ------------------------------------------------------------------ envoi dans le dépôt puis publication
  async function gh(path, opt = {}) {
    const r = await fetch(`https://api.github.com/repos/${OWNER}/${REPO}${path}`, { ...opt, headers: { Authorization: "Bearer " + TOK, Accept: "application/vnd.github+json", ...(opt.body ? { "Content-Type": "application/json" } : {}) } });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) throw Object.assign(new Error((j && j.message) || "GitHub " + r.status), { status: r.status });
    return j;
  }
  const b64 = blob => new Promise((ok, ko) => { const f = new FileReader(); f.onload = () => ok(String(f.result).split(",")[1]); f.onerror = ko; f.readAsDataURL(blob); });
  async function commit(files, message) {
    const blobs = [];
    for (const [path, blob] of files) { status("Envoi de " + path.split("/").pop() + "…"); blobs.push({ path, mode: "100644", type: "blob", sha: (await gh("/git/blobs", { method: "POST", body: JSON.stringify({ content: await b64(blob), encoding: "base64" }) })).sha }); }
    for (let k = 0; k < 4; k++) {
      const ref = await gh(`/git/ref/heads/${BRANCH}`), head = ref.object.sha, base = (await gh(`/git/commits/${head}`)).tree.sha;
      const tree = await gh("/git/trees", { method: "POST", body: JSON.stringify({ base_tree: base, tree: blobs }) });
      const c = await gh("/git/commits", { method: "POST", body: JSON.stringify({ message, tree: tree.sha, parents: [head] }) });
      try { await gh(`/git/refs/heads/${BRANCH}`, { method: "PATCH", body: JSON.stringify({ sha: c.sha }) }); return c.sha; }
      catch (e) { if (e.status !== 422) throw e; await sleep(1500); } // main a bougé entre-temps : on recommence
    }
    throw new Error("le dépôt a changé pendant l'envoi, réessayez");
  }
  async function publish() {
    if (!made || busy) return;
    if (!confirm("Publier ce Reel maintenant sur @megeveparcoeur (avec la musique, le lieu Megève et les 7 comptes identifiés) ?")) return;
    busy = true; bGo.disabled = bSh.disabled = bDl.disabled = true; cap.readOnly = true;
    try {
      const { key, mp4, cover } = made, base = `instagram/reel-${key}`;
      const json = { video: `${SITE}/${base}.mp4`, cover: `${SITE}/${base}-cover.jpg`, caption: cap.value.trim(), tags: TAGS, require_audio: false, location_id: LOCATION };
      await commit([[`${base}.mp4`, mp4], [`${base}-cover.jpg`, cover], [`instagram/reels/${key}.json`, new Blob([JSON.stringify(json, null, 1) + "\n"])]],
        `Instagram : reel neige ${key.slice(6, 16)} (bouton de la page météo)`);
      put("mpc_reel_neige", key);
      await publishStep(key);
    } catch (e) {
      status("Échec de l'envoi : " + (e.message || e) + (e.status === 401 ? " (reconnectez-vous à l'admin)" : ""), true);
      bGo.disabled = bDl.disabled = false; cap.readOnly = false; busy = false;
    }
  }
  async function publishStep(key) {
    busy = true; bGo.disabled = true;
    try {
      const video = `${SITE}/instagram/reel-${key}.mp4`;
      for (let k = 0; ; k++) { // attendre la mise en ligne du site (~1 à 3 min)
        status(`Mise en ligne de la vidéo sur le site… (${k * 10} s)`); prog(Math.min(0.6, k / 30));
        const r = await fetch(video + "?v=" + Date.now(), { method: "HEAD", cache: "no-store" }).catch(() => null);
        if (r && r.ok) break;
        if (k > 42) throw new Error("la vidéo n'est toujours pas en ligne après 7 min ; rouvrez cette fenêtre plus tard pour reprendre");
        await sleep(10000);
      }
      for (let k = 0; ; k++) {
        status("Publication sur Instagram…" + (k ? ` (traitement de la vidéo, ${k})` : "")); prog(0.6 + Math.min(0.39, k / 25));
        const r = await fetch("/api/reel?key=" + encodeURIComponent(key), { cache: "no-store" });
        const j = await r.json().catch(() => ({}));
        if (j.ok) {
          put("mpc_reel_neige", null); prog(1);
          stx.innerHTML = j.link ? `✅ Reel publié ! <a href="${j.link}" target="_blank" rel="noopener">Le voir sur Instagram</a>` : "✅ Reel publié !";
          stx.className = "rn-st"; return;
        }
        if (j.pending || r.status === 202) { if (k > 15) throw new Error("Instagram traite encore la vidéo ; rouvrez cette fenêtre dans quelques minutes"); await sleep(15000); continue; }
        if (r.status === 404 && k < 6) { await sleep(10000); continue; } // fichier JSON pas encore visible
        put("mpc_reel_neige", null);
        throw new Error(j.error || "erreur " + r.status);
      }
    } catch (e) {
      status("Publication : " + (e.message || e), true);
    } finally { busy = false; }
  }
  bGo.onclick = publish;
  bDl.onclick = () => { if (!made) return; const a = document.createElement("a"); a.href = URL.createObjectURL(made.mp4); a.download = made.key + ".mp4"; document.body.appendChild(a); a.click(); a.remove(); };
  bSh.onclick = async () => {
    if (!made) return;
    try { await navigator.clipboard.writeText(cap.value); } catch (_) {}
    navigator.share({ files: [new File([made.mp4], made.key + ".mp4", { type: "video/mp4" })], text: cap.value }).catch(() => {});
    status("Légende copiée : collez-la dans Instagram, puis identifiez les 7 comptes.");
  };
})();
