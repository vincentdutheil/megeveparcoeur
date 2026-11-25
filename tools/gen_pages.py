#!/usr/bin/env python3
"""Génère les pages « Que faire », « Venir & se déplacer » et « Proposer un événement », en FR et EN.

Usage : python3 tools/gen_pages.py   (depuis la racine du dépôt), puis python3 tools/build_en.py n'est pas
nécessaire pour ces pages : elles sont écrites directement dans les deux langues.
"""
import os, re, json, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://www.megeveparcoeur.fr"
_bal = open(os.path.join(ROOT, "balades/index.html"), encoding="utf-8").read()
SCENE = re.search(r'<svg class="scene".*?</svg>', _bal, re.S).group(0)
PEAKS = re.search(r'<svg class="foot-peaks".*?</svg>', _bal, re.S).group(0)

NAV = {
    "fr": [("/#agenda", "Agenda"), ("/meteo/", "Météo &amp; neige"), ("/webcams/", "Webcams"), ("/galerie/", "Galerie"), ("/balades/", "Balades"),
           ("/carte/", "Carte"), ("/enfants/", "Le coin des enfants"), ("/boutique/", "Boutique")],
    "en": [("/en/#agenda", "What's on"), ("/en/meteo/", "Snow &amp; weather"), ("/en/webcams/", "Webcams"), ("/en/galerie/", "Gallery"), ("/en/balades/", "Walks"),
           ("/en/carte/", "Map"), ("/enfants/", "Kids' corner (FR)"), ("/en/boutique/", "Shop")],
}
FOOT = {
    "fr": '<a href="/">Accueil</a> · <a href="/#agenda">Agenda</a> · <a href="/que-faire/">Que faire ?</a> · <a href="/skier/">Skier</a> · <a href="/venir/">Venir &amp; se déplacer</a> · <a href="/proposer/">Proposer un événement</a> · <a href="/app/">📲 L\'appli</a> · <a href="/meteo/">Météo &amp; neige</a>',
    "en": '<a href="/en/">Home</a> · <a href="/en/#agenda">What\'s on</a> · <a href="/en/things-to-do/">Things to do</a> · <a href="/en/skiing/">Skiing</a> · <a href="/en/getting-here/">Getting here</a> · <a href="/en/submit-event/">Submit an event</a> · <a href="/en/app/">📲 The app</a> · <a href="/en/meteo/">Snow &amp; weather</a>',
}


def page(lang, path, alt, title, desc, kicker, h1, intro, body, css="", js="", extra_head="", agenda=False):
    """path / alt : chemins de la page et de sa traduction (ex. '/que-faire/' et '/en/things-to-do/')."""
    fr_p, en_p = (path, alt) if lang == "fr" else (alt, path)
    other = (alt, "FR", "fr") if lang == "en" else (alt, "EN", "en")
    nav = "\n".join(f'      <li><a href="{h}">{l}</a></li>' for h, l in NAV[lang])
    nav += f'\n      <li><a class="lang" href="{other[0]}" lang="{other[2]}" hreflang="{other[2]}">{other[1]}</a></li>'
    home = "/" if lang == "fr" else "/en/"
    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="canonical" href="{SITE}{path}">
