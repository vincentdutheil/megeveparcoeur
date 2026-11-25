// Statistiques de visites pour l'admin (Vercel Web Analytics, API officielle).
// Accès réservé : l'admin envoie son jeton GitHub (en-tête X-GH-Token) ; on vérifie qu'il peut écrire dans le dépôt.
// Variables Vercel : VERCEL_TOKEN (obligatoire), VERCEL_PROJECT (nom du projet, défaut « megeveparcoeur »),
// VERCEL_TEAM_ID et VERCEL_PROJECT_ID (facultatifs : sinon retrouvés automatiquement).
const OWNER = "vincentdutheil", REPO = "megeveparcoeur";
const API = "https://api.vercel.com";
let target = null; // { projectId, teamId } mis en cache par instance
const okTokens = new Map(); // jeton GitHub vérifié -> expiration

async function vercel(path, params = {}) {
  const q = new URLSearchParams(Object.entries(params).filter(([, v]) => v !== undefined && v !== ""));
  const r = await fetch(`${API}${path}${path.includes("?") ? "&" : "?"}${q}`, { headers: { Authorization: "Bearer " + process.env.VERCEL_TOKEN } });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw Object.assign(new Error((j.error && j.error.message) || "vercel " + r.status), { status: r.status });
  return j;
}

async function findTarget() {
  if (target) return target;
  if (process.env.VERCEL_PROJECT_ID) return (target = { projectId: process.env.VERCEL_PROJECT_ID, teamId: process.env.VERCEL_TEAM_ID });
  const name = process.env.VERCEL_PROJECT || "megeveparcoeur";
  const teams = [];
  if (process.env.VERCEL_TEAM_ID) teams.push(process.env.VERCEL_TEAM_ID);
  else { try { (await vercel("/v2/teams", { limit: 20 })).teams.forEach(t => teams.push(t.id)); } catch (e) {} teams.push(undefined); }
  for (const teamId of teams) {
    try { const p = await vercel(`/v9/projects/${encodeURIComponent(name)}`, { teamId }); return (target = { projectId: p.id, teamId }); } catch (e) {}
  }
  throw new Error("projet Vercel « " + name + " » introuvable avec ce jeton");
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

const day = d => d.toISOString().slice(0, 10);

module.exports = async (req, res) => {
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.setHeader("Cache-Control", "no-store");
  const send = (c, o) => { res.statusCode = c; res.end(JSON.stringify(o)); };
  if (!(await canWrite(req.headers["x-gh-token"]))) return send(401, { ok: false, error: "auth" });
  if (!process.env.VERCEL_TOKEN) return send(503, { ok: false, error: "VERCEL_TOKEN manquant dans les variables Vercel" });
  const url = new URL(req.url, "http://x");
  const n = Math.min(30, Math.max(1, parseInt(url.searchParams.get("days") || "7", 10) || 7));
  const now = new Date(), until = day(now);
  const since = day(new Date(now.getTime() - (n - 1) * 864e5));
  const pSince = day(new Date(now.getTime() - (2 * n - 1) * 864e5)), pUntil = day(new Date(now.getTime() - n * 864e5));
  try {
    const { projectId, teamId } = await findTarget();
    const base = { projectId, teamId };
    const agg = (by, extra = {}) => vercel("/v1/query/web-analytics/visits/aggregate", { ...base, since, until, by, ...extra }).then(r => r.data || []);
    const cnt = (s, u) => vercel("/v1/query/web-analytics/visits/count", { ...base, since: s, until: u }).then(r => r.data || {}).catch(() => null);
    const [total, prev, days, pages, refs, countries, devices] = await Promise.all([
      cnt(since, until), n <= 15 ? cnt(pSince, pUntil) : Promise.resolve(null), agg("day"),
      agg("requestPath", { limit: 12 }), agg("referrerHostname", { limit: 8 }), agg("country", { limit: 8 }), agg("deviceType", { limit: 4 })
    ]);
    const sum = k => days.reduce((a, r) => a + (r[k] || 0), 0);
    return send(200, { ok: true, days: n, since, until,
      total: total && total.pageviews != null ? total : { pageviews: sum("pageviews"), visitors: sum("visitors") },
      prev, series: days, pages, refs, countries, devices });
  } catch (e) {
    return send(502, { ok: false, error: String(e.message || e).slice(0, 200) });
  }
};
