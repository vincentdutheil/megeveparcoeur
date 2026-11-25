// Photos Instagram où @megeveparcoeur est identifié (API Instagram avec Facebook Login).
// Variables Vercel : META_APP_ID, META_APP_SECRET, META_CONFIG_ID (configuration Facebook Login for Business),
// et le stockage Upstash Redis déjà utilisé par les notifications (KV_REST_API_URL / KV_REST_API_TOKEN).
// L'accès (jeton de page, qui n'expire pas) est obtenu par le bouton « Connecter Instagram » de l'admin
// et reste uniquement côté serveur, dans Redis.
//
//   POST /api/ig {action:"start"}        (admin) → adresse de connexion Facebook
//   GET  /api/ig-auth?code&state         retour de Facebook → enregistre l'accès → /admin/?ig=ok
//   GET  /api/ig?list                    (admin) → état + publications où le compte est identifié
//   GET  /api/ig?img=<id>                (admin) → l'image (pour l'ajouter à la galerie)
//   POST /api/ig {action:"ignore", id}   (admin) → masque une publication
//   POST /api/ig {action:"disconnect"}   (admin)
const crypto = require("crypto");
const OWNER = "vincentdutheil", REPO = "megeveparcoeur", SITE = "https://www.megeveparcoeur.fr";
const V = process.env.META_GRAPH_VERSION || "v23.0", GRAPH = "https://graph.facebook.com/" + V;
const REDIRECT = SITE + "/api/ig-auth";
const PERMS = "instagram_basic,instagram_content_publish,instagram_manage_comments,pages_show_list,pages_read_engagement,business_management";

// ---- Redis (Upstash)
const RURL = process.env.KV_REST_API_URL || process.env.UPSTASH_REDIS_REST_URL;
const RTOK = process.env.KV_REST_API_TOKEN || process.env.UPSTASH_REDIS_REST_TOKEN;
async function redis(...cmd) {
  if (!RURL || !RTOK) throw Object.assign(new Error("stockage Redis non configuré"), { code: 503 });
  const r = await fetch(RURL, { method: "POST", headers: { Authorization: "Bearer " + RTOK, "Content-Type": "application/json" }, body: JSON.stringify(cmd) });
  const j = await r.json(); if (j.error) throw new Error(j.error); return j.result;
}

// ---- admin : jeton GitHub avec droit d'écriture sur le dépôt
const okTokens = new Map();
async function canWrite(tok) {
  if (!tok) return false;
  const exp = okTokens.get(tok); if (exp && exp > Date.now()) return true;
  const r = await fetch(`https://api.github.com/repos/${OWNER}/${REPO}`, { headers: { Authorization: "Bearer " + tok, Accept: "application/vnd.github+json", "User-Agent": "megeveparcoeur" } });
  if (!r.ok) return false;
  const j = await r.json(), ok = !!(j.permissions && (j.permissions.push || j.permissions.admin));
  if (ok) okTokens.set(tok, Date.now() + 15 * 60e3);
  return ok;
}

async function graph(path, params = {}) {
  const u = new URL(path.startsWith("http") ? path : GRAPH + path);
  Object.entries(params).forEach(([k, v]) => v != null && u.searchParams.set(k, v));
  const r = await fetch(u), j = await r.json().catch(() => ({}));
  if (!r.ok || j.error) throw Object.assign(new Error((j.error && j.error.message) || "graph " + r.status), { status: r.status, meta: j.error });
  return j;
}
const configured = () => !!(process.env.META_APP_ID && process.env.META_APP_SECRET);
async function getAuth() { const s = await redis("GET", "ig:auth"); return s ? JSON.parse(s) : null; }

// ---- retour de Facebook après la connexion
async function callback(req, res, url) {
  const back = (q) => { res.statusCode = 302; res.setHeader("Location", "/admin/?ig=" + encodeURIComponent(q)); res.end(); };
  try {
    if (url.searchParams.get("error")) return back("refus");
    const code = url.searchParams.get("code"), state = url.searchParams.get("state") || "";
    if (!code || !/^[a-f0-9]{32}$/.test(state) || !(await redis("GET", "ig:state:" + state))) return back("expire");
    await redis("DEL", "ig:state:" + state);
    const id = process.env.META_APP_ID, secret = process.env.META_APP_SECRET;
    const short = await graph("/oauth/access_token", { client_id: id, client_secret: secret, redirect_uri: REDIRECT, code });
    const long = await graph("/oauth/access_token", { grant_type: "fb_exchange_token", client_id: id, client_secret: secret, fb_exchange_token: short.access_token });
    const pages = await graph("/me/accounts", { access_token: long.access_token, fields: "id,name,access_token,instagram_business_account{id,username}", limit: 100 });
    const withIg = (pages.data || []).filter(p => p.instagram_business_account);
    const page = withIg.find(p => /megeveparcoeur/i.test(p.instagram_business_account.username || "")) || withIg[0];
    if (!page) return back("aucun-compte");
    await redis("SET", "ig:auth", JSON.stringify({ pageId: page.id, pageName: page.name, pageToken: page.access_token,
      igId: page.instagram_business_account.id, username: page.instagram_business_account.username, userToken: long.access_token, at: new Date().toISOString() }));
    return back("ok");
  } catch (e) {
    console.error("ig-auth", e.message);
    return back("erreur");
  }
}

