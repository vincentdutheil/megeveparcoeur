#!/usr/bin/env python3
"""Base de connaissances du chatbot (data/chat-kb.json).

Usage : python3 tools/gen_chat_kb.py   (depuis la racine, après gen_pages / gen_ski / build_en)

Deux parties :
- "faq" : réponses rédigées à la main, utilisées directement dans le navigateur (gratuit, sans limite,
  sans IA). Champ "live" : la question dépend de données du jour (agenda, neige) → on préfère l'IA si elle est dispo.
- "chunks" : le texte des pages du site, découpé par section, que /api/chat donne à l'IA (Groq) comme
  seule source pour répondre aux questions que la FAQ ne couvre pas.
Relancer après toute modification importante des pages (le build Vercel ne le fait pas tout seul).
"""
import os, re, json, html as H, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --------------------------------------------------------------------------- FAQ (FR / EN)
# kw : mots-clés (sans accents, en minuscules ; « xxx* » accepte tout mot qui commence par xxx ; « ~xxx » compte pour moitié)
FAQ = [
 dict(id="forfait-prix", kw=["forfait*", "prix", "tarif*", "combien", "coute", "pass", "price*", "cost*", "skipass", "ticket*"],
  fr="Forfait journée adulte 2026-2027 : <b>65 €</b> sur l'Évasion Mont-Blanc (tout le domaine, 400 km), <b>52,50 €</b> sur les Portes du Mont-Blanc (Jaillet, Combloux, La Giettaz). En ligne, l'Évasion démarre à 32 € la journée si vous achetez 3 jours avant. Tous les tarifs (4 h, 6 jours, saison, enfants, seniors) sont sur la page ski.",
  en="Adult day pass 2026-2027: <b>€65</b> on Évasion Mont-Blanc (the whole area, 400 km), <b>€52.50</b> on Portes du Mont-Blanc (Jaillet, Combloux, La Giettaz). Online, an Évasion day starts at €32 if bought 3 days ahead. All prices (4 hours, 6 days, season, children, seniors) are on the skiing page.",
  u_fr="/skier/#prix", u_en="/en/skiing/#prices"),
 dict(id="quel-forfait", kw=["quel", "lequel", "difference", "evasion", "portes", "which", "domaine*", "area*", "versant*"],
  fr="Deux forfaits : l'<b>Évasion Mont-Blanc</b> donne accès à tout (Rochebrune, Côte 2000, Mont d'Arbois, Saint-Gervais, Saint-Nicolas, plus le Jaillet, Combloux, La Giettaz et Les Contamines). Le <b>Portes du Mont-Blanc</b>, moins cher, est limité au Jaillet, à Combloux et à La Giettaz.",
  en="Two passes: <b>Évasion Mont-Blanc</b> covers everything (Rochebrune, Côte 2000, Mont d'Arbois, Saint-Gervais, Saint-Nicolas, plus Le Jaillet, Combloux, La Giettaz and Les Contamines). The cheaper <b>Portes du Mont-Blanc</b> is limited to Le Jaillet, Combloux and La Giettaz.",
  u_fr="/skier/", u_en="/en/skiing/"),
 dict(id="relie", kw=["relie*", "skis", "pieds", "rejoindre", "linked", "connect*", "~combloux", "~jaillet", "~rochebrune", "~arbois"],
  fr="Megève a deux versants <b>non reliés skis aux pieds</b> : d'un côté Rochebrune, Côte 2000, Mont d'Arbois, la Princesse, Saint-Gervais et Saint-Nicolas-de-Véroce ; de l'autre le Jaillet, Combloux et La Giettaz. Pour passer de l'un à l'autre, on traverse Megève en voiture ou en Meg'bus gratuit.",
  en="Megève has two sides <b>not linked on skis</b>: on one side Rochebrune, Côte 2000, Mont d'Arbois, the Princesse, Saint-Gervais and Saint-Nicolas-de-Véroce; on the other Le Jaillet, Combloux and La Giettaz. To switch sides, cross Megève by car or on the free Meg'bus.",
  u_fr="/skier/", u_en="/en/skiing/"),
 dict(id="plan-pistes", kw=["plan*", "carte*", "pistes", "map*", "piste*", "runs"],
  fr="Les plans des pistes : <a href=\"https://forfait.megeve.com/hiver/plan-des-pistes-temps-reel/\" target=\"_blank\" rel=\"noopener\">Évasion Mont-Blanc (temps réel)</a> et <a href=\"https://www.lesportesdumontblanc.fr/hiver/plan-des-pistes-megeve-saintgervais-combloux-lagiettaz/\" target=\"_blank\" rel=\"noopener\">Portes du Mont-Blanc</a>.",
  en="Piste maps: <a href=\"https://forfait.megeve.com/hiver/en/ski-resort-map/\" target=\"_blank\" rel=\"noopener\">Évasion Mont-Blanc (live)</a> and <a href=\"https://www.lesportesdumontblanc.fr/hiver/plan-des-pistes-megeve-saintgervais-combloux-lagiettaz/\" target=\"_blank\" rel=\"noopener\">Portes du Mont-Blanc</a>.",
  u_fr="/skier/#plans", u_en="/en/skiing/#maps"),
 dict(id="parking", kw=["parking*", "garer", "stationn*", "voiture", "park*", "car"],
  fr="Gratuits au pied des pistes : la <b>Princesse</b> (Demi-Quartier) et <b>Côte 2000</b> à Megève ; <b>les Brons, la Cry et Cuchet</b> à Combloux. Rochebrune et Mont d'Arbois sont des parkings couverts payants (30 min gratuites) ; le Jaillet est en zone bleue.",
  en="Free at the foot of the slopes: the <b>Princesse</b> (Demi-Quartier) and <b>Côte 2000</b> in Megève; <b>Les Brons, la Cry and Cuchet</b> in Combloux. Rochebrune and Mont d'Arbois are paid covered car parks (first 30 min free); Le Jaillet is a blue zone.",
  u_fr="/skier/#parkings", u_en="/en/skiing/#parkings"),
 dict(id="ouverture", kw=["ouvre*", "ouverture", "ferme*", "fermeture", "dates", "quand", "saison", "open*", "clos*", "when", "season"],
  fr="Hiver 2026-2027 : Megève prévoit une pré-ouverture les 5-6 décembre, une ouverture partielle dès le 12 décembre et l'ouverture générale le <b>19 décembre</b>, jusqu'au <b>4 avril 2027</b>. Les Portes du Mont-Blanc ouvrent du 19 décembre au 21 mars. Tout dépend de la neige.",
  en="Winter 2026-2027: Megève plans an early opening on 5-6 December, partial opening from 12 December and full opening on <b>19 December</b>, until <b>4 April 2027</b>. Portes du Mont-Blanc is open from 19 December to 21 March. Everything depends on snow.",
  u_fr="/skier/", u_en="/en/skiing/"),
 dict(id="debutant", kw=["debut*", "apprendre", "premiere", "beginner*", "learn*", "first"],
  fr="Forfaits débutants : <b>29 €</b> la journée à Rochebrune / Mont d'Arbois (15 € pour le seul Petit Rochebrune), <b>18 €</b> aux Portes du Mont-Blanc. Les écoles de ski (ESF et indépendantes) proposent des cours à Megève comme à Combloux.",
  en="Beginner passes: <b>€29</b> a day at Rochebrune / Mont d'Arbois (€15 for Petit Rochebrune only), <b>€18</b> on Portes du Mont-Blanc. Ski schools (ESF and independent) run lessons in both Megève and Combloux.",
  u_fr="/skier/", u_en="/en/skiing/"),
 dict(id="reductions", kw=["gratuit*", "reduction*", "promo*", "moins", "cher", "famille", "enfant*", "senior*", "free", "discount*", "cheap*", "family", "child*", "kids"],
  fr="Gratuit pour les moins de 5 ans (support 2 €), -50 % dès 80 ans, -10 % famille (4 forfaits dont 2 enfants), -20 % en début et fin de saison, et des prix réduits en ligne (dès 32 € la journée à J-3, 6 jours au prix de 5 à J-10).",
  en="Free for under-5s (€2 card), 50% off from age 80, 10% family discount (4 passes incl. 2 children), 20% off early and late season, and cheaper online prices (from €32 a day 3 days ahead, 6 days for the price of 5 ten days ahead).",
  u_fr="/skier/#prix", u_en="/en/skiing/#prices"),
 dict(id="megbus", kw=["megbus", "meg", "bus", "navette*", "shuttle*", "transport*"],
  fr="Le <b>Meg'bus</b> est la navette gratuite de Megève (3 lignes en hiver) entre le village et les remontées. Les lignes régionales Y82 et Y83 relient Combloux, Megève, Praz-sur-Arly, Sallanches et Saint-Gervais.",
  en="The <b>Meg'bus</b> is Megève's free shuttle (3 lines in winter) between the village and the lifts. Regional lines Y82 and Y83 link Combloux, Megève, Praz-sur-Arly, Sallanches and Saint-Gervais.",
  u_fr="/venir/", u_en="/en/getting-here/"),
 dict(id="venir", kw=["venir", "acces", "geneve", "aeroport", "avion", "route", "getting", "geneva", "airport", "drive"],
  fr="Depuis Genève : environ 70 km, compter 1 h hors bouchons (A40, sortie Sallanches). L'aéroport le plus proche est Genève. En train, la gare est Sallanches-Combloux-Megève, puis le bus Y83 (environ 25 min jusqu'à Megève).",
  en="From Geneva: about 70 km, around 1 hour without traffic (A40, Sallanches exit). The nearest airport is Geneva. By train, the station is Sallanches-Combloux-Megève, then bus Y83 (about 25 minutes to Megève).",
  u_fr="/venir/", u_en="/en/getting-here/"),
 dict(id="train", kw=["train", "gare", "sncf", "ter", "station", "railway"],
  fr="La gare la plus proche est <b>Sallanches-Combloux-Megève</b> (TER). De là, le bus régional Y83 monte à Combloux, Megève et Praz-sur-Arly (environ 25 min jusqu'à Megève).",
  en="The nearest station is <b>Sallanches-Combloux-Megève</b> (TER regional trains). From there, regional bus Y83 goes up to Combloux, Megève and Praz-sur-Arly (about 25 minutes to Megève).",
  u_fr="/venir/", u_en="/en/getting-here/"),
 dict(id="equipement", kw=["pneu*", "chaine*", "chaussette*", "equipement*", "hiver", "tyre*", "tire*", "chain*", "winter"],
  fr="En Haute-Savoie, du 1er novembre au 31 mars, les équipements hiver sont obligatoires (loi Montagne) : pneus hiver, ou chaînes / chaussettes à neige dans le coffre.",
  en="In Haute-Savoie, from 1 November to 31 March, winter equipment is compulsory (Mountain Law): winter tyres, or snow chains / snow socks in the boot.",
  u_fr="/venir/", u_en="/en/getting-here/"),
 dict(id="neige", live=True, kw=["neige", "enneigement", "meteo", "temps", "snow*", "weather", "froid", "temperature*", "cm"],
  fr="La page Météo & neige montre la neige au sol et les chutes prévues sur 7 jours pour Megève, Combloux et les stations voisines, mises à jour plusieurs fois par jour.",
  en="The Snow & weather page shows snow on the ground and the 7-day snowfall forecast for Megève, Combloux and nearby resorts, updated several times a day.",
  u_fr="/meteo/", u_en="/en/meteo/"),
 dict(id="webcams", kw=["webcam*", "camera*", "direct", "live", "voir", "see"],
  fr="Les webcams en direct de Megève (village, Rochebrune, Mont d'Arbois…) et de Combloux sont sur notre page Webcams.",
  en="Live webcams of Megève (village, Rochebrune, Mont d'Arbois…) and Combloux are on our Webcams page.",
  u_fr="/webcams/", u_en="/en/webcams/"),
 dict(id="agenda", live=True, kw=["agenda", "evenement*", "evenements", "sortie*", "faire", "week", "weekend", "samedi", "dimanche", "aujourd", "demain", "concert*", "spectacle*", "event*", "whats", "today", "tomorrow", "saturday", "sunday", "do"],
  fr="L'agenda de Megève, Combloux, Demi-Quartier et Praz-sur-Arly est sur la page « Que faire ? », avec des sélections : ce week-end, aujourd'hui, avec des enfants, quand il pleut, gratuit.",
  en="What's on in Megève, Combloux, Demi-Quartier and Praz-sur-Arly is on the \"Things to do\" page, with selections: this weekend, today, with kids, rainy day, free.",
  u_fr="/que-faire/", u_en="/en/things-to-do/"),
 dict(id="enfants", live=True, kw=["enfant*", "famille", "kids", "child*", "family", "bebe*"],
  fr="Les sorties avec des enfants à Megève et autour sont regroupées sur la page « Avec des enfants ».",
  en="Outings with kids in and around Megève are gathered on the \"With kids\" page.",
  u_fr="/que-faire/avec-des-enfants/", u_en="/en/things-to-do/with-kids/"),
 dict(id="pluie", live=True, kw=["pluie", "pleut", "pleuvoir", "mauvais", "interieur", "rain*", "indoor*", "piscine*", "pool*", "palais", "spa", "balneo*", "musee*", "museum*", "cinema*", "patinoire", "rink"],
  fr="Quand il pleut : piscine et Balnéoforme du Palais, musées, cinéma, ateliers… La sélection du moment est sur la page « Quand il pleut ».",
  en="On a rainy day: the Palais pool and spa, museums, cinema, workshops… Current ideas are on the \"Rainy day\" page.",
  u_fr="/que-faire/quand-il-pleut/", u_en="/en/things-to-do/rainy-day/"),
 dict(id="balades", kw=["balade*", "randonnee*", "rando", "raquette*", "marche*", "promenade*", "walk*", "hike*", "hiking", "snowshoe*"],
  fr="Itinéraires balisés à pied et en raquettes, été comme hiver, avec durée, dénivelé et carte : voyez notre page Balades.",
  en="Signposted walking and snowshoe routes, summer and winter, with duration, elevation and map: see our Walks page.",
  u_fr="/balades/", u_en="/en/balades/"),
 dict(id="fond", kw=["fond", "nordique", "skating", "cross", "country", "nordic"],
  fr="Megève compte une quarantaine de kilomètres de ski de fond sur trois sites : la Livraz – Côte 2000 (le principal), le golf du Mont d'Arbois et Odier, relié à Combloux. Redevance au chalet d'accueil.",
  en="Megève has about forty kilometres of cross-country trails on three sites: la Livraz – Côte 2000 (the main one), the Mont d'Arbois golf course and Odier, linked to Combloux. Trail pass at the welcome chalet.",
  u_fr="/skier/", u_en="/en/skiing/"),
 dict(id="luge", kw=["luge*", "traineau*", "sledg*", "sled*", "toboggan*"],
  fr="La <b>Luge Princesse</b> (3 km sur neige, offerte avec un forfait Évasion acheté à Megève) et la luge 4S de Combloux.",
  en="The <b>Luge Princesse</b> (3 km on snow, free with an Évasion pass bought in Megève) and the Luge 4S in Combloux.",
  u_fr="/skier/", u_en="/en/skiing/"),
 dict(id="cours", kw=["cours", "ecole*", "esf", "moniteur*", "lecon*", "lesson*", "school*", "instructor*", "location", "louer", "rent*", "materiel"],
  fr="Écoles de ski (ESF et écoles indépendantes) et magasins de location à Megève comme à Combloux. Réservez tôt pour Noël et février ; les offices de tourisme ont la liste complète.",
  en="Ski schools (ESF and independent schools) and rental shops in both Megève and Combloux. Book early for Christmas and February; the tourist offices have the full list.",
  u_fr="/skier/", u_en="/en/skiing/"),
 dict(id="proposer", kw=["proposer", "organise*", "ajouter", "publier", "submit*", "organis*", "add"],
  fr="Vous organisez un événement ? Proposez-le avec le formulaire : il sera relu puis publié dans l'agenda.",
  en="Organising an event? Submit it with the form: it is reviewed and then published in the calendar.",
  u_fr="/proposer/", u_en="/en/submit-event/"),
 dict(id="appli", kw=["appli*", "application", "app", "notification*", "installer", "install*", "telephone", "phone"],
  fr="Megève par cœur s'installe comme une appli sur votre téléphone (gratuit, sans store), avec des notifications pour le programme du week-end et les grosses chutes de neige.",
  en="Megève par cœur installs like an app on your phone (free, no app store), with notifications for the weekend programme and big snowfalls.",
  u_fr="/app/", u_en="/en/app/"),
 dict(id="office", kw=["office", "tourisme", "contact", "telephone", "renseignement*", "tourist", "information"],
  fr="Offices de tourisme : <a href=\"https://www.megeve-tourisme.fr/\" target=\"_blank\" rel=\"noopener\">Megève Tourisme</a>, <a href=\"https://www.combloux.com/\" target=\"_blank\" rel=\"noopener\">Combloux</a> et <a href=\"https://www.prazsurarly.com/\" target=\"_blank\" rel=\"noopener\">Praz-sur-Arly</a>.",
  en="Tourist offices: <a href=\"https://www.megeve-tourisme.fr/en/\" target=\"_blank\" rel=\"noopener\">Megève Tourisme</a>, <a href=\"https://www.combloux.com/en/\" target=\"_blank\" rel=\"noopener\">Combloux</a> and <a href=\"https://www.prazsurarly.com/en/\" target=\"_blank\" rel=\"noopener\">Praz-sur-Arly</a>.",
  u_fr="/venir/", u_en="/en/getting-here/"),
]

