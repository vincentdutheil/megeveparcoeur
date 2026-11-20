// Build Vercel : copie le site dans dist/ puis
//  1. crée une page par événement (/agenda/<slug>/ et /en/agenda/<slug>/) à partir de data/agenda.json,
//  2. écrit la liste de l'agenda directement dans le HTML (accueil FR/EN et pages « Que faire »),
//     pour que Google la lise sans exécuter de JavaScript (le script la remplace ensuite à l'identique),
//  3. ajoute les pages d'événements au sitemap.
// Lancé automatiquement par Vercel à chaque déploiement (vercel.json → buildCommand).
// Si ce script échoue, Vercel garde le déploiement précédent : le site reste en ligne.
// Test local : node tools/build.mjs && (cd dist && python3 -m http.server 8765)
import fs from "node:fs";
import path from "node:path";

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const OUT = path.join(ROOT, "dist");
const SITE = "https://www.megeveparcoeur.fr";
const SKIP = new Set([".git", "dist", "tools", "node_modules", ".vercel"]);

// ------------------------------------------------------------------ copie
fs.rmSync(OUT, { recursive: true, force: true });
fs.mkdirSync(OUT);
for (const f of fs.readdirSync(ROOT)) {
  if (SKIP.has(f) || f.startsWith(".")) continue;
  fs.cpSync(path.join(ROOT, f), path.join(OUT, f), { recursive: true });
}
const read = p => fs.readFileSync(path.join(OUT, p), "utf8");
const write = (p, s) => { const f = path.join(OUT, p); fs.mkdirSync(path.dirname(f), { recursive: true }); fs.writeFileSync(f, s); };

