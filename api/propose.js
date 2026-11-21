// Propositions d'événements (formulaire /proposer/ et /en/submit-event/).
// Chaque proposition est ajoutée à data/propositions.json sur la branche « propositions » du dépôt GitHub
// (branche non déployée : voir vercel.json). Vincent les valide ou les refuse dans l'admin, onglet « Propositions ».
// Variable Vercel requise : GITHUB_TOKEN (jeton GitHub « fine-grained », accès Contents en lecture/écriture à ce seul dépôt).
// Avertissement par e-mail : à chaque proposition, un e-mail (Brevo, BREVO_API_KEY) part vers NOTIFY_EMAIL avec un lien
// signé (CRON_SECRET) qui ouvre une page de confirmation « Publier / Refuser » (une page, pas un lien direct :
// les antivirus des messageries ouvrent les liens tout seuls).
const crypto = require("crypto");
const SITE = "https://www.megeveparcoeur.fr";
const CATS = ["Fête", "Concert", "Marché", "Spectacle", "Expo", "Sport", "Ski", "Famille", "Culture", "Noël", "Gastronomie"];
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

const idOf = it => it.id || crypto.createHash("sha256").update((it.at || "") + "|" + (it.t || "")).digest("hex").slice(0, 16);
const sig = id => crypto.createHmac("sha256", process.env.CRON_SECRET || "x").update("prop:" + id).digest("hex").slice(0, 32);
const esc = t => String(t == null ? "" : t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const fdate = d => { if (!d) return ""; const [y, m, j] = d.split("-"); return `${+j} ${["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."][+m - 1]} ${y}`; };
function guessCat(it) {
  const t = ((it.t || "") + " " + (it.x || "")).toLowerCase();
  const rules = [["Concert", /concert|musique|chorale|orchestre|récital/], ["Marché", /march[ée]|brocante|vide-grenier|braderie/], ["Expo", /expo|vernissage|galerie/],
    ["Spectacle", /spectacle|théâtre|theatre|cirque|conte|cinéma|projection/], ["Noël", /noël|noel|père no/], ["Ski", /\bski|slalom|piste/],
    ["Sport", /course|trail|tournoi|match|vélo|velo|randonn|marche nordique/], ["Gastronomie", /dégustation|gastronom|repas|raclette|fondue|vin\b/],
    ["Famille", /enfant|famille|kids/], ["Culture", /conférence|visite|patrimoine|lecture|atelier/]];
  return (rules.find(([, re]) => re.test(t)) || ["Fête"])[0];
}
const detailsHtml = it => `<p style="margin:0 0 6px;font-size:20px;font-weight:800">${esc(it.t)}</p>
  <p style="margin:0 0 10px;color:#555">📍 ${esc(it.lieu)}${it.where ? " · " + esc(it.where) : ""}<br>📅 ${fdate(it.d)}${it.d2 && it.d2 !== it.d ? " → " + fdate(it.d2) : ""}${it.h ? " · " + esc(it.h) : ""}</p>
  <p style="margin:0 0 10px;white-space:pre-wrap">${esc(it.x)}</p>
  ${it.u ? `<p style="margin:0 0 10px"><a href="${esc(it.u)}">${esc(it.u)}</a></p>` : ""}
  <p style="margin:0;color:#777;font-size:13px">Envoyé par ${esc(it.name || "—")} · ${esc(it.mail)}</p>`;

async function notify(it) {
  const key = process.env.BREVO_API_KEY, to = process.env.NOTIFY_EMAIL;
  if (!key || !to) return;
  const link = `${SITE}/api/propose?id=${it.id}&s=${sig(it.id)}`;
  const html = `<div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;color:#222">
  <p style="color:#c27a34;font-weight:700;letter-spacing:.1em;font-size:12px;text-transform:uppercase">Nouvelle proposition d'événement</p>
  <div style="border:1px solid #e3e3e3;border-radius:14px;padding:18px">${detailsHtml(it)}</div>
  <p style="text-align:center;margin:22px 0"><a href="${link}&a=pub" style="background:#c8323d;color:#fff;text-decoration:none;font-weight:700;padding:13px 26px;border-radius:999px;display:inline-block;margin:4px">✅ Publier</a>
  <a href="${link}&a=no" style="background:#eee;color:#333;text-decoration:none;font-weight:700;padding:13px 26px;border-radius:999px;display:inline-block;margin:4px">Refuser</a></p>
  <p style="color:#888;font-size:12px;text-align:center">Le bouton ouvre une page de confirmation sur le site. Vous pouvez aussi gérer les propositions dans l'admin.</p></div>`;
  const r = await fetch("https://api.brevo.com/v3/smtp/email", { method: "POST", headers: { "api-key": key, "Content-Type": "application/json", accept: "application/json" },
    body: JSON.stringify({ sender: { name: "Megève par cœur", email: process.env.SENDER_EMAIL || "bonjour@megeveparcoeur.fr" }, to: [{ email: to }],
      replyTo: { email: it.mail, name: it.name || it.mail }, subject: "📝 Événement proposé : " + it.t.slice(0, 80), htmlContent: html }) });
  if (!r.ok) throw new Error("brevo " + r.status + " " + (await r.text()).slice(0, 120));
}

async function readJson(path, ref) {
  const r = await gh(`/contents/${path}?ref=${ref}`);
  if (!r.ok) throw new Error("read " + path + " " + r.status);
  const f = await r.json(); return { sha: f.sha, data: JSON.parse(Buffer.from(f.content, "base64").toString("utf8")) };
}
async function writeJson(path, ref, sha, data, message) {
  const w = await gh(`/contents/${path}`, { method: "PUT", body: JSON.stringify({ message, branch: ref, sha, content: Buffer.from(JSON.stringify(data, null, 1) + "\n").toString("base64") }) });
  if (!w.ok) throw new Error("write " + path + " " + w.status);
}
function page(res, title, body) {
  res.statusCode = 200; res.setHeader("Content-Type", "text/html; charset=utf-8"); res.setHeader("Cache-Control", "no-store"); res.setHeader("X-Robots-Tag", "noindex");
  res.end(`<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>${esc(title)}</title>
<style>body{font-family:system-ui,-apple-system,Segoe UI,sans-serif;background:#f1f4f9;color:#1c2533;margin:0;padding:24px}main{max-width:560px;margin:auto;background:#fff;border-radius:18px;padding:22px;box-shadow:0 10px 30px rgba(0,0,0,.08)}
h1{font-size:1.3rem;margin:0 0 14px}.box{border:1px solid #e3e8ef;border-radius:14px;padding:16px;margin-bottom:16px}label{font-weight:700;display:block;margin:10px 0 4px}select{font:inherit;padding:10px;border-radius:10px;border:1px solid #ccd;width:100%}
.chk{display:flex;gap:14px;margin:10px 0}.chk label{font-weight:600;display:flex;gap:6px;align-items:center;margin:0}button{font:700 1rem system-ui;border:0;border-radius:999px;padding:14px 22px;cursor:pointer;margin:6px 6px 0 0}.pub{background:#c8323d;color:#fff}.no{background:#eee}a{color:#c8323d}</style></head><body><main>${body}</main></body></html>`);
}

async function moderate(req, res, url) {
  const q = url.searchParams;
  let b = req.body; if (typeof b === "string") b = Object.fromEntries(new URLSearchParams(b)); b = b || {};
  const id = String(b.id || q.get("id") || ""), s = String(b.s || q.get("s") || "");
  if (!/^[a-f0-9]{16}$/.test(id) || s !== sig(id)) return page(res, "Lien invalide", "<h1>Lien invalide ou expiré</h1><p>Gérez la proposition depuis l'admin.</p>");
  let props;
  try { props = await readJson(FILE, BRANCH); } catch (e) { return page(res, "Erreur", "<h1>Impossible de lire les propositions</h1><p>Réessayez dans un instant.</p>"); }
  const k = props.data.findIndex(x => idOf(x) === id), it = props.data[k];
  if (!it) return page(res, "Déjà traitée", "<h1>Cette proposition a déjà été traitée ✓</h1><p><a href=\"/admin/\">Ouvrir l'admin</a></p>");
  if (req.method !== "POST") {
    const a = q.get("a") === "no" ? "no" : "pub", cat = guessCat(it);
    return page(res, "Proposition", `<h1>${a === "no" ? "Refuser cette proposition ?" : "Publier cet événement ?"}</h1><div class="box">${detailsHtml(it)}</div>
<form method="post"><input type="hidden" name="id" value="${id}"><input type="hidden" name="s" value="${s}">
${a === "pub" ? `<label for="cat">Catégorie</label><select id="cat" name="cat">${CATS.map(c => `<option${c === cat ? " selected" : ""}>${c}</option>`).join("")}</select>
<div class="chk"><label><input type="checkbox" name="free" value="1"> Gratuit</label><label><input type="checkbox" name="kids" value="1"> Pour les enfants</label></div>` : ""}
<button class="pub" name="a" value="pub">✅ Publier</button><button class="no" name="a" value="no">Refuser</button></form>`);
  }
  const act = b.a === "no" ? "no" : "pub";
  try {
    if (act === "pub") {
      const ag = await readJson("data/agenda.json", "main");
      const ev = { d: it.d, lieu: it.lieu, cat: CATS.includes(b.cat) ? b.cat : "Fête", t: it.t, x: (it.x || "") + (it.where ? " (" + it.where + ")" : ""), v: true };
      if (it.d2 && it.d2 !== it.d) ev.d2 = it.d2; if (it.h) ev.h = it.h; if (it.u) ev.u = it.u; if (b.free) ev.free = true; if (b.kids) ev.kids = true;
      const list = ag.data.concat([ev]).sort((x, y) => (x.d || "").localeCompare(y.d || ""));
      await writeJson("data/agenda.json", "main", ag.sha, list, "Événement proposé publié : " + it.t.slice(0, 60));
    }
    props.data.splice(k, 1);
    await writeJson(FILE, BRANCH, props.sha, props.data, (act === "pub" ? "Proposition publiée : " : "Proposition refusée : ") + it.t.slice(0, 60));
  } catch (e) { return page(res, "Erreur", "<h1>Ça n'a pas marché</h1><p>Réessayez, ou passez par l'admin.</p><p style=\"color:#888\">" + esc(e.message) + "</p>"); }
  return page(res, "C'est fait", act === "pub"
    ? `<h1>✅ Publié !</h1><p><b>${esc(it.t)}</b> sera dans l'agenda du site d'ici une minute, et dans la newsletter de jeudi.</p><p><a href="/#agenda">Voir l'agenda</a></p>`
    : `<h1>Proposition refusée</h1><p>« ${esc(it.t)} » a été retirée de la liste.</p>`);
}

module.exports = async (req, res) => {
  const url = new URL(req.url, SITE);
  if (url.searchParams.has("id") || (req.method === "POST" && req.body && (req.body.s || (typeof req.body === "string" && req.body.includes("s="))))) return moderate(req, res, url);
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
  item.id = idOf(item);
  const date = /^20\d\d-\d\d-\d\d$/;
  if (!item.t || !date.test(item.d) || (item.d2 && !date.test(item.d2)) || !LIEUX.includes(item.lieu) || !item.x
      || !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(item.mail) || !b.consent) return send(400, { ok: false, error: "fields" });
  if (item.u && !/^https?:\/\//i.test(item.u)) item.u = "https://" + item.u;
  for (const k of Object.keys(item)) if (item[k] === "") delete item[k];
  if (!process.env.GITHUB_TOKEN) return send(503, { ok: false, error: "not configured" });
  try {
    await ensureBranch(); await append(item);
    h.push(now); hits.set(ip, h);
    try { await notify(item); } catch (e) { console.error("notify", e.message); }
    return send(200, { ok: true });
  } catch (e) { return send(e.full ? 503 : 502, { ok: false, error: e.full ? "full" : "store" }); }
};