<link rel="alternate" hreflang="fr" href="{SITE}{fr_p}">
<link rel="alternate" hreflang="en" href="{SITE}{en_p}">
<link rel="alternate" hreflang="x-default" href="{SITE}{fr_p}">
<meta name="description" content="{desc}">
<link rel="icon" type="image/png" href="/img/favicon.png">
<link rel="manifest" href="/manifest.webmanifest">
<meta name="theme-color" content="#0a1424">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Megève ❤">
<link rel="apple-touch-icon" href="/img/apple-touch-icon.png">
<meta property="og:image" content="{SITE}/videos/hero-poster.jpg">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght,SOFT@0,9..144,400..700,100;1,9..144,400..700,100&family=Nunito+Sans:opsz,wght@6..12,400;6..12,600;6..12,700;6..12,800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/page.css">
{'<link rel="stylesheet" href="/assets/agenda.css">' if agenda else ''}
<style>
main{{padding-bottom:10px}}
.box{{background:var(--card);border:1px solid var(--line);border-radius:22px;padding:22px 24px;box-shadow:0 8px 24px rgba(10,20,40,.06);margin:0 0 20px}}
.box h2{{font-size:1.5rem;margin-bottom:8px}}
.lift{{margin-top:-40px;position:relative;z-index:4}}
.links{{display:flex;flex-wrap:wrap;gap:10px;margin:8px 0 0}}
.links a{{text-decoration:none;font-weight:800;font-size:.92rem;border:1.5px solid var(--line);background:var(--card);border-radius:999px;padding:9px 15px}}
.links a:hover,.links a[aria-current]{{border-color:var(--heart);color:var(--heart)}}
.faq details{{border-top:1px solid var(--line);padding:12px 0}}.faq details:first-of-type{{border-top:0}}
.faq summary{{font-weight:800;cursor:pointer}}.faq p{{margin:8px 0 0;color:var(--muted)}}
.cta{{background:linear-gradient(120deg,#0b1c36,#1f3d7a);color:#fff;border-radius:22px;padding:22px 24px;display:flex;flex-wrap:wrap;gap:14px;align-items:center;justify-content:space-between;margin:10px 0 20px}}
.cta h3{{font-size:1.35rem}}.cta p{{margin:4px 0 0;opacity:.85}}
.cta a{{background:var(--heart);color:#fff;text-decoration:none;font-weight:800;border-radius:999px;padding:11px 18px}}
{css}
</style>
{extra_head}
</head>
<body>
<header class="top">
  <div class="wrap nav">
    <a class="brand" href="{home}" aria-label="Megève par cœur, {'accueil' if lang == 'fr' else 'home'}"><img src="/img/logo.png" alt="" width="40" height="40">Megève par cœur</a>
    <ul>
{nav}
    </ul>
  </div>
</header>
<section class="hero">
  <div class="wrap">
    <div class="kicker">{kicker}</div>
    <h1>{h1}</h1>
    <p>{intro}</p>
  </div>
  {SCENE}
</section>
<main class="wrap">
{body}
</main>
{PEAKS}
<footer><div class="wrap">© Megève par cœur · {FOOT[lang]}</div></footer>
<script src="/assets/app.js" defer></script>
{js}
</body>
</html>
'''


def write(path, content):
    p = os.path.join(ROOT, path.strip("/"), "index.html")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(content)
    print("ok", path)


def faq_ld(qa):
    return '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub("<[^>]+>", "", a)}} for q, a in qa]},
        ensure_ascii=False) + '</script>'


def faq_html(qa, lang):
    return (f'<section class="box faq"><h2>{"Bon à savoir" if lang == "fr" else "Good to know"}</h2>' +
            "".join(f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in qa) + "</section>")


# =====================================================================  QUE FAIRE
QF = [  # clé filtre, slug fr, slug en, données fr, données en
    ("we", "ce-week-end", "this-weekend",
     dict(nav="🎉 Ce week-end", title="Que faire à Megève ce week-end ? Agenda des sorties · Megève par cœur",
          desc="Que faire à Megève, Combloux, Demi-Quartier et Praz-sur-Arly ce week-end : marchés, concerts, spectacles, sorties en famille. Le programme complet, mis à jour chaque jeudi.",
          h1="Que faire à Megève <em>ce week-end</em> ?",
          intro="Tous les rendez-vous du vendredi au dimanche à Megève, Combloux, Demi-Quartier et Praz-sur-Arly : marchés, concerts, spectacles, animations de Noël et sorties en famille.",
          faq=[("Où trouver le programme du week-end à Megève ?", "Ici : la liste ci-dessus réunit les événements de Megève, Combloux, Demi-Quartier et Praz-sur-Arly, du vendredi au dimanche. Elle est mise à jour chaque jeudi, à partir des offices de tourisme, des mairies et des organisateurs."),
               ("Et s'il fait mauvais ?", 'Consultez notre sélection <a href="/que-faire/quand-il-pleut/">que faire quand il pleut</a> : expositions, spectacles, cinéma, patinoire…'),
               ("Y a-t-il des activités gratuites ?", 'Oui, beaucoup : marchés, pots d\'accueil, concerts en plein air, contes à la médiathèque. Voir <a href="/que-faire/gratuit/">les sorties gratuites</a>.')]),
     dict(nav="🎉 This weekend", title="What's on in Megève this weekend · Megève par cœur",
          desc="Things to do in Megève, Combloux, Demi-Quartier and Praz-sur-Arly this weekend: markets, concerts, shows, family outings. The full programme, updated every Thursday.",
          h1="What's on in Megève <em>this weekend</em>",
          intro="Every event from Friday to Sunday in Megève, Combloux, Demi-Quartier and Praz-sur-Arly: markets, concerts, shows, Christmas activities and family outings.",
          faq=[("Where can I find this weekend's programme in Megève?", "Right here: the list above brings together events in Megève, Combloux, Demi-Quartier and Praz-sur-Arly from Friday to Sunday. It is updated every Thursday from tourist offices, town halls and organisers."),
               ("What if the weather is bad?", 'See our <a href="/en/things-to-do/rainy-day/">rainy day ideas</a>: exhibitions, shows, cinema, ice rink…'),
               ("Are there free things to do?", 'Yes, lots: markets, welcome drinks, open-air concerts, story time at the library. See <a href="/en/things-to-do/free/">free things to do</a>.')])),
    ("today", "aujourd-hui", "today",
     dict(nav="☀️ Aujourd'hui", title="Que faire à Megève aujourd'hui ? Sorties du jour · Megève par cœur",
          desc="Que faire aujourd'hui à Megève, Combloux, Demi-Quartier et Praz-sur-Arly : les événements, animations et sorties du jour, au même endroit.",
          h1="Que faire à Megève <em>aujourd'hui</em> ?",
          intro="Les événements, animations et sorties du jour à Megève et dans les villages voisins. Pensez à vérifier l'horaire sur le lien de chaque événement.",
          faq=[("Que faire à Megève quand on n'a rien prévu ?", 'Regardez la liste ci-dessus, puis la <a href="/meteo/">météo &amp; la neige</a> et les <a href="/webcams/">webcams</a> pour choisir entre pistes, balade ou sortie au chaud.'),
               ("Des idées de balades ?", 'Nos <a href="/balades/">balades &amp; itinéraires raquettes</a> balisés, du tour des fontaines du village aux alpages face au Mont-Blanc.')]),
     dict(nav="☀️ Today", title="What's on in Megève today · Megève par cœur",
          desc="Things to do today in Megève, Combloux, Demi-Quartier and Praz-sur-Arly: today's events and activities in one place.",
          h1="What's on in Megève <em>today</em>",
          intro="Today's events and activities in Megève and the neighbouring villages. Please check the time on each event's link.",
          faq=[("What to do in Megève with no plans?", 'Check the list above, then the <a href="/en/meteo/">snow &amp; weather</a> and the <a href="/en/webcams/">webcams</a> to choose between the slopes, a walk or something indoors.'),
               ("Any walking ideas?", 'Our signposted <a href="/en/balades/">walks &amp; snowshoe trails</a>, from the village fountains loop to the pastures facing Mont Blanc.')])),
    ("kids", "avec-des-enfants", "with-kids",
     dict(nav="🧒 Avec des enfants", title="Que faire à Megève avec des enfants ? Sorties en famille · Megève par cœur",
          desc="Sorties en famille à Megève, Combloux, Demi-Quartier et Praz-sur-Arly : spectacles, contes, ateliers, patinoire, Père Noël, animations pour enfants. Agenda mis à jour chaque jeudi.",
          h1="Megève <em>avec des enfants</em>",
          intro="Spectacles, contes, ateliers, patinoire, rencontres avec le Père Noël : toutes les sorties en famille à Megève, Combloux, Demi-Quartier et Praz-sur-Arly.",
          faq=[("Que faire à Megève avec des enfants quand on ne skie pas ?", 'Patinoire du Palais, heure du conte à la médiathèque, ateliers à l\'office de tourisme, balade en calèche, et des <a href="/balades/">balades faciles</a> comme le circuit des P\'tits Loups à Combloux.'),
               ("Les animations sont-elles payantes ?", 'Beaucoup sont gratuites : regardez l\'étiquette « Gratuit » sur chaque événement, ou la page <a href="/que-faire/gratuit/">sorties gratuites</a>.'),
               ("Et s'il pleut ?", 'Voir <a href="/que-faire/quand-il-pleut/">que faire quand il pleut</a>.')]),
     dict(nav="🧒 With kids", title="Megève with kids: family things to do · Megève par cœur",
          desc="Family things to do in Megève, Combloux, Demi-Quartier and Praz-sur-Arly: shows, story time, workshops, ice rink, Father Christmas, kids' activities. Updated every Thursday.",
          h1="Megève <em>with kids</em>",
          intro="Shows, story time, workshops, the ice rink, meeting Father Christmas: every family outing in Megève, Combloux, Demi-Quartier and Praz-sur-Arly.",
          faq=[("What to do in Megève with kids when not skiing?", 'The Palais ice rink, story time at the library, workshops at the tourist office, carriage rides, and <a href="/en/balades/">easy walks</a> such as the P\'tits Loups trail in Combloux.'),
               ("Do activities cost money?", 'Many are free: look for the “Free” tag on each event, or see <a href="/en/things-to-do/free/">free things to do</a>.'),
               ("And if it rains?", 'See <a href="/en/things-to-do/rainy-day/">rainy day ideas</a>.')])),
    ("rain", "quand-il-pleut", "rainy-day",
     dict(nav="☔ Quand il pleut", title="Que faire à Megève quand il pleut ? Activités à l'abri · Megève par cœur",
          desc="Que faire à Megève quand il pleut ou qu'il fait trop froid : expositions, spectacles, cinéma, patinoire, médiathèque, ateliers. Les sorties à l'abri à Megève et alentours.",
          h1="Megève <em>quand il pleut</em>",
          intro="Expositions, spectacles, cinéma, patinoire, médiathèque, ateliers : les sorties à l'abri à Megève, Combloux, Demi-Quartier et Praz-sur-Arly.",
          faq=[("Où aller à Megève par mauvais temps ?", "Le Palais (piscine, patinoire, auditorium, médiathèque) est le grand refuge des jours gris. Ajoutez les expositions, les spectacles de l'office de tourisme et les galeries d'art du village."),
               ("Comment savoir s'il va pleuvoir ou neiger ?", 'Notre page <a href="/meteo/">météo &amp; neige</a> donne la prévision sur 7 jours pour les quatre villages, au village et en altitude.')]),
     dict(nav="☔ Rainy day", title="Megève on a rainy day: indoor things to do · Megève par cœur",
          desc="Things to do in Megève when it rains or it's too cold: exhibitions, shows, cinema, ice rink, library, workshops. Indoor ideas in and around Megève.",
          h1="Megève <em>on a rainy day</em>",
          intro="Exhibitions, shows, cinema, the ice rink, the library, workshops: indoor things to do in Megève, Combloux, Demi-Quartier and Praz-sur-Arly.",
          faq=[("Where to go in Megève in bad weather?", "Le Palais (swimming pool, ice rink, auditorium, library) is the go-to place on grey days. Add exhibitions, shows at the tourist office and the village art galleries."),
               ("How do I know if it will rain or snow?", 'Our <a href="/en/meteo/">snow &amp; weather</a> page gives the 7-day forecast for the four villages, in the village and up the mountain.')])),
    ("free", "gratuit", "free",
     dict(nav="🆓 Gratuit", title="Que faire gratuitement à Megève ? Sorties gratuites · Megève par cœur",
          desc="Les sorties et animations gratuites à Megève, Combloux, Demi-Quartier et Praz-sur-Arly : marchés, concerts, contes, pots d'accueil, spectacles en plein air.",
          h1="Megève <em>gratuit</em>",
          intro="Marchés, concerts, contes, pots d'accueil, spectacles en plein air, ateliers : tout ce qu'on peut faire sans dépenser un euro à Megève et alentours.",
          faq=[("Megève, c'est forcément cher ?", 'Non : une grande partie des animations sont gratuites, et les <a href="/balades/">balades balisées</a> aussi. Le Meg\'bus, la navette du village, est gratuit.'),
               ("Comment être sûr que c'est gratuit ?", "Nous repérons la mention « gratuit » ou « entrée libre » chez l'organisateur. Vérifiez sur le lien de l'événement : les conditions peuvent changer.")]),
     dict(nav="🆓 Free", title="Free things to do in Megève · Megève par cœur",
          desc="Free events and activities in Megève, Combloux, Demi-Quartier and Praz-sur-Arly: markets, concerts, story time, welcome drinks, open-air shows.",
          h1="Megève <em>for free</em>",
          intro="Markets, concerts, story time, welcome drinks, open-air shows, workshops: everything you can do in and around Megève without spending a cent.",
          faq=[("Is Megève always expensive?", 'No: many events are free, and so are the <a href="/en/balades/">signposted walks</a>. The Meg\'bus village shuttle is free too.'),
               ("How do you know it's free?", "We look for “free” or “free entry” from the organiser. Please check the event's link: conditions can change.")])),
]

TABS = {"fr": ("Filtrer par village", "Tout"), "en": ("Filter by village", "All")}


def qf_links(lang, cur=None):
    base = "/que-faire/" if lang == "fr" else "/en/things-to-do/"
    out = []
    for k, sfr, sen, dfr, den in QF:
        d = dfr if lang == "fr" else den
        href = base + (sfr if lang == "fr" else sen) + "/"
        out.append(f'<a href="{href}"{" aria-current=\"page\"" if k == cur else ""}>{d["nav"]}</a>')
    return '<div class="links">' + "".join(out) + "</div>"


def qf_pages():
    for k, sfr, sen, dfr, den in QF:
        for lang, d in (("fr", dfr), ("en", den)):
            path = f"/que-faire/{sfr}/" if lang == "fr" else f"/en/things-to-do/{sen}/"
            alt = f"/en/things-to-do/{sen}/" if lang == "fr" else f"/que-faire/{sfr}/"
            lab, all_ = TABS[lang]
            tabs = f'<button class="tab" aria-pressed="true" data-l="all">{all_}</button>' + "".join(
                f'<button class="tab" aria-pressed="false" data-l="{v}">{v}</button>' for v in ["Megève", "Combloux", "Demi-Quartier", "Praz-sur-Arly"])
            nl = ("📬 Recevoir l'agenda chaque jeudi", "Tous les rendez-vous de la semaine dans ta boîte mail. Gratuit, sans pub.", "/#newsletter", "Je m'inscris")\
                if lang == "fr" else ("📬 Get the events every Thursday", "This week's events in your inbox. Free, no ads.", "/en/#newsletter", "Sign me up")
            body = f'''<section class="box lift">
  <p class="ag-stats" id="ag-stats" aria-live="polite" style="margin-top:0"></p>
  <div class="tabs" role="group" aria-label="{lab}" id="ag-tabs" style="margin:12px 0 14px">{tabs}</div>
  <div class="quick" id="ag-quick" role="group" aria-label="{"Filtres rapides" if lang == "fr" else "Quick filters"}"></div>
  <div class="agenda" id="agenda-list" data-q="{k}"><p class="note">{"Chargement de l'agenda…" if lang == "fr" else "Loading events…"}</p></div>
</section>
<div class="cta"><div><h3>{nl[0]}</h3><p>{nl[1]}</p></div><a href="{nl[2]}">{nl[3]}</a></div>
{faq_html(d["faq"], lang)}
<section class="box"><h2>{"Autres idées" if lang == "fr" else "More ideas"}</h2>{qf_links(lang, k)}</section>'''
            kicker = "📅 " + ("L'agenda de Megève &amp; alentours" if lang == "fr" else "What's on in Megève &amp; around")
            write(path, page(lang, path, alt, d["title"], H.escape(d["desc"]), kicker, d["h1"], d["intro"], body,
                             css=".lift .ev{box-shadow:none}", agenda=True, extra_head=faq_ld(d["faq"]),
                             js='<script src="/assets/agenda.js" defer></script>'))
    # page d'entrée
    for lang in ("fr", "en"):
        path, alt = ("/que-faire/", "/en/things-to-do/") if lang == "fr" else ("/en/things-to-do/", "/que-faire/")
        cards = []
        for k, sfr, sen, dfr, den in QF:
            d = dfr if lang == "fr" else den
            href = (f"/que-faire/{sfr}/" if lang == "fr" else f"/en/things-to-do/{sen}/")
            cards.append(f'<a class="qc" href="{href}"><b>{d["nav"]}</b><span>{d["intro"]}</span></a>')
        more = [("/balades/", "🥾 Balades &amp; raquettes", "Itinéraires balisés pour profiter de la montagne sans skis."),
                ("/carte/", "🗺️ La carte des beaux coins", "Panoramas, patrimoine et sorties en famille."),
                ("/skier/", "⛷️ Skier à Megève &amp; Combloux", "Domaines, prix des forfaits, parkings et plans des pistes."),
                ("/meteo/", "❄️ Météo &amp; neige", "Neige au sol et chutes prévues sur 7 jours."),
                ("/venir/", "🚗 Venir &amp; se déplacer", "Parkings, navettes gratuites, train et aéroports.")] if lang == "fr" else \
               [("/en/balades/", "🥾 Walks &amp; snowshoes", "Signposted trails to enjoy the mountains without skis."),
                ("/en/carte/", "🗺️ Map of favourite spots", "Viewpoints, heritage and family outings."),
                ("/en/skiing/", "⛷️ Skiing in Megève &amp; Combloux", "Ski areas, lift pass prices, parking and piste maps."),
                ("/en/meteo/", "❄️ Snow &amp; weather", "Snow on the ground and 7-day snowfall forecast."),
                ("/en/getting-here/", "🚗 Getting here &amp; around", "Car parks, free shuttles, trains and airports.")]
        cards += [f'<a class="qc alt" href="{h}"><b>{t}</b><span>{s}</span></a>' for h, t, s in more]
        if lang == "fr":
            t, de, h1, intro = ("Que faire à Megève ? Idées de sorties et agenda · Megève par cœur",
                                "Que faire à Megève, Combloux, Demi-Quartier et Praz-sur-Arly : ce week-end, aujourd'hui, avec des enfants, quand il pleut, gratuitement. Idées de sorties et agenda complet.",
                                "Que faire à <em>Megève</em> ?",
                                "Ce week-end, aujourd'hui, avec des enfants, quand il pleut ou sans dépenser un euro : toutes nos idées de sorties à Megève, Combloux, Demi-Quartier et Praz-sur-Arly.")
        else:
            t, de, h1, intro = ("Things to do in Megève: ideas and events · Megève par cœur",
                                "Things to do in Megève, Combloux, Demi-Quartier and Praz-sur-Arly: this weekend, today, with kids, on a rainy day, for free. Ideas and the full events guide.",
                                "Things to do in <em>Megève</em>",
                                "This weekend, today, with kids, on a rainy day or without spending a cent: all our ideas in Megève, Combloux, Demi-Quartier and Praz-sur-Arly.")
        body = f'<div class="qgrid lift">{"".join(cards)}</div>'
        css = (".qgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:20px}"
               ".qc{display:flex;flex-direction:column;gap:6px;text-decoration:none;background:var(--card);border:1px solid var(--line);border-radius:20px;padding:18px 20px;box-shadow:0 8px 24px rgba(10,20,40,.06)}"
               ".qc b{font-family:var(--display);font-weight:500;font-size:1.35rem}.qc span{color:var(--muted);font-size:.92rem}"
               ".qc:hover{border-color:var(--heart)}.qc.alt{background:var(--wool)}"
               "@media(max-width:860px){.qgrid{grid-template-columns:1fr 1fr}}@media(max-width:560px){.qgrid{grid-template-columns:1fr}}")
        write(path, page(lang, path, alt, t, H.escape(de), "📍 Megève · Combloux · Demi-Quartier · Praz-sur-Arly", h1, intro, body, css=css))


# =====================================================================  VENIR & SE DÉPLACER
VENIR = {
 "fr": dict(
  title="Venir à Megève & se déplacer : parkings, navettes, train, aéroport · Megève par cœur",
  desc="Comment venir à Megève, Combloux, Demi-Quartier et Praz-sur-Arly : voiture, train, bus et aéroport de Genève. Parkings de Megève, Meg'bus gratuit, navettes et bus entre les villages.",
  h1="Venir &amp; <em>se déplacer</em>",
  intro="Voiture, train, bus, avion : comment venir à Megève, puis se garer et circuler entre les villages sans prise de tête.",
  blocks=[
   ("🚗 En voiture", ["Depuis Genève : environ 70 km, compter 1 h hors bouchons, par l'autoroute A40 (sortie Sallanches) puis la route de Megève.",
                    "En hiver, équipements obligatoires du 1er novembre au 31 mars en Haute-Savoie (loi Montagne) : pneus hiver, ou chaînes / chaussettes à neige dans le coffre.",
                    "Les samedis de vacances, partez tôt : les montées vers les stations sont très chargées en fin de matinée."]),
   ("🚆 En train", ["La gare la plus proche est celle de <b>Sallanches-Combloux-Megève</b>, desservie par les TER.",
                   "De la gare, les bus régionaux <b>Y83</b> montent à Combloux, Megève et Praz-sur-Arly (environ 25 min jusqu'à Megève)."]),
   ("✈️ En avion", ["L'aéroport le plus proche est <b>Genève</b> (environ 1 h en voiture). Lyon et Annecy sont aussi possibles.",
                   "Des cars (FlixBus) relient Genève et Lyon à la gare routière de Sallanches, puis bus Y83 jusqu'à Megève.",
                   "Plusieurs sociétés proposent des transferts partagés ou privés depuis l'aéroport : réservez à l'avance en haute saison."]),
   ("🚌 Sur place, sans voiture", ["<b>Meg'bus</b> : la navette gratuite de Megève relie le village aux remontées (lignes 1 à 3 en hiver, 1 et 2 en été).",
                    "Les lignes régionales <b>Y82</b> (Chamonix · Saint-Gervais · Combloux · Megève · Praz-sur-Arly) et <b>Y83</b> (Sallanches · Combloux · Megève · Praz-sur-Arly) relient les villages entre eux.",
                    "<b>Combloux</b> et <b>Praz-sur-Arly</b> ont aussi leurs navettes d'hiver vers les pistes : horaires aux offices de tourisme.",
                    "Vélos électriques en libre-service <b>Montenvélo</b> dans plusieurs communes du Pays du Mont-Blanc, dont Combloux."]),
   ("🅿️ Se garer à Megève", ["Parkings couverts : <b>Village</b> (route Nationale), <b>Casino</b> (entrée de la zone piétonne, 200 places, hauteur 1,90 m), <b>Office de Tourisme</b> (rue de la Poste), <b>Rochebrune</b> et <b>Mont d'Arbois</b> (297 places au pied de la télécabine, 2,10 m).",
                    "Parking aérien du <b>Palais</b> : 389 places, à deux pas du centre.",
                    "Les 30 premières minutes sont gratuites dans la plupart des parkings. Renseignements : Megève Parkings, 04 50 21 18 30.",
                    "À Combloux, les parkings gratuits des <b>Brons</b>, de <b>la Cry</b> et de <b>Cuchet</b> sont au pied du domaine skiable (détails sur la page <a href=\"/skier/#parkings\">Skier</a>)."]),
  ],
  note="Informations pratiques vérifiées auprès des offices de tourisme et de la mairie de Megève ; horaires et tarifs peuvent changer d'une saison à l'autre.",
  links=[("https://www.megeve-tourisme.fr/", "Megève Tourisme"), ("https://www.combloux.com/", "Office de tourisme de Combloux"),
         ("https://www.prazsurarly.com/", "Office de tourisme de Praz-sur-Arly"), ("https://www.auvergnerhonealpes.fr/", "Cars Région (lignes Y82, Y83)")]),
 "en": dict(
  title="Getting to Megève & around: car parks, shuttles, train, airport · Megève par cœur",
  desc="How to get to Megève, Combloux, Demi-Quartier and Praz-sur-Arly: car, train, bus and Geneva airport. Megève car parks, the free Meg'bus, shuttles and buses between the villages.",
  h1="Getting here <em>&amp; around</em>",
  intro="Car, train, bus or plane: how to get to Megève, then park and get around the villages hassle-free.",
  blocks=[
   ("🚗 By car", ["From Geneva: about 70 km, around 1 hour without traffic, via the A40 motorway (Sallanches exit) then the road up to Megève.",
                 "In winter, equipment is compulsory from 1 November to 31 March in Haute-Savoie (Mountain Law): winter tyres, or snow chains / snow socks in the boot.",
                 "On holiday Saturdays, leave early: the roads up to the resorts get very busy from late morning."]),
   ("🚆 By train", ["The nearest station is <b>Sallanches-Combloux-Megève</b>, served by TER regional trains.",
                   "From the station, regional bus <b>Y83</b> goes up to Combloux, Megève and Praz-sur-Arly (about 25 minutes to Megève)."]),
   ("✈️ By plane", ["The nearest airport is <b>Geneva</b> (about 1 hour by car). Lyon and Annecy are also options.",
                   "Coaches (FlixBus) link Geneva and Lyon to Sallanches bus station, then take bus Y83 to Megève.",
                   "Several companies offer shared or private airport transfers: book ahead in high season."]),
   ("🚌 Getting around without a car", ["<b>Meg'bus</b>: Megève's free shuttle links the village to the lifts (lines 1 to 3 in winter, 1 and 2 in summer).",
                    "Regional lines <b>Y82</b> (Chamonix · Saint-Gervais · Combloux · Megève · Praz-sur-Arly) and <b>Y83</b> (Sallanches · Combloux · Megève · Praz-sur-Arly) link the villages.",
                    "<b>Combloux</b> and <b>Praz-sur-Arly</b> also run winter shuttles to the slopes: timetables at the tourist offices.",
                    "<b>Montenvélo</b> self-service e-bikes in several Pays du Mont-Blanc villages, including Combloux."]),
   ("🅿️ Parking in Megève", ["Covered car parks: <b>Village</b> (route Nationale), <b>Casino</b> (by the pedestrian area, 200 spaces, 1.90 m height limit), <b>Tourist Office</b> (rue de la Poste), <b>Rochebrune</b> and <b>Mont d'Arbois</b> (297 spaces at the gondola, 2.10 m).",
                    "Open-air <b>Palais</b> car park: 389 spaces, a short walk from the centre.",
                    "The first 30 minutes are free in most car parks. Information: Megève Parkings, +33 4 50 21 18 30.",
                    "In Combloux, the free <b>Brons</b>, <b>la Cry</b> and <b>Cuchet</b> car parks are at the foot of the ski area (details on the <a href=\"/en/skiing/#parkings\">Skiing</a> page)."]),
  ],
  note="Practical information checked with the tourist offices and Megève town hall; timetables and prices may change from season to season.",
  links=[("https://www.megeve-tourisme.fr/en/", "Megève Tourisme"), ("https://www.combloux.com/", "Combloux tourist office"),
         ("https://www.prazsurarly.com/en/", "Praz-sur-Arly tourist office"), ("https://www.auvergnerhonealpes.fr/", "Région buses (Y82, Y83)")]),
}


def venir_pages():
    for lang in ("fr", "en"):
        d = VENIR[lang]
        path, alt = ("/venir/", "/en/getting-here/") if lang == "fr" else ("/en/getting-here/", "/venir/")
        blocks = "".join(f'<section class="box vb"><h2>{t}</h2><ul>{"".join(f"<li>{x}</li>" for x in items)}</ul></section>' for t, items in d["blocks"])
        links = '<div class="links">' + "".join(f'<a href="{u}" target="_blank" rel="noopener">{l} ↗</a>' for u, l in d["links"]) + "</div>"
        body = f'''<div class="vgrid lift">{blocks}</div>
<section class="box"><h2>{"Liens utiles" if lang == "fr" else "Useful links"}</h2>{links}<p class="note">{d["note"]}</p></section>'''
        css = (".vgrid{display:grid;grid-template-columns:1fr 1fr;gap:0 20px}.vb ul{margin:0;padding-left:20px}.vb li{margin:6px 0}"
               ".vb:last-child{grid-column:1/-1}@media(max-width:760px){.vgrid{grid-template-columns:1fr}}")
        write(path, page(lang, path, alt, d["title"], H.escape(d["desc"]), "🧭 Megève · Combloux · Demi-Quartier · Praz-sur-Arly",
                         d["h1"], d["intro"], body, css=css))


# =====================================================================  PROPOSER UN ÉVÉNEMENT
PROP = {
 "fr": dict(title="Proposer un événement à l'agenda de Megève · Megève par cœur",
            desc="Organisateur, association, commerçant : proposez votre événement à Megève, Combloux, Demi-Quartier ou Praz-sur-Arly pour l'agenda de Megève par cœur. Gratuit.",
            h1="Proposer un <em>événement</em>",
            intro="Vous organisez un concert, un marché, une expo, une animation à Megève, Combloux, Demi-Quartier ou Praz-sur-Arly ? Envoyez-le-nous : c'est gratuit, et chaque proposition est relue avant publication.",
            L=dict(t="Nom de l'événement", d="Date de début", d2="Date de fin (si plusieurs jours)", h="Horaire", hp="ex. 18h30",
                   lieu="Village", where="Lieu précis", wherep="ex. place de l'église, salle des fêtes…", x="Description",
                   xp="En deux ou trois phrases : de quoi s'agit-il, pour qui, gratuit ou payant ?", u="Lien vers plus d'infos (site, billetterie…)",
                   name="Votre nom ou organisation", mail="Votre e-mail (jamais publié)", consent="J'accepte que ces informations soient publiées dans l'agenda de Megève par cœur (sauf mon e-mail).",
                   send="Envoyer la proposition", note="Nous publions les événements ouverts au public, à Megève et dans les villages voisins. Pas de réponse sous une semaine ? Écrivez à bonjour@megeveparcoeur.fr.",
                   sending="⏳ Envoi en cours…", okt="Merci, c'est reçu !", ok="Votre événement sera relu puis publié dans l'agenda, en général avant le jeudi suivant.",
                   err="Oups, l'envoi n'a pas marché. Réessayez, ou écrivez-nous à bonjour@megeveparcoeur.fr.",
                   miss="Merci de remplir le nom, la date, le village, la description et votre e-mail, et de cocher la case.")),
 "en": dict(title="Submit an event to the Megève events guide · Megève par cœur",
            desc="Organisers, associations, local businesses: submit your event in Megève, Combloux, Demi-Quartier or Praz-sur-Arly to the Megève par cœur events guide. Free.",
            h1="Submit an <em>event</em>",
            intro="Organising a concert, market, exhibition or activity in Megève, Combloux, Demi-Quartier or Praz-sur-Arly? Send it to us: it's free, and every submission is reviewed before publication.",
            L=dict(t="Event name", d="Start date", d2="End date (if several days)", h="Time", hp="e.g. 6:30pm",
                   lieu="Village", where="Exact place", wherep="e.g. church square, village hall…", x="Description",
                   xp="Two or three sentences: what is it, who is it for, free or paid?", u="Link for more info (website, tickets…)",
                   name="Your name or organisation", mail="Your email (never published)", consent="I agree that this information may be published in the Megève par cœur events guide (except my email).",
                   send="Send my event", note="We publish events open to the public, in Megève and the neighbouring villages. No reply within a week? Write to bonjour@megeveparcoeur.fr.",
                   sending="⏳ Sending…", okt="Thank you, it's in!", ok="Your event will be reviewed and published, usually before the following Thursday.",
                   err="Oops, sending failed. Please try again, or write to bonjour@megeveparcoeur.fr.",
                   miss="Please fill in the name, date, village, description and your email, and tick the box.")),
}


def prop_pages():
    for lang in ("fr", "en"):
        d = PROP[lang]; L = d["L"]
        path, alt = ("/proposer/", "/en/submit-event/") if lang == "fr" else ("/en/submit-event/", "/proposer/")
        opts = "".join(f"<option>{v}</option>" for v in ["Megève", "Combloux", "Demi-Quartier", "Praz-sur-Arly"])
        body = f'''<section class="box lift">
<form id="pr-form" novalidate>
  <div class="g">
    <label class="w">{L["t"]} *<input name="t" required maxlength="120"></label>
    <label>{L["d"]} *<input type="date" name="d" required></label>
    <label>{L["d2"]}<input type="date" name="d2"></label>
    <label>{L["h"]}<input name="h" maxlength="40" placeholder="{L["hp"]}"></label>
    <label>{L["lieu"]} *<select name="lieu" required>{opts}</select></label>
    <label class="w">{L["where"]}<input name="where" maxlength="120" placeholder="{L["wherep"]}"></label>
    <label class="w">{L["x"]} *<textarea name="x" required maxlength="1200" rows="5" placeholder="{L["xp"]}"></textarea></label>
    <label class="w">{L["u"]}<input type="url" name="u" maxlength="300" placeholder="https://…"></label>
    <label>{L["name"]}<input name="name" maxlength="120" autocomplete="organization"></label>
    <label>{L["mail"]} *<input type="email" name="mail" required maxlength="160" autocomplete="email"></label>
  </div>
  <input class="hp" type="text" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">
  <label class="c"><input type="checkbox" name="consent" required> {L["consent"]}</label>
  <button type="submit">{L["send"]}</button>
  <div class="msg" id="pr-msg" aria-live="polite"></div>
</form>
<p class="note">{L["note"]}</p>
</section>'''
        css = (".g{display:grid;grid-template-columns:1fr 1fr;gap:14px}.g label{display:flex;flex-direction:column;gap:6px;font-weight:800;font-size:.9rem}.g .w{grid-column:1/-1}"
               ".g input,.g select,.g textarea{font:500 1rem var(--body);color:var(--ink);background:var(--wool);border:1.5px solid var(--line);border-radius:12px;padding:11px 12px}"
               ".g input:focus,.g select:focus,.g textarea:focus{outline:none;border-color:var(--heart)}"
               ".c{display:flex;gap:10px;align-items:flex-start;margin:16px 0;font-size:.92rem}.hp{position:absolute;left:-9999px}"
               "#pr-form button{background:var(--heart);color:#fff;border:0;border-radius:999px;padding:13px 22px;font:800 1rem var(--body);cursor:pointer}"
               "#pr-form button:disabled{opacity:.6}.msg{margin-top:12px;font-weight:700}.msg.err{color:var(--heart)}"
               ".done{text-align:center;padding:20px}.done .ic{font-size:2.6rem}.done b{display:block;font-family:var(--display);font-size:1.6rem;font-weight:500;margin:6px 0}"
               "@media(max-width:620px){.g{grid-template-columns:1fr}}")
        M = json.dumps({k: L[k] for k in ("sending", "okt", "ok", "err", "miss")}, ensure_ascii=False)
        js = f'''<script>
(function(){{const f=document.getElementById("pr-form"),m=document.getElementById("pr-msg"),M={M};
f.addEventListener("submit",async e=>{{e.preventDefault();const d=Object.fromEntries(new FormData(f));m.classList.remove("err");
  if(!d.t||!d.d||!d.lieu||!d.x||!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]{{2,}}$/.test(d.mail||"")||!d.consent){{m.classList.add("err");m.textContent=M.miss;return;}}
  m.textContent=M.sending;f.querySelector("button").disabled=true;
  try{{const r=await fetch("/api/propose",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{...d,lang:"{lang}"}})}});const j=await r.json().catch(()=>({{}}));
    if(j.ok){{f.outerHTML=`<div class="done" role="status"><div class="ic">🎉</div><b>${{M.okt}}</b><p>${{M.ok}}</p></div>`;return;}}
    m.classList.add("err");m.textContent=M.err;}}catch(_){{m.classList.add("err");m.textContent=M.err;}}
  f.querySelector("button").disabled=false;}});}})();
