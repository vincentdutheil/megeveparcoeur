// Dernière image d'une webcam Skaping, servie depuis notre domaine pour que la page Webcams
// puisse la dessiner dans le visuel « story Instagram » (le navigateur refuse de copier une image d'un autre site).
//   GET /api/webcam?c=village|rochebrune|mont-d-arbois|cote-2000|combloux|jaillet
//   → l'image JPEG ; en-tête X-Shot = heure de la prise de vue (AAAA-MM-JJTHH:MM, heure de Paris)
// Seules les six webcams de la liste sont acceptées (pas de proxy ouvert). Réponse mise en cache 10 min.
const CAMS = {
  "village": "megeve/village",
  "rochebrune": "megeve/rochebrune",
  "mont-d-arbois": "megeve/mont-d-arbois",
  "cote-2000": "megeve/cote-2000",
  "combloux": "combloux/sommet",
  "jaillet": "jaillet/sommet",
};
const UA = "Mozilla/5.0 (compatible; megeveparcoeur.fr)";

module.exports = async function handler(req, res) {
  const path = CAMS[String(req.query.c || "")];
  if (!path) return res.status(404).json({ erreur: "webcam inconnue" });
  try {
    const page = await fetch("https://www.skaping.com/" + path, { headers: { "User-Agent": UA } });
    if (!page.ok) throw new Error("skaping " + page.status);
    const html = await page.text();
    const m = html.match(/<meta[^>]+property=["']og:image["'][^>]*content=["']([^"']+)["']/i)
           || html.match(/<meta[^>]+content=["']([^"']+)["'][^>]*property=["']og:image["']/i);
    if (!m) throw new Error("image introuvable");
    const src = new URL(m[1].replace(/&amp;/g, "&"));
    if (src.protocol !== "https:" || !/(^|\.)skaping\.com$|\.cloud\.ovh\.net$/.test(src.hostname)) throw new Error("adresse d'image inattendue");
    const img = await fetch(src, { headers: { "User-Agent": UA } });
    if (!img.ok) throw new Error("image " + img.status);
    const buf = Buffer.from(await img.arrayBuffer());
    const t = src.pathname.match(/(\d{4})\/(\d{2})\/(\d{2})\/[^/]+\/(\d{2})-(\d{2})/);
    if (t) res.setHeader("X-Shot", `${t[1]}-${t[2]}-${t[3]}T${t[4]}:${t[5]}`);
    res.setHeader("Content-Type", img.headers.get("content-type") || "image/jpeg");
    res.setHeader("Cache-Control", "public, s-maxage=600, stale-while-revalidate=1200");
    res.status(200).send(buf);
  } catch (e) {
    res.setHeader("Cache-Control", "no-store");
    res.status(502).json({ erreur: String(e.message || e) });
  }
};