module.exports = async (req, res) => {
  const url = new URL(req.url, SITE);
  if (url.pathname.endsWith("/ig-auth")) return callback(req, res, url);
  const send = (c, o) => { res.statusCode = c; res.setHeader("Content-Type", "application/json; charset=utf-8"); res.setHeader("Cache-Control", "no-store"); res.end(JSON.stringify(o)); };
  if (!(await canWrite(req.headers["x-gh-token"]))) return send(401, { ok: false, error: "auth" });
  try {
    if (req.method === "POST") {
      let b = req.body; if (typeof b === "string") try { b = JSON.parse(b); } catch (e) { b = {}; } b = b || {};
      if (b.action === "start") {
        if (!configured()) return send(503, { ok: false, error: "META_APP_ID / META_APP_SECRET manquants dans Vercel" });
        const state = crypto.randomBytes(16).toString("hex");
        await redis("SET", "ig:state:" + state, "1", "EX", 900);
        const q = new URLSearchParams({ client_id: process.env.META_APP_ID, redirect_uri: REDIRECT, state, response_type: "code" });
        if (process.env.META_CONFIG_ID) q.set("config_id", process.env.META_CONFIG_ID); else q.set("scope", PERMS);
        return send(200, { ok: true, url: `https://www.facebook.com/${V}/dialog/oauth?${q}` });
      }
      if (b.action === "ignore" && /^\d+$/.test(String(b.id))) { await redis("SADD", "ig:ignored", String(b.id)); return send(200, { ok: true }); }
      if (b.action === "disconnect") { await redis("DEL", "ig:auth"); return send(200, { ok: true }); }
      return send(400, { ok: false, error: "action inconnue" });
    }
    const auth = await getAuth();
    if (url.searchParams.has("img")) {
      const id = url.searchParams.get("img");
      if (!auth || !/^\d+$/.test(id)) return send(404, { ok: false });
      const m = await graph("/" + id, { access_token: auth.pageToken, fields: "media_type,media_url,thumbnail_url,children{media_type,media_url,thumbnail_url}" });
      const pickUrl = x => x.media_type === "VIDEO" ? x.thumbnail_url : x.media_url;
      const src = m.media_type === "CAROUSEL_ALBUM" && m.children ? pickUrl(m.children.data.find(c => c.media_type === "IMAGE") || m.children.data[0]) : pickUrl(m);
      if (!src) return send(404, { ok: false });
      const r = await fetch(src); if (!r.ok) return send(502, { ok: false });
      res.statusCode = 200; res.setHeader("Content-Type", r.headers.get("content-type") || "image/jpeg"); res.setHeader("Cache-Control", "no-store");
      return res.end(Buffer.from(await r.arrayBuffer()));
    }
    // ?list
    if (!auth) return send(200, { ok: true, connected: false, configured: configured(), hasConfig: !!process.env.META_CONFIG_ID });
    const ignored = new Set((await redis("SMEMBERS", "ig:ignored")) || []);
    let items = [];
    try {
      const t = await graph(`/${auth.igId}/tags`, { access_token: auth.pageToken, limit: 50,
        fields: "id,media_type,media_url,thumbnail_url,permalink,username,caption,timestamp,children{media_type,media_url,thumbnail_url}" });
      items = (t.data || []).filter(m => !ignored.has(m.id)).map(m => {
        const c = m.media_type === "CAROUSEL_ALBUM" && m.children ? (m.children.data.find(x => x.media_type === "IMAGE") || m.children.data[0]) : m;
        return { id: m.id, by: m.username ? "@" + m.username : "", caption: (m.caption || "").slice(0, 300), date: m.timestamp, link: m.permalink,
          type: m.media_type, preview: c && (c.media_type === "VIDEO" ? c.thumbnail_url : c.media_url) };
      });
    } catch (e) {
      const expired = e.meta && (e.meta.code === 190 || e.meta.type === "OAuthException");
      return send(200, { ok: true, connected: !expired, username: auth.username, error: (expired ? "Accès expiré : reconnecte Instagram. " : "") + e.message.slice(0, 200), items: [] });
    }
    return send(200, { ok: true, connected: true, username: auth.username, page: auth.pageName, since: auth.at, items });
  } catch (e) {
    return send(e.code === 503 ? 503 : 502, { ok: false, error: String(e.message || e).slice(0, 200) });
  }
};
