// Point d'entrée unique de toutes les API du site (le plan Hobby de Vercel limite à 12 fonctions par déploiement).
// Les adresses publiques ne changent pas : vercel.json réécrit /api/<nom> vers /api/main?fn=<nom>,
// puis on rend au gestionnaire l'URL d'origine (/api/<nom>?…) pour qu'il fonctionne exactement comme avant.
// Les gestionnaires sont dans api/_lib/ (non comptés comme fonctions). Pour ajouter une API :
//   1. créer api/_lib/<nom>.js (module.exports = async (req, res) => …),
//   2. l'ajouter ci-dessous,
//   3. ajouter <nom> à la liste de la règle « rewrites » de vercel.json.
const H = { // require paresseux : une erreur dans un module ne casse pas les autres
  compteur: () => require("./_lib/compteur.js"),
  ig: () => require("./_lib/ig.js"),
  "ig-auth": () => require("./_lib/ig.js"), // retour de Facebook (même module, branche selon l'adresse)
  neige: () => require("./_lib/neige.js"),
  newsletter: () => require("./_lib/newsletter.js"),
  propose: () => require("./_lib/propose.js"),
  push: () => require("./_lib/push.js"),
  reel: () => require("./_lib/reel.js"),
  stats: () => require("./_lib/stats.js"),
  subscribe: () => require("./_lib/subscribe.js"),
  webcam: () => require("./_lib/webcam.js"),
};

module.exports = async (req, res) => {
  const u = new URL(req.url, "http://x");
  let fn = u.searchParams.get("fn");
  if (!fn) { const m = u.pathname.match(/^\/api\/([\w-]+)\/?$/); fn = m && m[1] !== "main" ? m[1] : ""; }
  const load = H[fn];
  if (!load) { res.statusCode = 404; res.setHeader("Content-Type", "application/json; charset=utf-8"); return res.end(JSON.stringify({ ok: false, error: "api inconnue" })); }
  u.searchParams.delete("fn");
  const qs = u.searchParams.toString();
  req.url = `/api/${fn}${qs ? "?" + qs : ""}`;
  if (req.query && typeof req.query === "object") delete req.query.fn;
  return load()(req, res);
};

module.exports.HANDLERS = Object.keys(H);
