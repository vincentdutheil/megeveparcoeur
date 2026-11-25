// Chatbot du site : répond aux questions des visiteurs avec l'IA de Groq (plan gratuit : jamais facturé,
// au-delà du quota Groq renvoie simplement une erreur 429 → on répond « fallback » et le navigateur
// propose les pages utiles). L'IA ne répond qu'à partir du contenu du site (data/chat-kb.json),
// de l'agenda (data/agenda.json) et des prévisions de neige (/api/neige).
// Variables Vercel : GROQ_API_KEY (obligatoire pour activer l'IA), GROQ_MODELS (facultatif, liste séparée
// par des virgules ; chaque modèle a son propre quota gratuit, on passe au suivant si l'un est épuisé).
// Limites maison (Redis Upstash déjà utilisé) : 15 questions par heure et par visiteur, CHAT_DAY_MAX par jour (défaut 400).
//   GET  /api/chat              → { ok, enabled }
//   POST /api/chat {q, lang, h} → { ok, a, src:[{t,u}] }  ou  { ok:false, fallback:true, error }
const crypto = require("crypto");
const SITE = "https://www.megeveparcoeur.fr";
const MODELS = (process.env.GROQ_MODELS || "openai/gpt-oss-120b,qwen/qwen3.8-27b,openai/gpt-oss-20b").split(",").map(s => s.trim()).filter(Boolean);
const RURL = process.env.KV_REST_API_URL || process.env.UPSTASH_REDIS_REST_URL;
const RTOK = process.env.KV_REST_API_TOKEN || process.env.UPSTASH_REDIS_REST_TOKEN;
const PER_HOUR = 15, DAY_MAX = +process.env.CHAT_DAY_MAX || 400;

let KB = null, KB_AT = 0, AG = null, AG_AT = 0;
async function getJSON(path) { const r = await fetch(SITE + path, { headers: { "User-Agent": "megeveparcoeur-chat" } }); if (!r.ok) throw new Error(path + " " + r.status); return r.json(); }
async function kb() { if (!KB || Date.now() - KB_AT > 30 * 60e3) { KB = await getJSON("/data/chat-kb.json"); KB_AT = Date.now(); } return KB; }
async function agenda() { if (!AG || Date.now() - AG_AT > 30 * 60e3) { AG = await getJSON("/data/agenda.json"); AG_AT = Date.now(); } return AG; }

async function redis(cmds) {
  if (!RURL || !RTOK) return null;
  try {
    const r = await fetch(RURL.replace(/\/$/, "") + "/pipeline", { method: "POST", headers: { Authorization: "Bearer " + RTOK, "Content-Type": "application/json" }, body: JSON.stringify(cmds) });
    const j = await r.json(); return Array.isArray(j) ? j.map(x => x.result) : null;
  } catch (e) { return null; }
}

