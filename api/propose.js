// Propositions d'événements (formulaire /proposer/ et /en/submit-event/).
// Chaque proposition est ajoutée à data/propositions.json sur la branche « propositions » du dépôt GitHub
// (branche non déployée : voir vercel.json). Vincent les valide ou les refuse dans l'admin, onglet « Propositions ».
// Variable Vercel requise : GITHUB_TOKEN (jeton GitHub « fine-grained », accès Contents en lecture/écriture à ce seul dépôt).
const OWNER = "vincentdutheil", REPO = "megeveparcoeur", BRANCH = "propositions", FILE = "data/propositions.json";
const LIEUX = ["Megève", "Combloux", "Demi-Quartier", "Praz-sur-Arly"];
const hits = new Map(); // anti-abus simple, par adresse IP (mémoire de l'instance)

function clean(v, n) { return String(v == null ? "" : v).replace(/[\u0000-\u001f\u007f]/g, " ").replace(/\s+/g, " ").trim().slice(0, n); }
function cleanText(v, n) { return String(v == null ? "" : v).replace(/[\u0000-\u0009\u000b-\u001f\u007f]/g, " ").trim().slice(0, n); }

async function gh(path, opt = {}) {
  const r = await fetch(`https://api.github.com/repos/${OWNER}/${REPO}${path}`, { ...opt, headers: {
    Authorization: "Bearer " + process.env.GITHUB_TOKEN, Accept: "application/vnd.github+json", "User-Agent": "megeveparcoeur", ...(opt.body ? { "Content-Type": "application/json" } : {}) } });
  return r;
}

async function ensureBranch() {
  const r = await gh(`/git/ref/heads/${BRANCH}`);
  if (r.ok) return;
  const main = await (await gh("/git/ref/heads/main")).json();
  const c = await gh("/git/refs", { method: "POST", body: JSON.stringify({ ref: "refs/heads/" + BRANCH, sha: main.object.sha }) });
  if (!c.ok && c.status !== 422) throw new Error("branch " + c.status);
}

async function append(item) {
  for (let attempt = 0; attempt < 3; attempt++) {
    const r = await gh(`/contents/${FILE}?ref=${BRANCH}`);
    let list = [], sha;
    if (r.ok) { const f = await r.json(); sha = f.sha; list = JSON.parse(Buffer.from(f.content, "base64").toString("utf8")); }
    else if (r.status !== 404) throw new Error("read " + r.status);
    if (list.length >= 300) throw Object.assign(new Error("full"), { full: true });
    list.push(item);
    const w = await gh(`/contents/${FILE}`, { method: "PUT", body: JSON.stringify({
      message: "Nouvelle proposition d'événement : " + item.t.slice(0, 60), branch: BRANCH, ...(sha ? { sha } : {}),
      content: Buffer.from(JSON.stringify(list, null, 1) + "\n").toString("base64") }) });
    if (w.ok) return;
    if (w.status !== 409 && w.status !== 422) throw new Error("write " + w.status);
  }
  throw new Error("conflict");
}

module.exports = async (req, res) => {
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  const send = (code, o) => { res.statusCode = code; res.end(JSON.stringify(o)); };
  if (req.method === "GET") return send(200, { ok: true, configured: !!process.env.GITHUB_TOKEN });
  if (req.method !== "POST") return send(405, { ok: false, error: "method" });
  let b = req.body;
  if (typeof b === "string") { try { b = JSON.parse(b); } catch (e) { b = {}; } }
  b = b || {};
  if (b.website) return send(200, { ok: true }); // pot de miel : robot, on ignore poliment
  const ip = clean((req.headers["x-forwarded-for"] || "").split(",")[0], 60), now = Date.now();
  const h = (hits.get(ip) || []).filter(t => now - t < 3600e3);
  if (h.length >= 5) return send(429, { ok: false, error: "rate" });
  const item = {
    t: clean(b.t, 120), d: clean(b.d, 10), d2: clean(b.d2, 10), h: clean(b.h, 40), lieu: clean(b.lieu, 20),
    where: clean(b.where, 120), x: cleanText(b.x, 1200), u: clean(b.u, 300), name: clean(b.name, 120), mail: clean(b.mail, 160),
    lang: b.lang === "en" ? "en" : "fr", at: new Date().toISOString()
  };
  const date = /^20\d\d-\d\d-\d\d$/;
  if (!item.t || !date.test(item.d) || (item.d2 && !date.test(item.d2)) || !LIEUX.includes(item.lieu) || !item.x
      || !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(item.mail) || !b.consent) return send(400, { ok: false, error: "fields" });
  if (item.u && !/^https?:\/\//i.test(item.u)) item.u = "https://" + item.u;
  for (const k of Object.keys(item)) if (item[k] === "") delete item[k];
  if (!process.env.GITHUB_TOKEN) return send(503, { ok: false, error: "not configured" });
  try {
    await ensureBranch(); await append(item);
    h.push(now); hits.set(ip, h);
    return send(200, { ok: true });
  } catch (e) { return send(e.full ? 503 : 502, { ok: false, error: e.full ? "full" : "store" }); }
};