</script>'''
        write(path, page(lang, path, alt, d["title"], H.escape(d["desc"]), "📝 " + ("Organisateurs" if lang == "fr" else "Organisers"),
                         d["h1"], d["intro"], body, css=css, js=js))


# =====================================================================  L'APPLI (installation + notifications)
APP = {
 "fr": dict(title="L'appli Megève par cœur · agenda, neige et notifications sur ton téléphone",
   desc="Installe gratuitement l'appli Megève par cœur sur iPhone ou Android : l'agenda de Megève, la neige, les webcams, tes sorties favorites et des notifications pour le week-end et la neige.",
   h1="Megève par cœur <em>dans ta poche</em>",
   intro="L'agenda, la neige, les webcams et tes sorties préférées, sur ton écran d'accueil. Gratuit, sans pub, sans passer par l'App Store.",
   inst="Installer l'appli", notif="Les notifications", what="Ce que fait l'appli",
   inapp="👋 Tu es dans le navigateur d'Instagram (ou d'une autre appli). Il ne permet pas d'installer Megève par cœur : ouvre d'abord le site dans ton vrai navigateur.",
   inapp_ios="Touche les <b>trois petits points ⋯</b> en haut à droite, puis <b>« Ouvrir dans le navigateur externe »</b> (ou « Ouvrir dans Safari »).",
   inapp_and="Touche le bouton ci-dessous, ou les <b>trois petits points ⋮</b> en haut à droite, puis <b>« Ouvrir dans Chrome »</b>.", inapp_btn="🌐 Ouvrir dans Chrome",
   ios=["Ouvre megeveparcoeur.fr dans <b>Safari</b>.", "Touche le bouton <b>Partager</b> <span class=\"ic\">⬆︎</span> en bas de l'écran.", "Choisis <b>« Sur l'écran d'accueil »</b>, puis <b>Ajouter</b>.", "Ouvre l'appli depuis sa nouvelle icône ❤ pour activer les notifications."],
   android=["Ouvre megeveparcoeur.fr dans <b>Chrome</b>.", "Touche le bouton <b>Installer</b> ci-dessous, ou le menu <b>⋮</b> puis <b>« Installer l'application »</b>.", "L'appli apparaît sur ton écran d'accueil, comme les autres."],
   desktop="Sur ordinateur, Chrome et Edge proposent aussi d'installer l'appli (icône ⊕ dans la barre d'adresse). Mais c'est surtout sur téléphone qu'elle est pratique !",
   installed="✅ L'appli est installée sur cet appareil. Bienvenue !", installBtn="📲 Installer l'appli",
   t_we="🎉 Le programme du week-end", t_we2="Chaque vendredi après-midi : les sorties du week-end à Megève et alentours.",
   t_snow="❄️ Les alertes neige", t_snow2="Quand une belle chute de neige est annoncée en altitude.",
   on="🔔 Activer les notifications", off="Désactiver", save="Enregistrer mes choix", test="Recevoir une notification de test",
   s_ok="✅ Les notifications sont activées sur cet appareil.", s_saved="✅ C'est noté !", s_denied="Les notifications sont bloquées pour ce site. Autorise-les dans les réglages de ton navigateur, puis réessaie.",
   s_ios="Sur iPhone, les notifications marchent seulement dans l'appli installée : ajoute d'abord Megève par cœur à ton écran d'accueil (voir ci-dessus), puis ouvre-la depuis son icône.",
   s_no="Ton navigateur ne gère pas les notifications. Essaie avec Chrome (Android) ou Safari (iPhone, iOS 16.4 ou plus récent).",
   s_err="Oups, l'activation n'a pas marché. Réessaie dans un instant.", s_offd="Notifications désactivées.", s_test="📨 Envoyée ! Elle arrive dans quelques secondes.",
   feats=[("⭐", "Mes sorties", "Touche ☆ sur un événement de l'agenda pour le garder dans « Mes sorties »."), ("📶", "Même sans réseau", "Les dernières pages vues restent consultables en montagne, même sans 4G."),
          ("⚡", "Raccourcis", "Appui long sur l'icône : agenda, ce week-end, neige, webcams, coin des enfants."), ("🔒", "Respect de la vie privée", "Pas de compte, pas de pub, pas de pistage. Les favoris restent sur ton téléphone.")]),
 "en": dict(title="The Megève par cœur app · events, snow and notifications on your phone",
   desc="Install the free Megève par cœur app on iPhone or Android: Megève events, snow, webcams, your favourite outings and notifications for the weekend and fresh snow.",
   h1="Megève par cœur <em>in your pocket</em>",
   intro="Events, snow, webcams and your favourite outings on your home screen. Free, no ads, no App Store needed.",
   inst="Install the app", notif="Notifications", what="What the app does",
   inapp="👋 You're in Instagram's browser (or another app's). It can't install Megève par cœur: first open the site in your real browser.",
   inapp_ios="Tap the <b>three dots ⋯</b> at the top right, then <b>“Open in external browser”</b> (or “Open in Safari”).",
   inapp_and="Tap the button below, or the <b>three dots ⋮</b> at the top right, then <b>“Open in Chrome”</b>.", inapp_btn="🌐 Open in Chrome",
   ios=["Open megeveparcoeur.fr in <b>Safari</b>.", "Tap the <b>Share</b> button <span class=\"ic\">⬆︎</span> at the bottom of the screen.", "Choose <b>“Add to Home Screen”</b>, then <b>Add</b>.", "Open the app from its new ❤ icon to turn on notifications."],
   android=["Open megeveparcoeur.fr in <b>Chrome</b>.", "Tap the <b>Install</b> button below, or the <b>⋮</b> menu then <b>“Install app”</b>.", "The app appears on your home screen like any other."],
   desktop="On a computer, Chrome and Edge can install the app too (⊕ icon in the address bar). But it's most handy on your phone!",
   installed="✅ The app is installed on this device. Welcome!", installBtn="📲 Install the app",
   t_we="🎉 The weekend programme", t_we2="Every Friday afternoon: what's on this weekend in and around Megève.",
   t_snow="❄️ Snow alerts", t_snow2="When a good snowfall is forecast up the mountain.",
   on="🔔 Turn on notifications", off="Turn off", save="Save my choices", test="Send me a test notification",
   s_ok="✅ Notifications are on for this device.", s_saved="✅ Saved!", s_denied="Notifications are blocked for this site. Allow them in your browser settings, then try again.",
   s_ios="On iPhone, notifications only work in the installed app: first add Megève par cœur to your home screen (see above), then open it from its icon.",
   s_no="Your browser doesn't support notifications. Try Chrome (Android) or Safari (iPhone, iOS 16.4 or later).",
   s_err="Oops, that didn't work. Please try again in a moment.", s_offd="Notifications turned off.", s_test="📨 Sent! It should arrive in a few seconds.",
   feats=[("⭐", "My picks", "Tap ☆ on any event to save it to “My picks”."), ("📶", "Works offline", "The last pages you viewed stay available in the mountains, even without signal."),
          ("⚡", "Shortcuts", "Long-press the icon: events, this weekend, snow, webcams, kids' corner."), ("🔒", "Privacy first", "No account, no ads, no tracking. Your favourites stay on your phone.")]),
}


def app_pages():
    for lang in ("fr", "en"):
        d = APP[lang]
        path, alt = ("/app/", "/en/app/") if lang == "fr" else ("/en/app/", "/app/")
        ol = lambda items: "<ol class=\"steps\">" + "".join(f"<li>{x}</li>" for x in items) + "</ol>"
        feats = "".join(f'<div class="ft"><span>{i}</span><b>{t}</b><p>{x}</p></div>' for i, t, x in d["feats"])
        body = f"""<section class="box lift" id="inst">
  <h2>{d["inst"]}</h2>
  <p class="ok hidden" id="i-done">{d["installed"]}</p>
  <div id="i-inapp" class="hidden warn"><p>{d["inapp"]}</p><p id="i-inapp-ios" class="hidden">{d["inapp_ios"]}</p><p id="i-inapp-and" class="hidden">{d["inapp_and"]}</p><a class="big hidden" id="i-chrome" href="#">{d["inapp_btn"]}</a></div>
  <div id="i-ios" class="hidden"><p class="plat">🍏 iPhone / iPad</p>{ol(d["ios"])}</div>
  <div id="i-and" class="hidden"><p class="plat">🤖 Android</p>{ol(d["android"])}<button class="big hidden" id="i-btn">{d["installBtn"]}</button></div>
  <div id="i-desk" class="hidden"><p class="plat">🍏 iPhone</p>{ol(d["ios"])}<p class="plat">🤖 Android</p>{ol(d["android"])}<p class="note">{d["desktop"]}</p><button class="big hidden" id="i-btn2">{d["installBtn"]}</button></div>
</section>
<section class="box" id="notif">
  <h2>{d["notif"]}</h2>
  <label class="tp"><input type="checkbox" id="t-we" checked><span><b>{d["t_we"]}</b><small>{d["t_we2"]}</small></span></label>
  <label class="tp"><input type="checkbox" id="t-snow" checked><span><b>{d["t_snow"]}</b><small>{d["t_snow2"]}</small></span></label>
  <div class="row"><button class="big" id="n-on">{d["on"]}</button><button class="ghost hidden" id="n-save">{d["save"]}</button><button class="ghost hidden" id="n-test">{d["test"]}</button><button class="ghost hidden" id="n-off">{d["off"]}</button></div>
  <p class="msg" id="n-msg" aria-live="polite"></p>
</section>
<section class="box"><h2>{d["what"]}</h2><div class="feats">{feats}</div></section>"""
        css = (".steps{margin:6px 0 14px;padding-left:22px}.steps li{margin:8px 0;line-height:1.5}.steps .ic{display:inline-block;border:1.5px solid var(--line);border-radius:6px;padding:0 6px;font-weight:800}"
               ".warn{background:#fff4e5;border:1px solid #f3c27a;border-radius:14px;padding:12px 16px;margin:0 0 10px}.warn p{margin:6px 0}.warn .big{display:inline-block;text-decoration:none;margin-top:6px}"
               ".plat{font-weight:900;margin:10px 0 0}.ok{font-weight:800;color:#1f7a45;background:#eaf6ee;border-radius:12px;padding:10px 14px}.hidden{display:none!important}"
               ".big{background:var(--heart);color:#fff;border:0;border-radius:999px;padding:13px 22px;font:800 1rem var(--body);cursor:pointer}"
               ".ghost{background:transparent;border:1.5px solid var(--line);border-radius:999px;padding:11px 18px;font:800 .95rem var(--body);cursor:pointer;color:var(--ink)}"
               ".row{display:flex;flex-wrap:wrap;gap:10px;margin-top:14px}.tp{display:flex;gap:12px;align-items:flex-start;padding:12px 0;border-top:1px solid var(--line);cursor:pointer}"
               ".tp input{width:22px;height:22px;margin-top:2px;accent-color:var(--heart)}.tp b{display:block}.tp small{color:var(--muted);font-size:.9rem}"
               ".msg{font-weight:700;margin:12px 0 0}.feats{display:grid;grid-template-columns:1fr 1fr;gap:12px}.ft{background:var(--wool);border-radius:16px;padding:14px}"
               ".ft span{font-size:1.6rem}.ft b{display:block;margin:4px 0}.ft p{margin:0;color:var(--muted);font-size:.92rem}@media(max-width:600px){.feats{grid-template-columns:1fr}}")
        M = json.dumps({k: d[k] for k in ("s_ok", "s_saved", "s_denied", "s_ios", "s_no", "s_err", "s_offd", "s_test")}, ensure_ascii=False)
        js = f"""<script>
(function(){{
const M={M}, LANG="{lang}", $=id=>document.getElementById(id), show=(id,on=true)=>$(id).classList.toggle("hidden",!on);
const ua=navigator.userAgent, ios=/iphone|ipad|ipod/i.test(ua)||(/Macintosh/.test(ua)&&navigator.maxTouchPoints>1), android=/android/i.test(ua);
const standalone=matchMedia("(display-mode: standalone)").matches||navigator.standalone===true;
const inApp=/Instagram|FBAN|FBAV|FB_IAB|FBIOS|Line\\/|Twitter|TikTok|musical_ly|BytedanceWebview|Snapchat|Pinterest|LinkedInApp/i.test(ua);
if(standalone) show("i-done");
else if(inApp){{show("i-inapp");if(android){{show("i-inapp-and");const c=$("i-chrome");c.href="intent://"+location.host+location.pathname+"#Intent;scheme=https;package=com.android.chrome;end";show("i-chrome");}}else show("i-inapp-ios");}}
else if(ios) show("i-ios"); else if(android) show("i-and"); else show("i-desk");
let deferred=null;
addEventListener("beforeinstallprompt",e=>{{e.preventDefault();deferred=e;show("i-btn");show("i-btn2");}});
["i-btn","i-btn2"].forEach(id=>$(id).onclick=async()=>{{if(!deferred)return;deferred.prompt();await deferred.userChoice;deferred=null;show("i-btn",false);show("i-btn2",false);}});
addEventListener("appinstalled",()=>{{["i-ios","i-and","i-desk"].forEach(x=>show(x,false));show("i-done");}});
// notifications
const msg=(t,err)=>{{$("n-msg").textContent=t;$("n-msg").style.color=err?"var(--heart)":"";}};
const topics=()=>[$("t-we").checked?"we":null,$("t-snow").checked?"snow":null].filter(Boolean);
try{{const t=JSON.parse(localStorage.getItem("mpc-push-topics")||"null");if(t){{$("t-we").checked=t.includes("we");$("t-snow").checked=t.includes("snow");}}}}catch(_){{}}
const supported="serviceWorker" in navigator&&"PushManager" in window&&"Notification" in window;
const b64=s=>{{const p="=".repeat((4-s.length%4)%4),r=atob((s+p).replace(/-/g,"+").replace(/_/g,"/"));return Uint8Array.from([...r].map(c=>c.charCodeAt(0)));}};
async function current(){{if(!supported)return null;const reg=await navigator.serviceWorker.getRegistration();return reg?reg.pushManager.getSubscription():null;}}
function ui(on){{show("n-on",!on);show("n-save",on);show("n-test",on);show("n-off",on);}}
async function save(sub){{const r=await fetch("/api/push",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{action:"subscribe",sub,topics:topics(),lang:LANG}})}});const j=await r.json();if(!j.ok)throw new Error(j.error);try{{localStorage.setItem("mpc-push-topics",JSON.stringify(topics()));}}catch(_){{}}}}
current().then(s=>{{if(s){{ui(true);msg(M.s_ok);}}}}).catch(()=>{{}});
$("n-on").onclick=async()=>{{
  if(ios&&!standalone){{msg(M.s_ios,true);return;}}
  if(!supported){{msg(M.s_no,true);return;}}
  try{{
    const perm=await Notification.requestPermission();
    if(perm!=="granted"){{msg(M.s_denied,true);return;}}
    const reg=await navigator.serviceWorker.register("/sw.js");await navigator.serviceWorker.ready;
    const k=await (await fetch("/api/push?key")).json();
    const sub=await reg.pushManager.subscribe({{userVisibleOnly:true,applicationServerKey:b64(k.key)}});
    await save(sub.toJSON());ui(true);msg(M.s_ok);
    try{{window.va&&window.va("event",{{name:"notifications_on"}});}}catch(_){{}}
  }}catch(e){{msg(M.s_err,true);}}
}};
$("n-save").onclick=async()=>{{try{{const s=await current();if(s){{await save(s.toJSON());msg(M.s_saved);}}}}catch(e){{msg(M.s_err,true);}}}};
$("n-test").onclick=async()=>{{try{{const s=await current();if(!s)return;const r=await (await fetch("/api/push",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{action:"test",endpoint:s.endpoint}})}})).json();msg(r.ok?M.s_test:M.s_err,!r.ok);}}catch(e){{msg(M.s_err,true);}}}};
$("n-off").onclick=async()=>{{try{{const s=await current();if(s){{await fetch("/api/push",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{action:"unsubscribe",endpoint:s.endpoint}})}});await s.unsubscribe();}}ui(false);msg(M.s_offd);}}catch(e){{msg(M.s_err,true);}}}};
}})();
</script>"""
        write(path, page(lang, path, alt, d["title"], H.escape(d["desc"]), "📲 " + ("L'appli" if lang == "fr" else "The app"), d["h1"], d["intro"], body, css=css, js=js))


if __name__ == "__main__":
    qf_pages(); venir_pages(); prop_pages(); app_pages()