const norm = s => String(s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
const STOP = new Set("le la les un une des de du d l a au aux et ou en est il elle on je tu vous nous ce cet cette ces pour par sur dans avec sans que qui quoi quel quelle quels quelles comment ou y a-t-il est-ce faut peut puis the a an of to in on at for is are what how do does can i you it and or with from my me be there".split(" "));
const toks = s => norm(s).split(/[^a-z0-9]+/).filter(w => w.length > 1 && !STOP.has(w));

function pick(chunks, q, max = 5200) {
  const qt = toks(q); if (!qt.length) return [];
  const scored = chunks.map(c => {
    const t = norm(c.t + " " + c.x); let s = 0;
    for (const w of qt) { const n = t.split(w.length > 4 ? w.slice(0, -1) : w).length - 1; if (n) s += 1 + Math.min(n, 4) * .25 + (norm(c.t).includes(w) ? 1 : 0); }
    return { c, s };
  }).filter(x => x.s > 0).sort((a, b) => b.s - a.s);
  const out = []; let len = 0;
  for (const { c } of scored) { if (len + c.x.length > max) continue; out.push(c); len += c.x.length; if (len > max - 300) break; }
  return out;
}

const today = () => new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Paris" }).format(new Date());
function events(all, lang, q) {
  const t = today(), end = new Date(Date.now() + 15 * 864e5).toISOString().slice(0, 10), qn = norm(q);
  const list = all.filter(e => (e.d2 || e.d) >= t && e.d <= end);
  const kids = /enfant|kid|famil|child/.test(qn), free = /gratuit|free/.test(qn);
  return list.filter(e => (!kids || /enfant|kid|famil/i.test(norm(e.cat + e.x + (e.tags || "")))) && (!free || /gratuit|free/.test(norm(JSON.stringify(e)))))
    .slice(0, 15).map(e => `- ${e.d}${e.d2 ? " → " + e.d2 : ""}${e.h ? " " + e.h : ""} · ${e.lieu} · ${lang === "en" && e.t_en ? e.t_en : e.t}${(lang === "en" ? e.x_en : e.x) ? " : " + String(lang === "en" ? e.x_en : e.x).slice(0, 100) : ""}`).join("\n");
}
async function snow() {
  try {
    const j = await getJSON("/api/neige");
    return (j.stations || []).map(s => `- ${s.nom} (${s.altitude} m) : ${s.sol} cm au sol, ${s.prevu} cm prévus sur 7 jours`).join("\n");
  } catch (e) { return ""; }
}

function system(lang, ctx) {
  const fr = lang !== "en";
  return (fr
    ? `Tu es l'assistant du site Megève par cœur (www.megeveparcoeur.fr), guide gratuit de Megève, Combloux, Demi-Quartier et Praz-sur-Arly. Réponds en français, en 2 à 5 phrases, chaleureux et précis.`
    : `You are the assistant of the Megève par cœur website (www.megeveparcoeur.fr), a free guide to Megève, Combloux, Demi-Quartier and Praz-sur-Arly. Answer in English, in 2 to 5 sentences, warm and precise.`) + `
${fr ? "RÈGLES" : "RULES"}:
- ${fr ? "Utilise UNIQUEMENT les informations du CONTEXTE ci-dessous. N'invente jamais un prix, une date, un horaire, un nom ou un lien." : "Use ONLY the information in the CONTEXT below. Never invent a price, date, time, name or link."}
- ${fr ? "Si le contexte ne contient pas la réponse, dis-le simplement et conseille l'office de tourisme (megeve-tourisme.fr, combloux.com)." : "If the context does not contain the answer, say so and suggest the tourist office (megeve-tourisme.fr, combloux.com)."}
- ${fr ? "Termine si possible par un lien vers la page du site la plus utile, au format [titre](/chemin/)." : "If possible, end with a link to the most useful page of the site, formatted [title](/path/)."}
- ${fr ? "Pas de titres, pas de listes longues, pas d'emoji en excès. Ne parle que de Megève et de ses environs ; refuse poliment le reste." : "No headings, no long lists, few emojis. Only talk about Megève and its surroundings; politely decline anything else."}
- ${fr ? "Aujourd'hui" : "Today"}: ${today()}.

${fr ? "CONTEXTE" : "CONTEXT"}:
${ctx}`;
}

async function groq(messages) {
  let last = "no_model";
  for (const model of MODELS) {
    const extra = /gpt-oss/.test(model) ? { reasoning_effort: "low", include_reasoning: false } : /qwen/.test(model) ? { reasoning_format: "hidden" } : {};
    const bodies = [{ model, messages, temperature: .3, max_tokens: 450, ...extra }, { model, messages, temperature: .3, max_tokens: 450 }];
    for (let i = 0; i < bodies.length; i++) {
      const body = bodies[i];
      const r = await fetch("https://api.groq.com/openai/v1/chat/completions", {
        method: "POST", headers: { Authorization: "Bearer " + process.env.GROQ_API_KEY, "Content-Type": "application/json" }, body: JSON.stringify(body)
      }).catch(e => ({ ok: false, status: 0, json: async () => ({ error: { message: e.message } }) }));
      if (r.ok) {
        const j = await r.json();
        const a = String((j.choices && j.choices[0] && j.choices[0].message && j.choices[0].message.content) || "").replace(/<think>[\s\S]*?<\/think>/g, "").trim();
        if (a) return { a, model };
        last = "empty"; break;
      }
      last = "groq " + r.status;
      if (r.status === 400 && i === 0 && Object.keys(extra).length) continue; // paramètre non accepté : on réessaie sans
      break; // 429 (quota), 5xx… : modèle suivant
    }
  }
  throw Object.assign(new Error(last), { fallback: true });
}

module.exports = async (req, res) => {
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.setHeader("Cache-Control", "no-store");
  const send = (c, o) => { res.statusCode = c; res.end(JSON.stringify(o)); };
  if (req.method === "GET") return send(200, { ok: true, enabled: !!process.env.GROQ_API_KEY });
  if (req.method !== "POST") return send(405, { ok: false });
  if (!process.env.GROQ_API_KEY) return send(503, { ok: false, fallback: true, error: "disabled" });
  const from = String(req.headers.origin || req.headers.referer || "");
  if (from && !/^https:\/\/(www\.)?megeveparcoeur\.fr|^https:\/\/[\w-]+\.vercel\.app|^http:\/\/localhost/.test(from)) return send(403, { ok: false, error: "origin" });
  let b = req.body; if (typeof b === "string") { try { b = JSON.parse(b); } catch (e) { b = {}; } } b = b || {};
  const q = String(b.q || "").replace(/\s+/g, " ").trim().slice(0, 400), lang = b.lang === "en" ? "en" : "fr";
  if (q.length < 2) return send(400, { ok: false, error: "q" });

  // limites : par visiteur (adresse IP hachée, jamais stockée en clair) et par jour
  const ip = String(req.headers["x-forwarded-for"] || "").split(",")[0].trim();
  const id = crypto.createHash("sha256").update(ip + "|mpc-chat").digest("hex").slice(0, 16), d = today(), hr = new Date().toISOString().slice(0, 13);
  const lim = await redis([["INCR", `chat:ip:${id}:${hr}`], ["EXPIRE", `chat:ip:${id}:${hr}`, "3700"], ["INCR", `chat:day:${d}`], ["EXPIRE", `chat:day:${d}`, "864000"]]);
  if (lim && (lim[0] > PER_HOUR || lim[2] > DAY_MAX)) return send(429, { ok: false, fallback: true, error: "limit" });

  try {
    const K = await kb(), hist = Array.isArray(b.h) ? b.h.slice(-4) : [];
    const ctxQ = q + " " + hist.filter(m => m && m.r === "u").map(m => String(m.t || "")).join(" ");
    const parts = pick(K.chunks[lang] || K.chunks.fr, ctxQ);
    const qn = norm(ctxQ); let ctx = parts.map(c => `### ${c.t} (${c.u})\n${c.x}`).join("\n\n");
    if (/agenda|evenement|event|week|samedi|dimanche|saturday|sunday|aujourd|today|demain|tomorrow|faire|do\b|concert|spectacle|show|marche|market|fete|festival|enfant|kid|soir|night/.test(qn)) {
      const ev = events(await agenda(), lang, ctxQ);
      if (ev) ctx += `\n\n### ${lang === "en" ? "Upcoming events (next 15 days)" : "Agenda des 15 prochains jours"} (${lang === "en" ? "/en/things-to-do/" : "/que-faire/"})\n${ev}`;
    }
    if (/neige|snow|meteo|weather|enneig|poudreuse|powder|temps|froid|cold|cm\b/.test(qn)) {
      const s = await snow(); if (s) ctx += `\n\n### ${lang === "en" ? "Snow forecast (model estimates, cm)" : "Prévisions de neige (estimations des modèles, cm)"} (${lang === "en" ? "/en/meteo/" : "/meteo/"})\n${s}`;
    }
    if (!ctx) ctx = lang === "en" ? "(nothing relevant on the site)" : "(rien de pertinent sur le site)";
    const messages = [{ role: "system", content: system(lang, ctx) }];
    for (const m of hist) if (m && m.t) messages.push({ role: m.r === "u" ? "user" : "assistant", content: String(m.t).slice(0, 600) });
    messages.push({ role: "user", content: q });
    const { a, model } = await groq(messages);
    redis([["INCR", `chat:ok:${d}`], ["EXPIRE", `chat:ok:${d}`, "864000"]]);
    return send(200, { ok: true, a, model, src: parts.slice(0, 3).map(c => ({ t: c.t, u: c.u })) });
  } catch (e) {
    console.error("chat", e.message);
    return send(e.fallback ? 503 : 500, { ok: false, fallback: true, error: e.fallback ? "busy" : "error" });
  }
};
