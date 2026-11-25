// Inscription à « L'agenda de la semaine » (Brevo).
// Variables d'environnement Vercel : BREVO_API_KEY, BREVO_LIST_ID, et facultatif BREVO_DOI_TEMPLATE_ID (double opt-in).
module.exports = async (req, res) => {
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  const key = process.env.BREVO_API_KEY, list = Number(process.env.BREVO_LIST_ID), doi = Number(process.env.BREVO_DOI_TEMPLATE_ID || 0);
  if (req.method === "GET") {   // diagnostic : la configuration est-elle présente ? (aucune valeur secrète affichée)
    let brevo = null;
    if (key) { try { const r = await fetch("https://api.brevo.com/v3/contacts/lists/" + list, { headers: { "api-key": key, accept: "application/json" } }); brevo = r.status; } catch (e) { brevo = "network"; } }
    return res.end(JSON.stringify({ key: !!key, list: list || null, doi: !!doi, brevoListStatus: brevo }));
  }
  if (req.method !== "POST") { res.statusCode = 405; return res.end(JSON.stringify({ ok: false, error: "method" })); }
  if (!key || !list) { res.statusCode = 503; return res.end(JSON.stringify({ ok: false, error: "not_configured" })); }
  let body = req.body;
  if (typeof body === "string") { try { body = JSON.parse(body); } catch (e) { body = {}; } }
  body = body || {};
  const email = String(body.email || "").trim().toLowerCase();
  const lang = body.lang === "en" ? "en" : "fr";
  if (body.website) { return res.end(JSON.stringify({ ok: true })); }          // piège à robots
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email) || email.length > 200) { res.statusCode = 400; return res.end(JSON.stringify({ ok: false, error: "email" })); }
  if (body.consent !== true) { res.statusCode = 400; return res.end(JSON.stringify({ ok: false, error: "consent" })); }
  const H = { "api-key": key, "Content-Type": "application/json", accept: "application/json" };
  try {
    let r;
    if (doi) {
      r = await fetch("https://api.brevo.com/v3/contacts/doubleOptinConfirmation", { method: "POST", headers: H,
        body: JSON.stringify({ email, includeListIds: [list], templateId: doi, redirectionUrl: "https://www.megeveparcoeur.fr/merci/" + (lang === "en" ? "?lang=en" : ""), attributes: { LANG: lang } }) });
    } else {
      r = await fetch("https://api.brevo.com/v3/contacts", { method: "POST", headers: H,
        body: JSON.stringify({ email, listIds: [list], updateEnabled: true, attributes: { LANG: lang } }) });
    }
    if (r.ok || r.status === 204) return res.end(JSON.stringify({ ok: true, doi: !!doi }));
    const t = await r.text();
    if (/duplicate|already/i.test(t)) return res.end(JSON.stringify({ ok: true, already: true }));
    res.statusCode = 502; return res.end(JSON.stringify({ ok: false, error: "brevo" }));
  } catch (e) { res.statusCode = 502; return res.end(JSON.stringify({ ok: false, error: "network" })); }
};
