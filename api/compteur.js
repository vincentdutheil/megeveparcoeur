// Compteur maison des visites du site et de l'appli (écran d'accueil), sans cookie ni donnée personnelle.
// Stockage : Upstash Redis déjà utilisé par les notifications (KV_REST_API_URL / KV_REST_API_TOKEN
// ou UPSTASH_REDIS_REST_URL / UPSTASH_REDIS_REST_TOKEN). On ne garde que des totaux.
//   POST /api/compteur?k=web      → une visite du site dans le navigateur (une par session d'onglet)
//   POST /api/compteur?k=app      → une ouverture de l'appli installée
//   POST /api/compteur?k=install  → une installation de l'appli
//   GET  /api/compteur?days=30    → totaux + détail par jour (admin : en-tête X-GH-Token)
const OWNER = "vincentdutheil", REPO = "megeveparcoeur";
const KINDS = ["web", "app", "install"];
const RURL = process.env.KV_REST_API_URL || process.env.UPSTASH_REDIS_REST_URL;
const RTOK = process.env.KV_REST_API_TOKEN || process.env.UPSTASH_REDIS_REST_TOKEN;
const okTokens = new Map();

async function pipeline(cmds) {
  if (!RURL || !RTOK) throw Object.assign(new Error("stockage non configuré"), { code: 503 });
  const r = await fetch(RURL.replace(/\/$/, "") + "/pipeline", { method: "POST", headers: { Authorization: "Bearer " + RTOK, "Content-Type": "application/json" }, body: JSON.stringify(cmds) });
  const j = await r.json();
  if (!Array.isArray(j)) throw new Error((j && j.error) || "redis " + r.status);
  return j.map(x => x.result);
}

async function canWrite(tok) {
  if (!tok) return false;
  const exp = okTokens.get(tok);
  if (exp && exp > Date.now()) return true;
  const r = await fetch(`https://api.github.com/repos/${OWNER}/${REPO}`, { headers: { Authorization: "Bearer " + tok, Accept: "application/vnd.github+json", "User-Agent": "megeveparcoeur" } });
  if (!r.ok) return false;
  const j = await r.json();
  const ok = !!(j.permissions && (j.permissions.push || j.permissions.admin));
  if (ok) okTokens.set(tok, Date.now() + 15 * 60e3);
  return ok;
}

// date du jour à Megève
const dayOf = t => new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Paris" }).format(t);

module.exports = async (req, res) => {
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.setHeader("Cache-Control", "no-store");
  const send = (c, o) => { res.statusCode = c; res.end(JSON.stringify(o)); };
  const url = new URL(req.url, "http://x");
  try {
    if (req.method === "POST") {
      const k = url.searchParams.get("k");
      if (!KINDS.includes(k)) return send(400, { ok: false });
      // uniquement depuis le site lui-même, et pas les robots
      const from = String(req.headers.origin || req.headers.referer || "");
      const ua = String(req.headers["user-agent"] || "");
      if (!/^https:\/\/(www\.)?megeveparcoeur\.fr(\/|$)/.test(from) || /bot|crawl|spider|slurp|preview|lighthouse|headless/i.test(ua)) return send(204, {});
      const d = dayOf(new Date());
      await pipeline([
        ["INCR", "cpt:" + k],
        ["HINCRBY", "cpt:j:" + d, k, 1],
        ["EXPIRE", "cpt:j:" + d, 400 * 86400],
        ["SETNX", "cpt:depuis", d]
      ]);
      return send(200, { ok: true });
    }
    if (!(await canWrite(req.headers["x-gh-token"]))) return send(401, { ok: false, error: "auth" });
    const n = Math.min(365, Math.max(1, parseInt(url.searchParams.get("days") || "30", 10) || 30));
    const days = [];
    for (let i = n - 1; i >= 0; i--) days.push(dayOf(new Date(Date.now() - i * 864e5)));
    const r = await pipeline([["MGET", ...KINDS.map(k => "cpt:" + k)], ["GET", "cpt:depuis"], ...days.map(d => ["HGETALL", "cpt:j:" + d])]);
    const total = {}; KINDS.forEach((k, i) => total[k] = +(r[0][i] || 0));
    const series = days.map((d, i) => {
      const h = r[i + 2] || [], o = { day: d, web: 0, app: 0, install: 0 };
      for (let j = 0; j < h.length; j += 2) if (KINDS.includes(h[j])) o[h[j]] = +h[j + 1];
      return o;
    });
    const period = {}; KINDS.forEach(k => period[k] = series.reduce((a, s) => a + s[k], 0));
    return send(200, { ok: true, since: r[1], total, period, days: n, series });
  } catch (e) {
    return send(e.code || 502, { ok: false, error: String(e.message || e).slice(0, 200) });
  }
};
