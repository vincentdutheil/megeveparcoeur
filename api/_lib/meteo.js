// Relais météo : GET /api/meteo?<mêmes paramètres que https://api.open-meteo.com/v1/forecast>
// Renvoie la réponse Open-Meteo telle quelle (même JSON), mais interrogée depuis Vercel.
// Pourquoi : les scripts des tâches automatiques tournent dans le cloud sur une adresse IP partagée,
// dont le quota quotidien Open-Meteo est souvent épuisé (erreur 429). Depuis Vercel, pas ce problème.
// Pour ne pas servir de relais ouvert : paramètres autorisés seulement, coordonnées limitées au pays du Mont-Blanc.
const ALLOWED = new Set(["latitude", "longitude", "elevation", "current", "hourly", "daily", "forecast_days",
  "past_days", "start_date", "end_date", "timezone", "models"]);
const inBox = (s, min, max) => String(s).split(",").every(v => { const n = Number(v); return v !== "" && n >= min && n <= max; });

module.exports = async function handler(req, res) {
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  try {
    const u = new URL(req.url, "http://x");
    const q = new URLSearchParams();
    for (const [k, v] of u.searchParams) {
      if (!ALLOWED.has(k)) return res.status(400).end(JSON.stringify({ error: true, reason: "paramètre non autorisé : " + k }));
      if (v.length > 400) return res.status(400).end(JSON.stringify({ error: true, reason: "paramètre trop long : " + k }));
      q.set(k, v);
    }
    const lat = q.get("latitude"), lon = q.get("longitude");
    if (!lat || !lon || !inBox(lat, 45.4, 46.4) || !inBox(lon, 6.0, 7.3) || lat.split(",").length > 20)
      return res.status(400).end(JSON.stringify({ error: true, reason: "coordonnées hors zone (Megève et environs)" }));
    const r = await fetch("https://api.open-meteo.com/v1/forecast?" + q.toString(), { signal: AbortSignal.timeout(15000) });
    const body = await r.text();
    if (r.ok) res.setHeader("Cache-Control", "public, s-maxage=600, stale-while-revalidate=1800");
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.status(r.status).end(body);
  } catch (e) {
    res.status(502).end(JSON.stringify({ error: true, reason: "open-meteo injoignable : " + String(e.message || e) }));
  }
};
