// Envoi de « L'agenda de la semaine » chaque jeudi (Vercel Cron, voir vercel.json).
// /api/newsletter?preview=1  → aperçu HTML, sans envoi.
// Envoi : appelé par Vercel Cron (en-tête Authorization: Bearer CRON_SECRET) ou /api/newsletter?key=CRON_SECRET.
// Inclut un point météo & neige (Open-Meteo) ; si l'API ne répond pas, l'e-mail part sans.
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

// ---- Point météo & neige (Open-Meteo, mêmes données que la page /meteo/) ----
const VIL = [
  { n: "Megève", lat: 45.8567, lon: 6.6175, v: 1113, a: 1850 },
  { n: "Combloux", lat: 45.8966, lon: 6.6417, v: 1000, a: 1850 },
  { n: "Demi-Quartier", lat: 45.8760, lon: 6.6260, v: 1050, a: 1830 },
  { n: "Praz-sur-Arly", lat: 45.8375, lon: 6.5719, v: 1036, a: 1830 }
];
const WI = c => c === 0 ? "☀️" : c <= 2 ? "🌤️" : c === 3 ? "☁️" : c <= 48 ? "🌫️" : c <= 67 ? "🌧️" : c <= 77 ? "🌨️" : c <= 82 ? "🌦️" : c <= 86 ? "🌨️" : "⛈️";
async function meteoZone(z) {
  const q = new URLSearchParams({
    latitude: VIL.map(v => v.lat).join(","), longitude: VIL.map(v => v.lon).join(","), elevation: VIL.map(v => z === "v" ? v.v : v.a).join(","),
    current: "temperature_2m,weather_code", hourly: "snow_depth",
    daily: "weather_code,temperature_2m_max,temperature_2m_min,snowfall_sum", timezone: "Europe/Paris", forecast_days: "7"
  });
  const r = await fetch("https://api.open-meteo.com/v1/forecast?" + q, { signal: AbortSignal.timeout(8000) });
  if (!r.ok) throw new Error("open-meteo " + r.status);
  let d = await r.json(); if (!Array.isArray(d)) d = [d];
  return d.map(x => {
    const H = x.hourly, i = Math.max(0, H.time.findIndex(t => t.slice(0, 13) === x.current.time.slice(0, 13)));
    const D = x.daily;
    return { depth: Math.round((H.snow_depth[i] || 0) * 100), temp: Math.round(x.current.temperature_2m),
      week: D.snowfall_sum.reduce((a, b) => a + (b || 0), 0),
      days: D.time.map((t, k) => ({ t, c: D.weather_code[k], mx: Math.round(D.temperature_2m_max[k]), mn: Math.round(D.temperature_2m_min[k]), sn: D.snowfall_sum[k] || 0 })) };
  });
}
async function meteo() {
  try { const [v, a] = await Promise.all([meteoZone("v"), meteoZone("a")]); return { v, a }; }
  catch (e) { return null; } // pas de météo : la newsletter part quand même
}
const cm = x => x >= 10 ? Math.round(x) : Math.round(x * 10) / 10;
function meteoBlock(M) {
  if (!M) return "";
  // prochaine chute de neige notable (en altitude)
  let best = null;
  M.a.forEach((s, i) => s.days.forEach((x, k) => { if (x.sn >= 1 && (!best || k < best.k || (k === best.k && x.sn > best.sn))) best = { k, sn: x.sn, t: x.t }; }));
  const maxWeek = Math.max(...M.a.map(s => s.week)), maxWeekV = Math.max(...M.v.map(s => s.week));
  const head = best
    ? `❄️ ${best.k === 0 ? "Il neige aujourd'hui" : best.k === 1 ? "De la neige attendue demain" : "Prochaine neige : " + lab(best.t).replace(/ \d.*$/, "")} · jusqu'à ${cm(maxWeek)} cm cumulés sur 7 jours en altitude${maxWeekV >= 1 ? `, ${cm(maxWeekV)} cm au village` : ""}.`
    : "☀️ Pas de chute de neige prévue cette semaine.";
  const td = "padding:8px 6px;font:13px Arial,sans-serif;color:#1c2533;border-top:1px solid #e6ecf4";
  const rows = VIL.map((v, i) => `<tr>
      <td style="${td};font-weight:700">${v.n}</td>
      <td style="${td};text-align:center">${M.v[i].temp}°</td>
      <td style="${td};text-align:center">${M.v[i].depth} cm</td>
      <td style="${td};text-align:center">${M.a[i].depth} cm</td>
      <td style="${td};text-align:center;font-weight:700;color:#1f3d7a">${cm(M.a[i].week)} cm</td></tr>`).join("");
  const th = "padding:6px;font:700 10px Arial,sans-serif;letter-spacing:.06em;text-transform:uppercase;color:#8592a3";
  const strip = M.v[0].days.map((x, k) => `<td align="center" style="padding:8px 2px;font:12px Arial,sans-serif;color:#5d6878">
      <div style="font-weight:700;color:#1c2533">${k === 0 ? "Auj." : JOURS[new Date(x.t + "T12:00:00Z").getUTCDay()].slice(0, 3) + "."}</div>
      <div style="font-size:20px;line-height:28px">${WI(x.c)}</div>
      <div><b style="color:#1c2533">${x.mx}°</b> ${x.mn}°</div>
      <div style="color:#1f3d7a;font-weight:700;height:16px">${M.a[0].days[k].sn >= 0.5 ? "❄ " + cm(M.a[0].days[k].sn) : ""}</div></td>`).join("");
  return `<tr><td style="padding:16px 18px 0">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#ffffff;border:1px solid #dbe3ee;border-radius:16px"><tr><td style="padding:16px 16px 12px">
      <div style="font:700 13px/1.2 Arial,sans-serif;letter-spacing:.12em;text-transform:uppercase;color:#c8323d">Le point météo &amp; neige</div>
      <div style="font:600 16px/1.4 Arial,sans-serif;color:#1c2533;margin:8px 0 10px">${head}</div>
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
        <tr><td style="${th}"></td><td style="${th};text-align:center">Temp.</td><td style="${th};text-align:center">Neige au village</td><td style="${th};text-align:center">Neige en altitude</td><td style="${th};text-align:center">À venir 7 j</td></tr>
        ${rows}
      </table>
      <div style="font:700 11px Arial,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:#8592a3;margin-top:14px">Les 7 jours à Megève (❄ = cm de neige en altitude)</div>
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>${strip}</tr></table>
      <div style="font:12px/1.5 Arial,sans-serif;color:#8592a3;margin-top:6px">Estimations des modèles météo (Open-Meteo), au moment de l'envoi. <a href="${SITE}/meteo/" style="color:#1f3d7a;font-weight:700">Prévisions à jour →</a></div>
    </td></tr></table></td></tr>`;
}

