// Notifications de l'appli (Web Push, Android + iPhone avec l'appli sur l'écran d'accueil).
// Sans dépendance : notifications « sans contenu chiffré » ; le service worker vient chercher le texte ici (?latest).
// Stockage des abonnements : Upstash Redis (Vercel → Storage), variables KV_REST_API_URL / KV_REST_API_TOKEN
// (ou UPSTASH_REDIS_REST_URL / UPSTASH_REDIS_REST_TOKEN).
// Clé VAPID : dérivée de CRON_SECRET (aucune clé supplémentaire à gérer). Si CRON_SECRET change, les abonnés
// devront réactiver les notifications.
//   GET  /api/push?key                     → clé publique VAPID
//   GET  /api/push?latest&ep=<endpoint>    → texte de la dernière notification pour cet abonné
//   POST /api/push {action:"subscribe", sub, topics, lang} / {action:"unsubscribe", endpoint}
//   GET  /api/push?job=we|snow|test        → envoi (cron Vercel avec CRON_SECRET, ou ?key=CRON_SECRET)
const crypto = require("crypto");
const SITE = "https://www.megeveparcoeur.fr";
const b64u = b => Buffer.from(b).toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");

let VK = null;
function vapid() {
  if (VK) return VK;
  const secret = process.env.CRON_SECRET;
  if (!secret) throw new Error("CRON_SECRET manquant");
  const d = Buffer.from(crypto.hkdfSync("sha256", secret, "megeveparcoeur", "vapid-p256", 32));
  const ecdh = crypto.createECDH("prime256v1"); ecdh.setPrivateKey(d);
  const pub = ecdh.getPublicKey(); // 65 octets, non compressé
  const key = crypto.createPrivateKey({ format: "jwk", key: { kty: "EC", crv: "P-256", d: b64u(d), x: b64u(pub.subarray(1, 33)), y: b64u(pub.subarray(33)) } });
  return (VK = { pub: b64u(pub), key });
}
function jwt(aud) {
  const { key } = vapid();
  const h = b64u(JSON.stringify({ typ: "JWT", alg: "ES256" }));
  const p = b64u(JSON.stringify({ aud, exp: Math.floor(Date.now() / 1000) + 12 * 3600, sub: "mailto:bonjour@megeveparcoeur.fr" }));
  const sig = crypto.sign("sha256", Buffer.from(h + "." + p), { key, dsaEncoding: "ieee-p1363" });
  return h + "." + p + "." + b64u(sig);
}

// ---- Redis (API REST d'Upstash)
const RURL = process.env.KV_REST_API_URL || process.env.UPSTASH_REDIS_REST_URL;
const RTOK = process.env.KV_REST_API_TOKEN || process.env.UPSTASH_REDIS_REST_TOKEN;
async function redis(...cmd) {
  if (!RURL || !RTOK) throw Object.assign(new Error("stockage non configuré"), { code: 503 });
  const r = await fetch(RURL, { method: "POST", headers: { Authorization: "Bearer " + RTOK, "Content-Type": "application/json" }, body: JSON.stringify(cmd) });
  const j = await r.json(); if (j.error) throw new Error(j.error); return j.result;
}
const idOf = ep => crypto.createHash("sha256").update(String(ep)).digest("hex").slice(0, 32);

// ---- envoi d'une notification (sans contenu) à un abonné
async function pushTo(sub) {
  const u = new URL(sub.endpoint);
  const r = await fetch(sub.endpoint, { method: "POST", headers: {
    TTL: "86400", Urgency: "normal", "Content-Length": "0",
    Authorization: `vapid t=${jwt(u.origin)}, k=${vapid().pub}` } });
  return r.status;
}

// ---- contenus
const paris = () => new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Paris" }).format(new Date());
const addDays = (s, k) => { const d = new Date(s + "T12:00:00Z"); d.setUTCDate(d.getUTCDate() + k); return d.toISOString().slice(0, 10); };
async function weekendMsg() {
  const A = await (await fetch(SITE + "/data/agenda.json")).json();
  const t = paris(), wd = new Date(t + "T12:00:00Z").getUTCDay();
  const fri = wd === 5 ? t : addDays(t, (5 - wd + 7) % 7), sun = addDays(fri, 2);
  const list = A.filter(e => !e.always && e.d <= sun && (e.d2 || e.d) >= fri);
  const top = list.filter(e => !e.d2 || e.d2 === e.d).concat(list.filter(e => e.d2 && e.d2 !== e.d)).slice(0, 3);
  return {
    fr: { title: `🎉 Ce week-end à Megève : ${list.length} sorties`, body: top.map(e => e.t).join(" · ") + (list.length > 3 ? " · et plus…" : ""), url: "/que-faire/ce-week-end/", tag: "we" },
    en: { title: `🎉 This weekend in Megève: ${list.length} things to do`, body: top.map(e => e.t_en || e.t).join(" · ") + (list.length > 3 ? " · and more…" : ""), url: "/en/things-to-do/this-weekend/", tag: "we" },
    n: list.length
  };
}
async function snowMsg() {
  const q = "latitude=45.8567&longitude=6.6175&elevation=1850&daily=snowfall_sum&timezone=Europe%2FParis&forecast_days=3";
  const d = (await (await fetch("https://api.open-meteo.com/v1/forecast?" + q)).json()).daily;
  const tomorrow = Math.round(d.snowfall_sum[1] || 0), two = Math.round((d.snowfall_sum[1] || 0) + (d.snowfall_sum[2] || 0));
  if (tomorrow < 10 && two < 15) return null;
  const cm = tomorrow >= 10 ? tomorrow : two, when = tomorrow >= 10 ? ["demain", "tomorrow"] : ["d'ici 2 jours", "within 2 days"];
  return {
    fr: { title: "❄️ Il va neiger !", body: `Jusqu'à ${cm} cm de neige fraîche attendus ${when[0]} en altitude à Megève.`, url: "/meteo/", tag: "snow" },
    en: { title: "❄️ Snow is coming!", body: `Up to ${cm} cm of fresh snow expected ${when[1]} up the mountain in Megève.`, url: "/en/meteo/", tag: "snow" }
  };
}