# --------------------------------------------------------------------------- pages découpées pour l'IA
PAGES = [("skier", "/skier/", "/en/skiing/"), ("venir", "/venir/", "/en/getting-here/"), ("balades", "/balades/", "/en/balades/"),
         ("que-faire", "/que-faire/", "/en/things-to-do/"), ("app", "/app/", "/en/app/"), ("proposer", "/proposer/", "/en/submit-event/"),
         ("meteo", "/meteo/", "/en/meteo/")]


def text(h):
    h = re.sub(r"(?is)<(script|style|svg|template)[^>]*>.*?</\1>", " ", h)
    h = re.sub(r"(?i)<br\s*/?>|</(p|li|tr|h\d|div|section|summary|details)>", "\n", h)
    h = re.sub(r"(?i)</t[dh]>", " · ", h)
    h = re.sub(r"<[^>]+>", " ", h)
    h = H.unescape(h)
    h = re.sub(r"[ \t ]+", " ", h)
    return re.sub(r"\n\s*\n+", "\n", h).strip()


def chunks(path, url):
    h = open(os.path.join(ROOT, path.strip("/"), "index.html"), encoding="utf-8").read()
    main = re.search(r"(?is)<main[^>]*>(.*)</main>", h)
    title = re.sub(r"\s+", " ", H.unescape(re.sub("<[^>]+>", "", re.search(r"(?is)<h1[^>]*>(.*?)</h1>", h).group(1)))).strip()
    body = main.group(1) if main else h
    out = []
    for part in re.split(r"(?i)(?=<h2)", body):
        m = re.search(r"(?is)<h2[^>]*>(.*?)</h2>", part)
        head = text(m.group(1)) if m else ""
        t = text(part)
        if len(t) < 60: continue
        for i in range(0, len(t), 1400):  # sections longues coupées en morceaux d'environ 1 400 caractères
            out.append({"u": url, "t": f"{title} — {head}" if head else title, "x": t[i:i + 1400]})
    return out


def main():
    kb = {"faq": FAQ, "chunks": {"fr": [], "en": []}}
    for _, fr, en in PAGES:
        kb["chunks"]["fr"] += chunks(fr, fr)
        kb["chunks"]["en"] += chunks(en, en)
    p = os.path.join(ROOT, "data", "chat-kb.json")
    json.dump(kb, open(p, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("ok data/chat-kb.json :", len(FAQ), "réponses,", len(kb["chunks"]["fr"]), "+", len(kb["chunks"]["en"]), "morceaux,", os.path.getsize(p) // 1024, "Ko")


if __name__ == "__main__":
    main()