function build(agenda, start, M) {
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
  ${meteoBlock(M)}
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
  const mail = build(agenda, start, await meteo());
  if (url.searchParams.get("preview")) { res.setHeader("Content-Type", "text/html; charset=utf-8"); return res.end(mail.html.replace("{{ unsubscribe }}", "#")); }
  const secret = process.env.CRON_SECRET, auth = req.headers.authorization || "";
  if (!secret || (auth !== "Bearer " + secret && url.searchParams.get("key") !== secret)) { res.statusCode = 401; return res.end("unauthorized"); }
  const key = process.env.BREVO_API_KEY, list = Number(process.env.BREVO_LIST_ID);
  if (!key || !list) { res.statusCode = 503; return res.end("not configured"); }
  if (!mail.count) return res.end("no events this week");
  const H = { "api-key": key, "Content-Type": "application/json", accept: "application/json" };
  const c = await fetch("https://api.brevo.com/v3/emailCampaigns", { method: "POST", headers: H, body: JSON.stringify({
    name: "Agenda " + start, subject: mail.subject, sender: { name: "Megève par cœur", email: process.env.SENDER_EMAIL || "bonjour@megeveparcoeur.fr" },
    htmlContent: mail.html, recipients: { listIds: [list] }, inlineImageActivation: false,
    replyTo: process.env.SENDER_EMAIL || "bonjour@megeveparcoeur.fr",
    previewText: "Marchés, spectacles, sorties en famille, et le point météo & neige : tout ce qui se passe cette semaine à Megève, Combloux, Demi-Quartier et Praz." }) });
  if (!c.ok) { res.statusCode = 502; return res.end("create failed: " + (await c.text()).slice(0, 300)); }
  const { id } = await c.json();
  const s = await fetch(`https://api.brevo.com/v3/emailCampaigns/${id}/sendNow`, { method: "POST", headers: H });
  if (!s.ok && s.status !== 204) { res.statusCode = 502; return res.end("send failed: " + (await s.text()).slice(0, 300)); }
  res.end("sent campaign " + id + " (" + mail.count + " events)");
};
module.exports.build = build;