async function broadcast(topic, msg) {
  const all = await redis("HGETALL", "push:subs") || [];
  let sent = 0, gone = 0, fail = 0;
  const subs = [];
  for (let i = 0; i < all.length; i += 2) { try { const v = JSON.parse(all[i + 1]); if (topic === "test" || (v.topics || []).includes(topic)) subs.push([all[i], v]); } catch (e) {} }
  for (let i = 0; i < subs.length; i += 10) {
    await Promise.all(subs.slice(i, i + 10).map(async ([id, v]) => {
      try {
        await redis("SET", "push:msg:" + id, JSON.stringify(msg[v.lang === "en" ? "en" : "fr"]), "EX", "172800");
        const st = await pushTo(v.sub);
        if (st === 404 || st === 410) { gone++; await redis("HDEL", "push:subs", id); }
        else if (st >= 200 && st < 300) sent++; else fail++;
      } catch (e) { fail++; }
    }));
  }
  await redis("SET", "push:last", JSON.stringify(msg));
  return { subscribers: subs.length, sent, gone, fail };
}

module.exports = async (req, res) => {
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.setHeader("Cache-Control", "no-store");
  const send = (c, o) => { res.statusCode = c; res.end(JSON.stringify(o)); };
  const url = new URL(req.url, "http://x"), Q = url.searchParams;
  try {
    if (req.method === "GET" && Q.has("key") && !Q.has("job")) return send(200, { key: vapid().pub, storage: !!(RURL && RTOK) });
    if (req.method === "GET" && Q.has("latest")) {
      const ep = Q.get("ep"); let m = null;
      if (ep) m = await redis("GET", "push:msg:" + idOf(ep)).catch(() => null);
      if (!m) { const l = await redis("GET", "push:last").catch(() => null); if (l) m = JSON.stringify(JSON.parse(l).fr); }
      return send(200, m ? JSON.parse(m) : { title: "Megève par cœur", body: "Du nouveau à Megève !", url: "/" });
    }
    if (req.method === "POST") {
      let b = req.body; if (typeof b === "string") { try { b = JSON.parse(b); } catch (e) { b = {}; } } b = b || {};
      if (b.action === "subscribe") {
        const s = b.sub || {};
        if (!/^https:\/\/[^\s]+$/.test(s.endpoint || "") || String(s.endpoint).length > 800) return send(400, { ok: false, error: "endpoint" });
        const topics = (Array.isArray(b.topics) ? b.topics : []).filter(t => ["we", "snow"].includes(t));
        await redis("HSET", "push:subs", idOf(s.endpoint), JSON.stringify({ sub: { endpoint: s.endpoint, keys: s.keys || {} }, topics, lang: b.lang === "en" ? "en" : "fr", at: new Date().toISOString() }));
        return send(200, { ok: true, topics });
      }
      if (b.action === "test") { // notification de test, envoyée seulement à l'appareil qui la demande
        const id = idOf(b.endpoint), v = await redis("HGET", "push:subs", id);
        if (!v) return send(404, { ok: false, error: "abonnement introuvable" });
        const sub = JSON.parse(v), en = sub.lang === "en";
        await redis("SET", "push:msg:" + id, JSON.stringify(en ? { title: "🔔 It works!", body: "Megève par cœur notifications are on. See you Friday for the weekend programme ❄️", url: "/en/app/", tag: "test" } : { title: "🔔 Ça marche !", body: "Les notifications Megève par cœur sont activées. Rendez-vous vendredi pour le programme du week-end ❄️", url: "/app/", tag: "test" }), "EX", "3600");
        const st = await pushTo(sub.sub);
        return send(200, { ok: st >= 200 && st < 300, status: st });
      }
      if (b.action === "unsubscribe") { await redis("HDEL", "push:subs", idOf(b.endpoint)); return send(200, { ok: true }); }
      return send(400, { ok: false, error: "action" });
    }
    if (req.method === "GET" && Q.has("job")) {
      const auth = req.headers.authorization === "Bearer " + process.env.CRON_SECRET || Q.get("key") === process.env.CRON_SECRET;
      if (!process.env.CRON_SECRET || !auth) return send(401, { ok: false });
      const job = Q.get("job");
      if (job === "we") { const m = await weekendMsg(); if (!m.n) return send(200, { ok: true, skipped: "aucun événement" }); return send(200, { ok: true, ...(await broadcast("we", m)) }); }
      if (job === "snow") {
        const today = paris(), last = await redis("GET", "push:snowlast");
        if (last && last >= addDays(today, -2)) return send(200, { ok: true, skipped: "alerte récente" });
        const m = await snowMsg(); if (!m) return send(200, { ok: true, skipped: "pas de neige annoncée" });
        const r = await broadcast("snow", m); await redis("SET", "push:snowlast", today); return send(200, { ok: true, ...r });
      }
      if (job === "test") return send(200, { ok: true, ...(await broadcast("test", { fr: { title: "🔔 Test Megève par cœur", body: "Les notifications fonctionnent !", url: "/app/", tag: "test" }, en: { title: "🔔 Megève par cœur test", body: "Notifications are working!", url: "/en/app/", tag: "test" } })) });
      return send(400, { ok: false, error: "job" });
    }
    return send(405, { ok: false });
  } catch (e) { return send(e.code || 500, { ok: false, error: String(e.message || e).slice(0, 160) }); }
};