// ------------------------------------------------------------------ logique agenda (même règles que assets/agenda.js)
const A = JSON.parse(read("data/agenda.json"));
const pad = n => String(n).padStart(2, "0");
const TODAY = new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/Paris" }).format(new Date()); // AAAA-MM-JJ
const addDays = (s, k) => { const d = new Date(s + "T12:00:00Z"); d.setUTCDate(d.getUTCDate() + k); return d.toISOString().slice(0, 10); };
const wday = s => new Date(s + "T12:00:00Z").getUTCDay();
const strip = s => String(s || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
const slug = e => "e-" + e.d + "-" + strip(e.t).slice(0, 40);
// adresse de la page d'un événement : date + titre, et le village en cas de doublon
const cut = s => s.length <= 60 ? s : s.slice(0, 60).replace(/-[^-]*$/, "");
const pbase = e => e.d + "-" + cut(strip(e.t));
const counts = {}; A.forEach(e => { const k = pbase(e); counts[k] = (counts[k] || 0) + 1; });
const pslug = e => pbase(e) + (counts[pbase(e)] > 1 ? "-" + strip(e.lieu) : "");
const esc = s => String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");
const txt = e => ((e.t || "") + " " + (e.x || "")).toLowerCase();
const isFree = e => e.free === true || (e.free !== false && /gratuit|entr[ée]e libre|acc[eè]s libre|\bfree\b/.test(txt(e)) && !/payant/.test(txt(e)));
const isKids = e => e.kids === true || (e.kids !== false && (e.cat === "Famille" || /enfant|famille|b[ée]b[ée]|conte|guignol|p[èe]re no[ëe]l|lutin|jeunesse|kids|ludique|chasse au/.test(txt(e))));
const isRain = e => e.indoor === true || (e.indoor !== false && e.cat !== "Ski" && (["Expo", "Spectacle"].includes(e.cat) || /salle|palais|m[ée]diath[eè]que|mus[ée]e|[ée]glise|cin[ée]ma|th[ée][âa]tre|auditorium|chapelle|biblioth[eè]que|escape|atelier|conf[ée]rence|projection|patinoire|galerie|int[ée]rieur/.test(txt(e))));
const overlaps = (e, a, b) => e.d <= b && (e.d2 || e.d) >= a;
function weekend() { const t = TODAY, wd = wday(t); if (wd === 6) return [t, addDays(t, 1)]; if (wd === 0) return [t, t]; const sat = addDays(t, 6 - wd); return [addDays(sat, -1), addDays(sat, 1)]; }
function filtered(q) {
  return A.filter(e => (e.d2 || e.d) >= TODAY && (
    q === "today" ? overlaps(e, TODAY, TODAY) : q === "we" ? overlaps(e, ...weekend()) :
    q === "free" ? isFree(e) : q === "kids" ? isKids(e) : q === "rain" ? isRain(e) : true))
    .sort((x, y) => (x.always ? 1 : 0) - (y.always ? 1 : 0) || x.d.localeCompare(y.d));
}
const CP = { "Megève": "74120", "Demi-Quartier": "74120", "Praz-sur-Arly": "74120", "Combloux": "74920" };
const T = {
  fr: { months: ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"],
        mc: ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."],
        days: ["dim.", "lun.", "mar.", "mer.", "jeu.", "ven.", "sam."], dl: ["dimanche", "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi"],
        season: "Toute la saison", until: "Jusqu'au", to: "au", more: "Plus d'infos ↗", free: "Gratuit", kids: "Enfants", home: "/" },
  en: { months: ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
        mc: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        days: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"], dl: ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
        season: "All season", until: "Until", to: "to", more: "More info ↗", free: "Free", kids: "Kids", home: "/en/" }
};
const parts = s => { const [y, m, d] = s.split("-").map(Number); return { y, m, d }; };
function dLabel(e, L) {
  const t = T[L], a = parts(e.d);
  if (!e.d2 || e.d2 === e.d) return { big: `${a.d} ${t.mc[a.m - 1]}`, small: t.days[wday(e.d)] + " " + a.y };
  const b = parts(e.d2);
  if (e.always) return { big: t.until, small: `${b.d} ${t.mc[b.m - 1]} ${b.y}` };
  if (a.m === b.m && a.y === b.y) return { big: `${a.d}–${b.d} ${t.mc[a.m - 1]}`, small: String(a.y) };
  return { big: `${a.d} ${t.mc[a.m - 1]}`, small: `${t.to} ${b.d} ${t.mc[b.m - 1]} ${b.y}` };
}
const longDate = (s, L) => { const p = parts(s), t = T[L]; return L === "fr" ? `${t.dl[wday(s)]} ${p.d} ${t.months[p.m - 1]} ${p.y}` : `${t.dl[wday(s)]} ${p.d} ${t.months[p.m - 1]} ${p.y}`; };
function whenText(e, L) {
  if (e.always) return (L === "fr" ? "Toute la saison, jusqu'au " : "All season, until ") + longDate(e.d2, L);
  if (!e.d2 || e.d2 === e.d) return longDate(e.d, L);
  return (L === "fr" ? "Du " : "From ") + longDate(e.d, L) + (L === "fr" ? " au " : " to ") + longDate(e.d2, L);
}
const title = (e, L) => L === "en" && e.t_en ? e.t_en : e.t;
const desc = (e, L) => L === "en" && e.x_en ? e.x_en : e.x;
const evUrl = (e, L) => (L === "en" ? "/en" : "") + "/agenda/" + pslug(e) + "/";
const hhmm = h => { if (!h) return null; const m = String(h).match(/(\d{1,2})\s*h\s*(\d{2})?/i); return m ? [pad(+m[1]), m[2] || "00"] : null; };
function ld(e, L) {
  const hm = hhmm(e.h), one = !e.d2 || e.d2 === e.d;
  const o = { "@context": "https://schema.org", "@type": "Event", name: title(e, L), description: desc(e, L) || title(e, L),
    startDate: hm && one ? `${e.d}T${hm[0]}:${hm[1]}` : e.d, endDate: e.d2 || e.d,
    eventStatus: "https://schema.org/EventScheduled", eventAttendanceMode: "https://schema.org/OfflineEventAttendanceMode",
    location: { "@type": "Place", name: e.lieu, address: { "@type": "PostalAddress", addressLocality: e.lieu, postalCode: CP[e.lieu] || "", addressRegion: "Haute-Savoie", addressCountry: "FR" } },
    image: [SITE + "/videos/hero-poster.jpg"], url: SITE + evUrl(e, L), inLanguage: L };
  if (isFree(e)) o.isAccessibleForFree = true;
  if (e.u) o.sameAs = e.u;
  return o;
}
const ldScript = (o, id) => `<script type="application/ld+json"${id ? ` id="${id}"` : ""}>${JSON.stringify(o).replace(/</g, "\\u003c")}</script>`;

// ------------------------------------------------------------------ liste pré-rendue (même balisage que assets/agenda.js, sans les boutons)
function listHtml(list, L) {
  let html = "", cur = "";
  for (const e of list) {
    const a = parts(e.d), key = e.always ? T[L].season : `${T[L].months[a.m - 1]} ${a.y}`;
    if (key !== cur) { cur = key; html += `<h3 class="month">${key.charAt(0).toUpperCase() + key.slice(1)}</h3>`; }
    const D = dLabel(e, L), tags = [isFree(e) ? T[L].free : "", isKids(e) ? T[L].kids : ""].filter(Boolean);
    html += `<article class="ev" id="${slug(e)}"><div class="date"><b>${D.big}</b><span>${D.small}</span></div>` +
      `<div><h3><a href="${evUrl(e, L)}">${esc(title(e, L))}</a></h3><p>${e.h ? `<span class="hour">${esc(e.h)} · </span>` : ""}${esc(desc(e, L))}</p>` +
      `<div class="acts">${tags.map(x => `<span class="tg">${x}</span>`).join("")}</div></div>` +
      `<div class="meta"><span class="place ${esc(e.lieu)}">${esc(e.lieu)}</span>${e.u ? `<a class="more" href="${esc(e.u)}" target="_blank" rel="noopener">${T[L].more}</a>` : ""}</div></article>`;
  }
  return html;
}
function inject(file, L, q) {
  let h = read(file);
  const list = filtered(q || "all");
  const re = /(<div class="agenda" id="agenda-list"[^>]*>)[\s\S]*?(<\/div>)/;
  if (!re.test(h)) throw new Error("liste d'agenda introuvable dans " + file);
  h = h.replace(re, (m, a, b) => a + listHtml(list, L) + b);
  h = h.replace("</head>", ldScript(list.slice(0, 300).map(e => ld(e, L)), "ld-events") + "\n</head>");
  write(file, h);
}
inject("index.html", "fr"); inject("en/index.html", "en");
for (const [q, fr, en] of [["we", "ce-week-end", "this-weekend"], ["today", "aujourd-hui", "today"], ["kids", "avec-des-enfants", "with-kids"], ["rain", "quand-il-pleut", "rainy-day"], ["free", "gratuit", "free"]]) {
  inject(`que-faire/${fr}/index.html`, "fr", q); inject(`en/things-to-do/${en}/index.html`, "en", q);
}

// ------------------------------------------------------------------ pages d'événements
const tpl = { fr: read("venir/index.html"), en: read("en/getting-here/index.html") };
const piece = (h, re) => { const m = h.match(re); if (!m) throw new Error("gabarit : " + re); return m[0]; };
const SHELL = {};
for (const L of ["fr", "en"]) {
  const h = tpl[L];
  SHELL[L] = { header: piece(h, /<header class="top">[\s\S]*?<\/header>/), scene: piece(h, /<svg class="scene"[\s\S]*?<\/svg>/),
    peaks: piece(h, /<svg class="foot-peaks"[\s\S]*?<\/svg>/), footer: piece(h, /<footer>[\s\S]*?<\/footer>/), fonts: piece(h, /<link rel="preconnect"[\s\S]*?rel="stylesheet">/) };
}
const W = {
  fr: { when: "Quand", time: "Horaire", where: "Où", price: "Tarif", free: "Gratuit", kids: "Idéal avec des enfants", info: "Plus d'infos &amp; réservation ↗",
        gcal: "📅 Ajouter à Google Agenda", wa: "💬 Envoyer sur WhatsApp", all: "← Tout l'agenda", also: v => `À venir aussi à ${v}`, near: "À venir dans les villages voisins",
        past: "Cet événement est terminé. Voici les prochains rendez-vous.", check: "Dates et horaires sous réserve : vérifiez sur le site de l'organisateur avant de venir.",
        meteo: "❄️ La météo &amp; la neige à", crumbs: ["Accueil", "Agenda"], suffix: "Megève par cœur", agendaUrl: "/#agenda", meteoUrl: "/meteo/",
        metaT: (e, w) => `${title(e, "fr")} · ${w} · ${e.lieu}`, venir: ["/venir/", "🚗 Venir &amp; se garer"] },
  en: { when: "When", time: "Time", where: "Where", price: "Price", free: "Free", kids: "Great with kids", info: "More info &amp; booking ↗",
        gcal: "📅 Add to Google Calendar", wa: "💬 Send on WhatsApp", all: "← All events", also: v => `Also coming up in ${v}`, near: "Coming up in the nearby villages",
        past: "This event is over. Here are the next ones.", check: "Dates and times may change: please check the organiser's website before you go.",
        meteo: "❄️ Snow &amp; weather in", crumbs: ["Home", "What's on"], suffix: "Megève par cœur", agendaUrl: "/en/#agenda", meteoUrl: "/en/meteo/",
        metaT: (e, w) => `${title(e, "en")} · ${w} · ${e.lieu}`, venir: ["/en/getting-here/", "🚗 Getting here &amp; parking"] }
};
const upcoming = A.filter(e => (e.d2 || e.d) >= TODAY).sort((x, y) => (x.always ? 1 : 0) - (y.always ? 1 : 0) || x.d.localeCompare(y.d));
function miniList(list, L) {
  return `<ul class="mini">${list.map(e => { const D = dLabel(e, L); return `<li><a href="${evUrl(e, L)}"><span class="md"><b>${D.big}</b> ${D.small}</span><span class="mt">${esc(title(e, L))}</span><span class="place ${esc(e.lieu)}">${esc(e.lieu)}</span></a></li>`; }).join("")}</ul>`;
}
const CSS = `<link rel="stylesheet" href="/assets/agenda.css"><style>
.box{background:var(--card);border:1px solid var(--line);border-radius:22px;padding:22px 24px;box-shadow:0 8px 24px rgba(10,20,40,.06);margin:0 0 20px}
.box h2{font-size:1.4rem;margin-bottom:10px}.lift{margin-top:-40px;position:relative;z-index:4}
.crumbs{font-size:.85rem;margin:0 0 10px;opacity:.85}.crumbs a{color:inherit}
.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:0 0 18px}
.facts div{background:var(--wool);border-radius:14px;padding:10px 14px}.facts small{display:block;font-size:.72rem;font-weight:800;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}
.facts b{font-size:1rem}.lead{font-size:1.08rem;line-height:1.6;margin:0 0 16px}
.btns{display:flex;flex-wrap:wrap;gap:10px;margin:6px 0 4px}.btns a{text-decoration:none;font-weight:800;font-size:.92rem;border-radius:999px;padding:10px 16px;border:1.5px solid var(--line);background:var(--card);color:var(--ink)}
.btns a.main{background:var(--heart);border-color:var(--heart);color:#fff}.btns a:hover{border-color:var(--heart)}
.tg{display:inline-block;font-size:.78rem;font-weight:800;border-radius:999px;padding:4px 10px;background:var(--wool);margin:0 6px 10px 0}
.past{background:#fff4e5;border:1px solid #f3c27a;border-radius:14px;padding:10px 14px;margin:0 0 16px;font-weight:700}
.mini{list-style:none;margin:0;padding:0}.mini li{border-top:1px solid var(--line)}.mini li:first-child{border-top:0}
.mini a{display:grid;grid-template-columns:150px 1fr auto;gap:12px;align-items:center;padding:10px 2px;text-decoration:none;color:var(--ink)}
.mini a:hover .mt{color:var(--heart)}.mini .md{font-size:.85rem;color:var(--muted)}.mini .md b{color:var(--ember)}.mini .mt{font-weight:700}
@media(max-width:600px){.mini a{grid-template-columns:1fr auto}.mini .md{grid-column:1/-1}}
.note{color:var(--muted);font-size:.88rem}
</style>`;
function eventPage(e, L) {
  const w = W[L], S = SHELL[L], other = L === "fr" ? "en" : "fr";
  const D = dLabel(e, L), dateShort = `${D.big} ${D.small}`.replace(/\s+/g, " ");
  const url = evUrl(e, L), frU = evUrl(e, "fr"), enU = evUrl(e, "en");
  const metaTitle = esc(w.metaT(e, dateShort)) + " | " + w.suffix;
  const d = desc(e, L) || "";
  const metaDesc = esc((d.length > 150 ? d.slice(0, 147).replace(/\s+\S*$/, "") + "…" : d) || title(e, L));
  const ended = (e.d2 || e.d) < TODAY;
  const hm = hhmm(e.h), one = !e.d2 || e.d2 === e.d;
  const dates = hm && one ? `${e.d.replace(/-/g, "")}T${hm[0]}${hm[1]}00/${e.d.replace(/-/g, "")}T${pad(Math.min(23, +hm[0] + 2))}${hm[1]}00` : `${e.d.replace(/-/g, "")}/${addDays(e.d2 || e.d, 1).replace(/-/g, "")}`;
  const gcal = "https://calendar.google.com/calendar/render?" + new URLSearchParams({ action: "TEMPLATE", text: title(e, L), dates, details: d + "\n\n" + SITE + url, location: `${e.lieu}, ${CP[e.lieu] || ""} France`, ctz: "Europe/Paris" });
  const wa = "https://wa.me/?text=" + encodeURIComponent(`${title(e, L)} · ${dateShort}${e.h ? " · " + e.h : ""} · ${e.lieu}\n${SITE}${url}`);
  const same = upcoming.filter(x => x !== e && x.lieu === e.lieu).slice(0, 6);
  const near = upcoming.filter(x => x !== e && x.lieu !== e.lieu && !x.always).slice(0, 5);
  const header = S.header.replace(/<a class="lang" href="[^"]*"/, `<a class="lang" href="${other === "en" ? enU : frU}"`);
  const crumbs = [[w.crumbs[0], T[L].home], [w.crumbs[1], w.agendaUrl], [title(e, L), url]];
  const ldCrumbs = { "@context": "https://schema.org", "@type": "BreadcrumbList", itemListElement: crumbs.map(([n, u], i) => ({ "@type": "ListItem", position: i + 1, name: n, item: SITE + u })) };
  const tags = [isFree(e) ? `<span class="tg">🆓 ${w.free}</span>` : "", isKids(e) ? `<span class="tg">🧒 ${w.kids}</span>` : ""].join("");
  return `<!DOCTYPE html>
<html lang="${L}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${metaTitle}</title>
<link rel="canonical" href="${SITE}${url}">
<link rel="alternate" hreflang="fr" href="${SITE}${frU}">
<link rel="alternate" hreflang="en" href="${SITE}${enU}">
<link rel="alternate" hreflang="x-default" href="${SITE}${frU}">
<meta name="description" content="${metaDesc}">
<link rel="icon" type="image/png" href="/img/favicon.png">
<link rel="manifest" href="/manifest.webmanifest">
<meta name="theme-color" content="#0a1424">
<link rel="apple-touch-icon" href="/img/apple-touch-icon.png">
<meta property="og:type" content="article">
<meta property="og:title" content="${esc(title(e, L))} · ${esc(dateShort)}">
<meta property="og:description" content="${metaDesc}">
<meta property="og:image" content="${SITE}/videos/hero-poster.jpg">
<meta property="og:url" content="${SITE}${url}">
${S.fonts}
<link rel="stylesheet" href="/assets/page.css">
${CSS}
${ldScript(ld(e, L))}
${ldScript(ldCrumbs)}
</head>
<body>
${header}
<section class="hero">
  <div class="wrap">
    <nav class="crumbs" aria-label="${L === "fr" ? "Fil d'Ariane" : "Breadcrumb"}"><a href="${T[L].home}">${w.crumbs[0]}</a> › <a href="${w.agendaUrl}">${w.crumbs[1]}</a> › ${esc(e.lieu)}</nav>
    <div class="kicker">📅 ${esc(dateShort)} · ${esc(e.lieu)}</div>
    <h1>${esc(title(e, L))}</h1>
  </div>
  ${S.scene}
</section>
<main class="wrap">
<article class="box lift">
  ${ended ? `<p class="past">${w.past}</p>` : ""}
  <div class="facts">
    <div><small>${w.when}</small><b>${esc(whenText(e, L))}</b></div>
    ${e.h ? `<div><small>${w.time}</small><b>${esc(e.h)}</b></div>` : ""}
    <div><small>${w.where}</small><b>${esc(e.lieu)} · ${CP[e.lieu] || ""}</b></div>
  </div>
  ${tags ? `<div>${tags}</div>` : ""}
  <p class="lead">${esc(d)}</p>
  <div class="btns">
    ${e.u ? `<a class="main" href="${esc(e.u)}" target="_blank" rel="noopener">${w.info}</a>` : ""}
    ${ended ? "" : `<a href="${esc(gcal)}" target="_blank" rel="noopener">${w.gcal}</a>`}
    <a href="${esc(wa)}" target="_blank" rel="noopener">${w.wa}</a>
    <a href="${w.agendaUrl}">${w.all}</a>
  </div>
  <p class="note">${w.check} · <a href="${w.meteoUrl}">${w.meteo} ${esc(e.lieu)}</a> · <a href="${w.venir[0]}">${w.venir[1]}</a></p>
</article>
${same.length ? `<section class="box"><h2>${w.also(esc(e.lieu))}</h2>${miniList(same, L)}</section>` : ""}
${near.length ? `<section class="box"><h2>${w.near}</h2>${miniList(near, L)}</section>` : ""}
</main>
${S.peaks}
${S.footer}
<script src="/assets/app.js" defer></script>
</body>
</html>
`;
}
let n = 0;
for (const e of A) for (const L of ["fr", "en"]) { write(evUrl(e, L).slice(1) + "index.html", eventPage(e, L)); n++; }

// ------------------------------------------------------------------ sitemap
let sm = read("sitemap.xml");
const evs = A.filter(e => (e.d2 || e.d) >= addDays(TODAY, -7)).map(e => {
  const alt = `<xhtml:link rel="alternate" hreflang="fr" href="${SITE}${evUrl(e, "fr")}"/><xhtml:link rel="alternate" hreflang="en" href="${SITE}${evUrl(e, "en")}"/>`;
  return ["fr", "en"].map(L => `  <url><loc>${SITE}${evUrl(e, L)}</loc>${alt}<changefreq>weekly</changefreq><priority>${L === "fr" ? "0.6" : "0.4"}</priority></url>`).join("\n");
}).join("\n");
sm = sm.replace("</urlset>", evs + "\n</urlset>");
write("sitemap.xml", sm);
console.log(`build ok · ${n} pages d'événements · aujourd'hui ${TODAY} · sitemap ${(sm.match(/<loc>/g) || []).length} URL`);
