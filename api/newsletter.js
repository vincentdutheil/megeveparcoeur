// Envoi de « L'agenda de la semaine » chaque jeudi (Vercel Cron, voir vercel.json).
// /api/newsletter?preview=1  → aperçu HTML, sans envoi.
// Envoi : appelé par Vercel Cron (en-tête Authorization: Bearer CRON_SECRET) ou /api/newsletter?key=CRON_SECRET.
// Variables : BREVO_API_KEY, BREVO_LIST_ID, CRON_SECRET, SENDER_EMAIL (défaut bonjour@megeveparcoeur.fr).
const SITE = "https://www.megeveparcoeur.fr";
const MC = ["janv.","févr.","mars","avr.","mai","juin","juil.","août","sept.","oct.","nov.","déc."];
const JOURS = ["dimanche","lundi","mardi","mercredi","jeudi","vendredi","samedi"];
const COL = { "Megève": "#1f3d7a", "Combloux": "#2f5a44", "Demi-Quartier": "#5b4a86", "Praz-sur-Arly": "#8a5a24" };
const esc = s => String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
const pad = n => String(n).padStart(2, "0");
function parisToday() { const p = new Intl.DateTimeFormat("fr-CA", { timeZone: "Europe/Paris", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date()); return p; }
function add(s, k) { const d = new Date(s + "T12:00:00Z"); d.setUTCDate(d.getUTCDate() + k); return d.toISOString().slice(0, 10); }
function lab(s) { const d = new Date(s + "T12:00:00Z"); return `${JOURS[d.getUTCDay()]} ${d.getUTCDate()} ${MC[d.getUTCMonth()]}`; }
function slug(e) { return "e-" + e.d + "-" + (e.t || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 40); }

function build(agenda, start) {
  const end = add(start, 6);
  const evs = agenda.filter(e => { const a = e.d, b = e.d2 || e.d; if (b < start || a > end) return false;
      const long = (new Date(b) - new Date(a)) / 864e5 > 14; return !long || (a >= start && a <= end); })
    .sort((x, y) => (x.d < start ? start : x.d).localeCompare(y.d < start ? start : y.d) || x.t.localeCompare(y.t));
  const days = {};
  for (const e of evs) { const k = e.d < start ? start : e.d; (days[k] = days[k] || []).push(e); }
  const period = `du ${lab(start).replace(/^\S+ /, "")} au ${lab(end).replace(/^\S+ /, "")}`;
  const rows = Object.keys(days).sort().map(k => `
    <tr><td style="padding:22px 0 6px;font:700 13px/1.2 Arial,sans-serif;letter-spacing:.12em;text-transform:uppercase;color:#c8323d">${lab(k)}</td></tr>
    ${days[k].map(e => `<tr><td style="padding:6px 0">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#ffffff;border:1px solid #dbe3ee;border-radius:14px"><tr><td style="padding:14px 16px">
        <div style="font:700 16px/1.3 Arial,sans-serif;color:#1c2533">${esc(e.t)}</div>
        <div style="font:13px/1.5 Arial,sans-serif;color:#5d6878;margin-top:4px">${e.h ? `<b style="color:#1c2533">${esc(e.h)}</b> · ` : ""}${e.d2 && e.d2 !== e.d ? `jusqu'au ${lab(e.d2).replace(/^\S+ /, "")} · ` : ""}${esc(e.x)}</div>
        <div style="margin-top:8px"><span style="display:inline-block;background:${COL[e.lieu] || "#1f3d7a"};color:#fff;font:700 11px Arial,sans-serif;text-transform:uppercase;letter-spacing:.06em;border-radius:99px;padding:3px 9px">${esc(e.lieu)}</span>
        &nbsp;<a href="${SITE}/#${slug(e)}" style="font:700 13px Arial,sans-serif;color:#c8323d;text-decoration:none">Détails →</a></div>
      </td></tr></table></td></tr>`).join("")}`).join("");
  const html = `<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>L'agenda de la semaine</title></head>
<body style="margin:0;background:#f1f4f9">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f1f4f9"><tr><td align="center" style="padding:20px 12px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px">
  <tr><td style="background:#0b1c36;border-radius:20px 20px 0 0;padding:28px 26px;text-align:left">
    <img src="${SITE}/img/icon-192.png" width="56" height="56" alt="Megève par cœur" style="border-radius:12px;display:block">
    <div style="font:700 12px Arial,sans-serif;letter-spacing:.16em;text-transform:uppercase;color:#f3c27a;margin-top:16px">L'agenda de la semaine</div>
    <div style="font:28px/1.15 Georgia,serif;color:#ffffff;margin-top:6px">Megève &amp; alentours</div>
    <div style="font:15px Arial,sans-serif;color:#cfe0f7;margin-top:6px">${period} · Megève, Combloux, Demi-Quartier, Praz-sur-Arly</div>
  </td></tr>
  <tr><td style="background:#f1f4f9;padding:4px 18px 10px">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">${rows || `<tr><td style="padding:24px 0;font:15px Arial,sans-serif;color:#5d6878">Semaine calme : retrouvez les prochains rendez-vous sur le site.</td></tr>`}</table>
  </td></tr>
  <tr><td style="padding:18px 18px 4px;text-align:center">
    <a href="${SITE}/#agenda" style="display:inline-block;background:#c8323d;color:#fff;font:700 15px Arial,sans-serif;text-decoration:none;border-radius:99px;padding:13px 22px">Tout l'agenda sur megeveparcoeur.fr</a>
    <div style="font:14px Arial,sans-serif;color:#5d6878;margin-top:14px"><a href="${SITE}/meteo/" style="color:#1f3d7a">❄ Météo &amp; neige</a> · <a href="${SITE}/webcams/" style="color:#1f3d7a">📷 Webcams</a> · <a href="${SITE}/balades/" style="color:#1f3d7a">🥾 Balades</a></div>
  </td></tr>
  <tr><td style="padding:22px 18px 30px;text-align:center;font:12px/1.6 Arial,sans-serif;color:#8592a3">
    Dates sous réserve : vérifiez le lien de chaque événement avant de venir.<br>
    Vous recevez cet e-mail car vous êtes inscrit à l'agenda de Megève par cœur · <a href="https://www.instagram.com/megeveparcoeur/" style="color:#8592a3">@megeveparcoeur</a><br>
    <a href="{{ unsubscribe }}" style="color:#8592a3">Se désinscrire</a>
  </td></tr>
</table></td></tr></table></body></html>`;
  return { html, subject: `📅 Cette semaine à Megève & alentours (${period})`, count: evs.length };
}

module.exports = async (req, res) => {
  const url = new URL(req.url, SITE);
  const r = await fetch(SITE + "/data/agenda.json", { cache: "no-store" });
  const agenda = await r.json();
  let start = parisToday();
  if (url.searchParams.get("start")) start = url.searchParams.get("start");
  const mail = build(agenda, start);
  if (url.searchParams.get("preview")) { res.setHeader("Content-Type", "text/html; charset=utf-8"); return res.end(mail.html.replace("{{ unsubscribe }}", "#")); }
  const secret = process.env.CRON_SECRET, auth = req.headers.authorization || "";
  if (!secret || (auth !== "Bearer " + secret && url.searchParams.get("key") !== secret)) { res.statusCode = 401; return res.end("unauthorized"); }
  const key = process.env.BREVO_API_KEY, list = Number(process.env.BREVO_LIST_ID);
  if (!key || !list) { res.statusCode = 503; return res.end("not configured"); }
  if (!mail.count) return res.end("no events this week");
  const H = { "api-key": key, "Content-Type": "application/json", accept: "application/json" };
  const c = await fetch("https://api.brevo.com/v3/emailCampaigns", { method: "POST", headers: H, body: JSON.stringify({
    name: "Agenda " + start, subject: mail.subject, sender: { name: "Megève par cœur", email: process.env.SENDER_EMAIL || "bonjour@megeveparcoeur.fr" },
    htmlContent: mail.html, recipients: { listIds: [list] }, inlineImageActivation: false }) });
  if (!c.ok) { res.statusCode = 502; return res.end("create failed: " + (await c.text()).slice(0, 300)); }
  const { id } = await c.json();
  const s = await fetch(`https://api.brevo.com/v3/emailCampaigns/${id}/sendNow`, { method: "POST", headers: H });
  if (!s.ok && s.status !== 204) { res.statusCode = 502; return res.end("send failed: " + (await s.text()).slice(0, 300)); }
  res.end("sent campaign " + id + " (" + mail.count + " events)");
};
module.exports.build = build;
