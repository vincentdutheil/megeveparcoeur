// Prévisions de neige pour les visuels Instagram (et la rubrique météo du samedi).
// GET /api/neige -> { maj, du, au, stations:[{nom, sol, prevu, jours:[…]}], megeve:{jours:[{date,tmin,tmax,code,neige}]} }
// Données Open-Meteo (gratuites, sans clé), interrogées côté serveur ; réponse mise en cache 30 min.
const P = [
  ["Megève", 45.857, 6.617, 1500], ["Combloux", 45.893, 6.640, 1400], ["Praz-sur-Arly", 45.837, 6.571, 1400],
  ["Demi-Quartier", 45.875, 6.632, 1350], ["Cordon", 45.920, 6.600, 1300], ["Saint-Gervais", 45.910, 6.690, 1500],
  ["Les Houches", 45.892, 6.800, 1500], ["Les Contamines", 45.812, 6.727, 1600], ["La Giettaz", 45.858, 6.495, 1400],
  ["N.-D.-de-Bellecombe", 45.800, 6.520, 1500], ["Les Saisies", 45.762, 6.531, 1650], ["La Clusaz", 45.903, 6.424, 1600],
  ["Chamonix", 45.923, 6.870, 1800],
];

module.exports = async function handler(req, res) {
  try {
    const q = (i) => P.map(p => p[i]).join(",");
    const u = `https://api.open-meteo.com/v1/forecast?latitude=${q(1)}&longitude=${q(2)}&elevation=${q(3)}`
      + `&current=snow_depth&daily=snowfall_sum,temperature_2m_max,temperature_2m_min,weather_code&forecast_days=7&timezone=Europe%2FParis`;
    const r = await fetch(u);
    if (!r.ok) throw new Error("open-meteo " + r.status);
    const all = await r.json();
    const list = Array.isArray(all) ? all : [all];
    const stations = list.map((x, i) => ({
      nom: P[i][0], altitude: P[i][3],
      sol: Math.round((x.current?.snow_depth || 0) * 100),
      prevu: Math.round(x.daily.snowfall_sum.reduce((a, b) => a + (b || 0), 0)),
      jours: x.daily.time.map((d, k) => ({ date: d, neige: Math.round((x.daily.snowfall_sum[k] || 0) * 10) / 10 })),
    })).sort((a, b) => b.prevu - a.prevu);
    const m = list[0].daily;
    res.setHeader("Cache-Control", "public, s-maxage=900, stale-while-revalidate=900"); // jamais plus vieux que 30 min
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.status(200).json({
      maj: new Date().toISOString(), du: m.time[0], au: m.time[m.time.length - 1],
      source: "Open-Meteo (neige au sol estimée par le modèle, cumul de chutes prévu sur 7 jours)",
      stations,
      megeve: { jours: m.time.map((d, k) => ({ date: d, tmin: m.temperature_2m_min[k], tmax: m.temperature_2m_max[k], code: m.weather_code[k], neige: m.snowfall_sum[k] })) },
    });
  } catch (e) {
    res.status(502).json({ erreur: String(e.message || e) });
  }
}
