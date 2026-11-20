#!/usr/bin/env python3
"""Génère la version anglaise du site (/en/...) à partir des pages françaises.

Usage : python3 tools/build_en.py   (depuis la racine du dépôt)

Pour chaque page FR, on remplace les textes via un dictionnaire FR→EN
(chaque entrée doit exister, sinon le script s'arrête : ça évite qu'une
modification de la page FR passe inaperçue), on réécrit les liens vers
/en/..., et on ajoute les balises hreflang des deux côtés.
Relancer ce script après chaque modification d'une page FR.
"""
import re, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://www.megeveparcoeur.fr"
SUB = "meteo|webcams|balades|carte|boutique"

NAV_FR = [("#agenda", "Agenda"), ("meteo/", "Météo &amp; neige"), ("webcams/", "Webcams"), ("balades/", "Balades"),
          ("carte/", "Carte"), ("#galerie", "Galerie"), ("maths/", "Maths des frileux"), ("boutique/", "Boutique")]
NAV_EN = [("#agenda", "What's on"), ("meteo/", "Snow &amp; weather"), ("webcams/", "Webcams"), ("balades/", "Walks"),
          ("carte/", "Map"), ("#galerie", "Gallery"), ("maths/", "Kids' maths (FR)"), ("boutique/", "Shop")]


def nav(items, prefix, path, other):
    """prefix '/' (FR) or '/en/' ; path '' or 'meteo/' ; other = (href, label, lang) of the language switch."""
    li = []
    for href, label in items:
        cur = ' aria-current="page"' if href == path else ''
        h = "/maths/" if href == "maths/" else f"{prefix}{href}"
        li.append(f'      <li><a href="{h}"{cur}>{label}</a></li>')
    h, l, lang = other
    li.append(f'      <li><a class="lang" href="{h}" lang="{lang}" hreflang="{lang}">{l}</a></li>')
    return "<ul>\n" + "\n".join(li) + "\n    </ul>"


def head_links(html, path, lang):
    """canonical + hreflang pair, idempotent."""
    html = re.sub(r'\n<link rel="(canonical|alternate)"[^>]*>', '', html)
    own = f"{SITE}{'/en' if lang == 'en' else ''}/{path}"
    tags = (f'\n<link rel="canonical" href="{own}">'
            f'\n<link rel="alternate" hreflang="fr" href="{SITE}/{path}">'
            f'\n<link rel="alternate" hreflang="en" href="{SITE}/en/{path}">'
            f'\n<link rel="alternate" hreflang="x-default" href="{SITE}/{path}">')
    return re.sub(r'(<title>.*?</title>)', lambda m: m.group(1) + tags, html, count=1, flags=re.S)


def set_nav(html, items, prefix, path, other):
    return re.sub(r'(<header class="top">.*?)<ul>.*?</ul>', lambda m: m.group(1) + nav(items, prefix, path, other),
                  html, count=1, flags=re.S)


def apply(html, pairs, page, strict=True):
    for fr, en in pairs:
        if fr not in html:
            if strict:
                sys.exit(f"[{page}] texte introuvable : {fr[:90]!r}")
            continue
        html = html.replace(fr, en)
    return html


def rewrite_links(html, path):
    if path:  # sous-page : liens relatifs ../
        html = re.sub(r'href="\.\./((?:%s)/[^"]*|#[^"]*)?"' % SUB, lambda m: f'href="/en/{m.group(1) or ""}"', html)
        html = re.sub(r'(href|src)="\.\./', r'\1="/', html)
    else:  # page d'accueil (avec <base href="/">)
        html = re.sub(r'href="((?:%s)/)"' % SUB, r'href="/en/\1"', html)
        html = re.sub(r'href="#', 'href="/en/#', html)
    # liens absolus vers les pages du site
    html = re.sub(r'href="/((?:%s)/[^"]*)"' % SUB, r'href="/en/\1"', html)
    html = re.sub(r'(?<!<base )href="/(#[^"]*)?"', lambda m: f'href="/en/{m.group(1) or ""}"', html)
    return html.replace('href="__FR__"', 'href="/"').replace('href="__EN__', 'href="/en/')


# ---------------------------------------------------------------- textes communs
COMMON = [
    ('aria-label="Megève par cœur, accueil"', 'aria-label="Megève par cœur, home"'),
    ('>Accueil</a>', '>Home</a>'),
    ('<a href="/en/#agenda">Agenda</a>', '<a href="/en/#agenda">What\'s on</a>'),
    ('>Météo &amp; neige</a>', '>Snow &amp; weather</a>'),
    ('>Balades</a>', '>Walks</a>'),
    ('>Carte</a>', '>Map</a>'),
]

# ---------------------------------------------------------------- accueil
PHOTOS = {
    "Le Mont-Blanc et la vallée de Megève": "Mont Blanc and the Megève valley",
    "Entre les sapins, la vallée": "The valley, between the fir trees",
    "Ruisseau en forêt": "A stream in the forest",
    "Le mini-film du festival (musique : Akhilleus)": "The festival short film (music: Akhilleus)",
    "La lune au-dessus des crêtes enneigées": "The moon above the snowy ridges",
    "Premières neiges sur les crêtes": "First snow on the ridges",
    "Les crêtes au soleil couchant": "The ridges at sunset",
    "Cueillette de coulemelles": "Picking parasol mushrooms",
    "Une coulemelle au bord du chemin": "A parasol mushroom by the path",
    "Le village sous la brume, le Mont-Blanc en majesté": "The village in the mist, Mont Blanc in all its glory",
    "Un chalet niché dans les couleurs d'automne": "A chalet tucked into autumn colours",
    "Pommes de pin et Aravis sous la neige": "Pine cones and the snowy Aravis",
    "Une montgolfière au-dessus du Mont-Blanc": "A hot-air balloon above Mont Blanc",
    "La montgolfière, quelques instants plus tard": "The balloon, a few moments later",
    "Lever de soleil sur le Mont-Blanc après la première neige": "Sunrise on Mont Blanc after the first snow",
    "L'aube sur le massif, l'herbe givrée": "Dawn on the massif, frosty grass",
    "Départ au golf du Mont d'Arbois": "Teeing off at the Mont d'Arbois golf course",
    "Sur le green": "On the green",
    "La forêt s'embrase en octobre": "The forest ablaze in October",
    "Lumière dorée sur la forêt": "Golden light on the forest",
    "Belle rencontre aux Toquicimes avec Chicandier": "Meeting Chicandier at Les Toquicimes",
    "Balade en famille, vue sur le massif": "Family walk with a view of the massif",
    "Vue sur la vallée depuis le pierrier": "The valley seen from the scree",
    "Amanites tue-mouches en sous-bois": "Fly agarics in the undergrowth",
    "Un chemin d'amanites tue-mouches": "A trail of fly agarics",
    "Un chamois sous le télésiège": "A chamois under the chairlift",
    "Chamois dans l'alpage": "Chamois in the alpine pasture",
    "Alpages et sommets enneigés": "Pastures and snowy peaks",
    "Mer de nuages au petit matin": "A sea of clouds at daybreak",
    "Rencontre au pâturage, face aux sommets enneigés": "A pasture encounter, facing the snowy peaks",
    "Sapins et sommets dans les nuages": "Fir trees and peaks in the clouds",
    "Démonstration en scène": "A live cooking demo",
    "Le dôme végétal": "The green dome",
    "Miels et confitures du terroir": "Local honeys and jams",
    "Un atelier au cœur du salon": "A workshop at the heart of the fair",
    "Pause lecture au salon": "A reading break at the fair",
    "L'entrée du festival au Palais": "The festival entrance at the Palais",
    "Dans les pierriers, sous les falaises": "In the scree, below the cliffs",
    "Un champignon bleu-vert dans la mousse": "A blue-green mushroom in the moss",
    "Mousse et sous-bois": "Moss and undergrowth",
    "À travers les herbes d'automne": "Through the autumn grass",
    "Cascade et bouleaux dorés": "Waterfall and golden birches",
    "Un bouleau doré au pied des falaises": "A golden birch below the cliffs",
    "Sous les grands épicéas": "Under the tall spruces",
}
CATS = {"Automne": "Autumn", "Hiver": "Winter", "Printemps": "Spring", "Été": "Summer", "Événements": "Events"}

import json as _json
TR_JS = ("const TT=" + _json.dumps(PHOTOS, ensure_ascii=False) + ",CT=" + _json.dumps(CATS, ensure_ascii=False) +
         ";\nfunction tr(p){if(TT[p.t])p.t=TT[p.t];if(CT[p.cat])p.cat=CT[p.cat];return p;}\n")

NL_EN = '''<div class="nl" id="newsletter">
  <div><div class="kicker" style="color:#f3c27a">📬 Every Thursday</div>
    <h2>This week's events by email</h2>
    <p>Every event in Megève, Combloux, Demi-Quartier and Praz, in your inbox on Thursdays. Free, no ads, one-click unsubscribe. (The email is in French.)</p></div>
  <form id="nl-form" novalidate>
    <div class="row"><input type="email" name="email" required autocomplete="email" placeholder="you@email.com" aria-label="Email"><button type="submit">Sign me up</button></div>
    <input class="hp" type="text" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">
    <label class="c"><input type="checkbox" name="consent" required> I agree to receive the Megève par cœur events email. My address is only used for this.</label>
    <div class="msg" id="nl-msg" aria-live="polite"></div>
  </form>
</div>'''

HOME = [
    ('<title>Megève par cœur · Agenda, météo, webcams de Megève, Combloux, Demi-Quartier, Praz-sur-Arly</title>',
     "<title>Megève par cœur · What's on, snow, webcams in Megève, Combloux, Demi-Quartier, Praz-sur-Arly</title>"),
    ('''content="Que faire à Megève ce week-end ? L'agenda le plus complet de Megève, Combloux, Demi-Quartier et Praz-sur-Arly : marchés, concerts, spectacles, sorties enfants, mis à jour chaque jeudi. Plus météo, neige et webcams."''',
     '''content="What's on in Megève this weekend? The most complete events guide for Megève, Combloux, Demi-Quartier and Praz-sur-Arly: markets, concerts, shows, kids' activities, updated every Thursday. Plus snow forecast, webcams, walks and a map."'''),
    ('<span class="sub">Agenda, neige &amp; bons plans à Megève et alentours</span>', '<span class="sub">What\'s on, snow &amp; local tips in Megève and around</span>'),
    ('<div class="kicker">Megève &amp; ses alentours</div>', '<div class="kicker">Megève &amp; around</div>'),
    ('<p>Pour les amoureux de Megève : la région en randonnée, à vélo, à ski ou en trail, et les bons moments du village, saison après saison.</p>',
     '<p>For everyone who loves Megève: the area on foot, by bike, on skis or trail running, and the best moments in the village, season after season.</p>'),
    ('Suivre @megeveparcoeur</a>', 'Follow @megeveparcoeur</a>'),
    (">Voir l'agenda de Megève</a>", ">See what's on in Megève</a>"),
    (">📬 L'agenda par e-mail</a>", ">📬 Events by email</a>"),
    ('aria-label="Secouer la boule à neige"', 'aria-label="Shake the snow globe"'),
    ('aria-label="La place du village de Megève sous la neige, la nuit, dans une boule de Noël"',
     'aria-label="Megève village square under the snow at night, inside a Christmas bauble"'),
    ('<p class="hint">❄ Touchez la boule pour la secouer</p>', '<p class="hint">❄ Tap the globe to shake it</p>'),
    ('aria-label="Mini-film : Les Toquicimes à Megève"', 'aria-label="Short film: Les Toquicimes in Megève"'),
    ('<div class="kicker">À la une</div>', '<div class="kicker">Featured</div>'),
    ('<h2>Les Toquicimes en images</h2>', '<h2>Les Toquicimes on film</h2>'),
    ('<p>Une minute au cœur du festival gastronomique de Megève : les chefs, le marché des producteurs, les saveurs du terroir. Filmé et monté par Vincent.</p>',
     "<p>One minute at the heart of Megève's food festival: the chefs, the producers' market, the local flavours. Filmed and edited by Vincent.</p>"),
    ('♪ Musique originale : <b>Akhilleus</b>', '♪ Original music: <b>Akhilleus</b>'),
    ('<div class="kicker">Galerie</div>', '<div class="kicker">Gallery</div>'),
    ('<h2>Megève au fil des saisons</h2>', '<h2>Megève through the seasons</h2>'),
    ("<p>Les photos de Vincent, prises au fil des balades : lever de soleil sur le Mont-Blanc, forêts d'automne et rendez-vous du village.</p>",
     "<p>Vincent's photos, taken on his walks: sunrise on Mont Blanc, autumn forests and village events.</p>"),
    ('aria-label="Filtrer les photos"', 'aria-label="Filter photos"'),
    ("<p class=\"note\">Touchez une photo pour l'agrandir.</p>", '<p class="note">Tap a photo to enlarge it.</p>'),
    ('<div class="kicker">Vos photos</div>', '<div class="kicker">Your photos</div>'),
    ('<h2>Megève vue par vous</h2>', '<h2>Megève through your eyes</h2>'),
    ('<p>Partagez vos plus belles photos de Megève, Combloux, Demi-Quartier ou Praz avec <b>#megeveparcoeur</b> ou en identifiant <b>@megeveparcoeur</b> : chaque semaine, nos coups de cœur sont publiés ici et sur Instagram, avec votre nom.</p>',
     '<p>Share your best photos of Megève, Combloux, Demi-Quartier or Praz with <b>#megeveparcoeur</b> or by tagging <b>@megeveparcoeur</b>: every week, our favourites are featured here and on Instagram, with your name.</p>'),
    ('>📷 Partager sur Instagram</a>', '>📷 Share on Instagram</a>'),
    ('Les premières photos de la communauté arrivent bientôt. La vôtre sera peut-être la première ✨',
     'The first community photos are coming soon. Yours could be the first ✨'),
    ('<h2>L\'agenda de Megève</h2>', "<h2>What's on in Megève</h2>"),
    ('<p>Les temps forts de Megève et des villages voisins : Combloux, Demi-Quartier et Praz-sur-Arly. Dates sous réserve : vérifiez sur le lien de chaque événement avant de venir.</p>',
     '<p>The highlights of Megève and the neighbouring villages: Combloux, Demi-Quartier and Praz-sur-Arly. Dates may change: please check the link of each event before you go.</p>'),
    ('aria-label="Filtrer par village"', 'aria-label="Filter by village"'),
    ('data-l="all">Tout</button>', 'data-l="all">All</button>'),
    ('aria-label="Filtres rapides"', 'aria-label="Quick filters"'),
    ('<div class="kicker">Coups de cœur</div>', '<div class="kicker">Our favourites</div>'),
    ('<h2>Nos balades préférées</h2>', '<h2>Our favourite walks</h2>'),
    ("<p>Les itinéraires qu'on refait chaque année, à pied, à vélo ou en raquettes.</p>",
     '<p>The routes we come back to every year, on foot, by bike or on snowshoes.</p>'),
    ('<div class="meta">Rando · Patrimoine</div><h3>Le chemin du Calvaire</h3><p>Une promenade au-dessus du village, entre alpages et vieilles fermes, avec vue sur toute la vallée.</p>',
     '<div class="meta">Hike · Heritage</div><h3>Le chemin du Calvaire</h3><p>A walk above the village, between pastures and old farms, with a view over the whole valley.</p>'),
    ('<div class="meta">Rando · Panorama</div><h3>Les crêtes du Mont Joly</h3><p>Le grand classique pour les panoramas : le massif du Mont-Blanc en face, les Aravis dans le dos.</p>',
     '<div class="meta">Hike · Viewpoint</div><h3>The Mont Joly ridges</h3><p>The great classic for views: the Mont Blanc massif in front of you, the Aravis behind.</p>'),
    ("<div class=\"meta\">Ski · Raquettes</div><h3>La Côte 2000</h3><p>Le secteur le plus sauvage du domaine, idéal pour une journée au calme loin de l'agitation du village.</p>",
     '<div class="meta">Ski · Snowshoes</div><h3>La Côte 2000</h3><p>The wildest part of the ski area, perfect for a quiet day away from the bustle of the village.</p>'),
    ('>🗺️ La carte des beaux coins</a>', '>🗺️ Map of our favourite spots</a>'),
    ('>🥾 Balades &amp; raquettes balisées</a>', '>🥾 Signposted walks &amp; snowshoe trails</a>'),
    ('<div class="kicker" style="color:#ff8a97">Boutique solidaire</div>', '<div class="kicker" style="color:#ff8a97">Charity shop</div>'),
    ('<h2>Portez Megève sur le cœur</h2>', '<h2>Wear Megève close to your heart</h2>'),
    ('<p>En partenariat avec la Coupe des Banques Genevoises : casquettes, tours de cou, tasses et protections solaires, dont 100 % des bénéfices sont reversés à une association, annoncée prochainement.</p>',
     '<p>In partnership with the Coupe des Banques Genevoises: caps, neck warmers, mugs and sun protection, with 100% of profits going to a charity, to be announced soon.</p>'),
    ('>Découvrir la boutique →</a>', '>Visit the shop →</a>'),
    ('aria-label="Produits prévus"', 'aria-label="Planned products"'),
    ('</svg>Casquette</div>', '</svg>Cap</div>'),
    ('</svg>Tour de cou</div>', '</svg>Neck warmer</div>'),
    ('</svg>Tasse</div>', '</svg>Mug</div>'),
    ('aria-label="Photo agrandie"', 'aria-label="Enlarged photo"'),
    ('aria-label="Fermer"', 'aria-label="Close"'),
    ('aria-label="Photo précédente"', 'aria-label="Previous photo"'),
    ('aria-label="Photo suivante"', 'aria-label="Next photo"'),
    ('<span class="xmas">Joyeuses fêtes depuis Megève ✨</span>', '<span class="xmas">Happy holidays from Megève ✨</span>'),
    ('© Megève par cœur · Photos et textes de Vincent ·', '© Megève par cœur · Photos and words by Vincent ·'),
    ('<b>Idées de sorties</b><div class="ag-ideas"><a href="/que-faire/ce-week-end/">🎉 Ce week-end</a><a href="/que-faire/avec-des-enfants/">🧒 Avec des enfants</a><a href="/que-faire/quand-il-pleut/">☔ Quand il pleut</a><a href="/que-faire/gratuit/">🆓 Gratuit</a><a href="/venir/">🚗 Venir &amp; se déplacer</a></div>',
     '<b>Ideas</b><div class="ag-ideas"><a href="__EN__things-to-do/this-weekend/">🎉 This weekend</a><a href="__EN__things-to-do/with-kids/">🧒 With kids</a><a href="__EN__things-to-do/rainy-day/">☔ Rainy day</a><a href="__EN__things-to-do/free/">🆓 Free</a><a href="__EN__getting-here/">🚗 Getting here &amp; around</a></div>'),
    ('<a class="ag-prop" href="/proposer/">📝 Vous organisez un événement ? <u>Proposez-le</u></a>', '<a class="ag-prop" href="__EN__submit-event/">📝 Organising an event? <u>Submit it</u></a>'),
    ('<a href="/que-faire/">Que faire ?</a> · <a href="/venir/">Venir</a> · <a href="/proposer/">Proposer un événement</a>',
     '<a href="__EN__things-to-do/">Things to do</a> · <a href="__EN__getting-here/">Getting here</a> · <a href="__EN__submit-event/">Submit an event</a>'),
    ('<a href="en/">English</a>', '<a href="__FR__" lang="fr" hreflang="fr">Français</a>'),
    ('toLocaleDateString("fr-FR"', 'toLocaleDateString("en-GB"'),
    ('aria-label="Agrandir : ${esc(i.t)}"', 'aria-label="Enlarge: ${esc(i.t)}"'),
    ('${c==="all"?"Tout":esc(c)}', '${c==="all"?"All":esc(c)}'),
    ('"Photo de "+p.by', '"Photo by "+p.by'),
    ("La galerie n\\'a pas pu se charger. Rechargez la page.", "The gallery could not load. Please reload the page."),
    ('.then(d=>{const f=d.filter(', '.then(d=>{d.forEach(tr);const f=d.filter('),
    ('.then(d=>{items=d.sort(', '.then(d=>{d.forEach(tr);items=d.sort('),
    ('<script>\nlet items = [];', '<script>\n' + TR_JS + 'let items = [];'),
]


def home_special(html):
    # bloc newsletter et son script : on reprend la version anglaise
    html, n = re.subn(r'<div class="nl" id="newsletter">.*?</form>\n</div>', lambda m: NL_EN, html, count=1, flags=re.S)
    assert n == 1, "bloc newsletter introuvable"
    pairs = [
        ('M={"ok": "Merci ! Vérifie ta boîte mail pour confirmer ton inscription ✉️", "okdirect": "C\'est noté, à jeudi ! 🎉", "email": "Cette adresse e-mail ne semble pas valide.", "consent": "Coche la case pour accepter de recevoir l\'e-mail.", "soon": "Les inscriptions ouvrent très bientôt, reviens dans quelques jours 🙂", "err": "Oups, ça n\'a pas marché. Réessaie dans un instant."}',
         'M={"ok": "Thanks! Check your inbox to confirm ✉️", "okdirect": "You\'re in, see you Thursday! 🎉", "email": "This email address doesn\'t look right.", "consent": "Please tick the box to agree.", "soon": "Sign-ups open very soon, come back in a few days 🙂", "err": "Oops, something went wrong. Please try again."}'),
        ('"⏳ Inscription en cours…"', '"⏳ Signing you up…"'),
        ('lang:"fr",website', 'lang:"en",website'),
        ('<b>Inscription confirmée !</b>', "<b>You're subscribed!</b>"),
        ('"Un e-mail de confirmation vient de partir : clique sur le lien pour valider."', '"A confirmation email is on its way: click the link to confirm."'),
        ('"Rendez-vous jeudi en fin d\'après-midi dans ta boîte mail. Pense à vérifier tes spams la première fois."',
         '"See you Thursday afternoon in your inbox. Check your spam folder the first time."'),
    ]
    html = apply(html, pairs, "home-nl")
    # chemins relatifs : la page /en/ s'appuie sur la racine du site
    html = html.replace('<head>\n', '<head>\n<base href="/">\n', 1)
    return html


# ---------------------------------------------------------------- météo
METEO = [
    ('<title>Météo & neige · Megève, Combloux, Demi-Quartier, Praz-sur-Arly · Megève par cœur</title>',
     '<title>Snow & weather · Megève, Combloux, Demi-Quartier, Praz-sur-Arly · Megève par cœur</title>'),
    ('content="Météo, hauteur de neige et prévisions de chutes de neige à Megève, Combloux, Demi-Quartier et Praz-sur-Arly, au village et en altitude."',
     'content="Weather, snow depth and snowfall forecast for Megève, Combloux, Demi-Quartier and Praz-sur-Arly, in the village and up the mountain."'),
    ('<h1>Météo &amp; <em>neige</em></h1>', '<h1>Snow &amp; <em>weather</em></h1>'),
    ("<p>Le temps qu'il fait, la neige au sol et les chutes de neige prévues sur 7 jours, au village ou en altitude.</p>",
     '<p>The weather now, the snow on the ground and the snowfall expected over the next 7 days, in the village or up the mountain.</p>'),
    ('aria-label="Altitude"', 'aria-label="Elevation"'),
    ('>🏡 Au village</button>', '>🏡 In the village</button>'),
    ('>🏔️ En altitude (~1 850 m)</button>', '>🏔️ Up the mountain (~1,850 m)</button>'),
    ('<span class="upd" id="upd">Chargement…</span>', '<span class="upd" id="upd">Loading…</span>'),
    ('<p class="skel">Chargement de la météo…</p>', '<p class="skel">Loading the weather…</p>'),
    ('<span>📏 <b>Au sol</b> : hauteur de neige estimée par les modèles</span><span>🆕 <b>Tombée 24 h</b> : neige fraîche des dernières 24 h</span><span>📅 <b>À venir 7 j</b> : cumul des chutes prévues</span>',
     '<span>📏 <b>On the ground</b>: snow depth estimated by the models</span><span>🆕 <b>Last 24 h</b>: fresh snow over the past 24 hours</span><span>📅 <b>Next 7 days</b>: total expected snowfall</span>'),
    ('Estimations des modèles météo (Météo-France, ECMWF…) fournies par', 'Weather model estimates (Météo-France, ECMWF…) provided by'),
    (", mises à jour plusieurs fois par jour. Elles peuvent différer de l'enneigement mesuré sur les pistes : pour l'ouverture des pistes et les bulletins officiels, consultez",
     ', updated several times a day. They may differ from the snow measured on the slopes: for slope openings and official reports, see'),
    ('>Météo-France montagne</a> et les offices de tourisme de', '>Météo-France mountain</a> and the tourist offices of'),
    ('>Combloux</a> et <a href="https://www.prazsurarly.com/"', '>Combloux</a> and <a href="https://www.prazsurarly.com/"'),
    (">L'agenda de Megève &amp; alentours</a>", ">What's on in Megève &amp; around</a>"),
    ('· Données météo :', '· Weather data:'),
    ('"Ensoleillé"', '"Sunny"'), ('"Plutôt ensoleillé"', '"Mostly sunny"'), ('"Éclaircies"', '"Sunny spells"'),
    ('"Couvert"', '"Overcast"'), ('"Brouillard"', '"Fog"'), ('"Brouillard givrant"', '"Freezing fog"'),
    ('"Bruine"', '"Drizzle"'), ('"Bruine forte"', '"Heavy drizzle"'), ('"Bruine verglaçante"', '"Freezing drizzle"'),
    ('"Pluie faible"', '"Light rain"'), ('"Pluie"', '"Rain"'), ('"Forte pluie"', '"Heavy rain"'),
    ('"Pluie verglaçante"', '"Freezing rain"'), ('"Neige faible"', '"Light snow"'), ('"Neige"', '"Snow"'),
    ('"Fortes chutes de neige"', '"Heavy snow"'), ('"Grains de neige"', '"Snow grains"'), ('"Averses"', '"Showers"'),
    ('"Fortes averses"', '"Heavy showers"'), ('"Averses de neige"', '"Snow showers"'),
    ('"Fortes averses de neige"', '"Heavy snow showers"'), ('"Orage"', '"Thunderstorm"'), ('"Orage et grêle"', '"Thunderstorm with hail"'),
    ('const JN=["dim.","lun.","mar.","mer.","jeu.","ven.","sam."], JL=["dimanche","lundi","mardi","mercredi","jeudi","vendredi","samedi"];',
     'const JN=["Sun","Mon","Tue","Wed","Thu","Fri","Sat"], JL=["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"];'),
    ('k===0?"auj.":', 'k===0?"today":'),
    ('aria-label="Météo ${v.n}"', 'aria-label="Weather ${v.n}"'),
    ('toLocaleString("fr-FR")', 'toLocaleString("en-GB")'),
    ('Ressenti ${', 'Feels like ${'), ('° · Vent ${', '° · Wind ${'), ('` (rafales ${', '` (gusts ${'),
    ('Isotherme 0 °C : ${', 'Freezing level: ${'),
    ('<div class="k">📏 Au sol</div>', '<div class="k">📏 On the ground</div>'),
    ('<div class="k">🆕 Tombée 24 h</div>', '<div class="k">🆕 Last 24 h</div>'),
    ('<div class="k">📅 À venir 7 j</div>', '<div class="k">📅 Next 7 days</div>'),
    (' cm de neige`', ' cm of snow`'),
    ('"Il neige aujourd\'hui !"', '"It\'s snowing today!"'), ('"De la neige attendue demain"', '"Snow expected tomorrow"'),
    ('`Prochaine neige : ${', '`Next snow: ${'),
    ("`Jusqu'à ${cmF(best.sn)} cm ce jour-là (${best.v}) · jusqu'à ${r0(tot)} cm cumulés sur 7 jours ${zone===\"v\"?\"au village\":\"en altitude\"}.`",
     '`Up to ${cmF(best.sn)} cm that day (${best.v}) · up to ${r0(tot)} cm in total over 7 days ${zone==="v"?"in the village":"up the mountain"}.`'),
    ('"Pas de chute de neige prévue cette semaine"', '"No snowfall expected this week"'),
    ('"Regardez aussi en altitude : la neige y tombe souvent plus tôt."', '"Check up the mountain too: snow often falls there first."'),
    ('"Profitez du soleil sur les pistes !"', '"Enjoy the sunshine on the slopes!"'),
    ('"Mis à jour à "+t.toLocaleTimeString("fr-FR"', '"Updated at "+t.toLocaleTimeString("en-GB"'),
    ('$("upd").textContent="Chargement…"', '$("upd").textContent="Loading…"'),
    ("La météo n\\'a pas pu se charger. Réessayez dans un instant.", 'The weather could not load. Please try again in a moment.'),
]

# ---------------------------------------------------------------- webcams
WEBCAMS = [
    ("<title>Webcams · Megève, Rochebrune, Mont d'Arbois, Côte 2000, Combloux, Jaillet · Megève par cœur</title>",
     "<title>Live webcams · Megève, Rochebrune, Mont d'Arbois, Côte 2000, Combloux, Jaillet · Megève par cœur</title>"),
    ("content=\"Toutes les webcams de Megève et Combloux sur une seule page : village de Megève, Rochebrune, Mont d'Arbois, Côte 2000, sommet de Combloux et du Jaillet.\"",
     "content=\"All the Megève and Combloux webcams on one page: Megève village, Rochebrune, Mont d'Arbois, Côte 2000, the Combloux summit and Le Jaillet.\""),
    ('<h1>Les webcams, <em>en direct</em></h1>', '<h1>The webcams, <em>live</em></h1>'),
    ("<p>Du village de Megève au sommet de Combloux, regardez les six webcams panoramiques en même temps : la neige, le ciel, l'ambiance sur les pistes.</p>",
     '<p>From Megève village to the top of Combloux, watch all six panoramic webcams at once: the snow, the sky, the mood on the slopes.</p>'),
    ('<i></i>6 webcams en direct</span>', '<i></i>6 live webcams</span>'),
    ('aria-label="Taille des webcams"', 'aria-label="Webcam size"'),
    ('>◻◻ Grandes</button>', '>◻◻ Large</button>'), ('>◻◻◻ Mosaïque</button>', '>◻◻◻ Grid</button>'),
    ('>🌨️ Météo &amp; neige des 4 villages →</a>', '>🌨️ Snow &amp; weather in the 4 villages →</a>'),
    ('<h3>Il va neiger ?</h3><p>Hauteur de neige et chutes prévues sur 7 jours, au village et en altitude.</p>',
     '<h3>Is snow on the way?</h3><p>Snow depth and snowfall forecast for the next 7 days, in the village and up the mountain.</p>'),
    ('>Voir la météo &amp; neige →</a>', '>See the snow forecast →</a>'),
    ('<p class="note">Webcams panoramiques', '<p class="note">Panoramic webcams by'),
    (", affichées depuis leurs pages publiques. Les images se mettent à jour automatiquement ; dans chaque webcam, vous pouvez vous déplacer dans le panorama et remonter le temps. Si une webcam ne s'affiche pas, touchez « Ouvrir ↗ ».",
     ', shown from their public pages. Images update automatically; in each webcam you can pan around the view and go back in time. If a webcam does not show, tap “Open ↗”.'),
    ('"Megève village"', '"Megève village"'),
    ('"La place, l\'église et les chalets"', '"The square, the church and the chalets"'),
    ('"Domaine de Rochebrune"', '"Rochebrune ski area"'), ('"Face au Mont-Blanc"', '"Facing Mont Blanc"'),
    ('"Le haut du domaine"', '"The top of the ski area"'), ('t:"Sommet de Combloux"', 't:"Combloux summit"'),
    ('t:"Sommet du Jaillet"', 't:"Le Jaillet summit"'), ('"Entre Megève et Combloux"', '"Between Megève and Combloux"'),
    ('Chargement de la webcam…', 'Loading the webcam…'), ('⛶ Plein écran</button>', '⛶ Full screen</button>'),
    ('>Ouvrir ↗</a><span class="tag">', '>Open ↗</a><span class="tag">'),
]

# ---------------------------------------------------------------- balades
BALADES = [
    ('<title>Balades & raquettes à Megève, Combloux, Praz-sur-Arly · Megève par cœur</title>',
     '<title>Walks & snowshoe trails in Megève, Combloux, Praz-sur-Arly · Megève par cœur</title>'),
    ('content="Balades & raquettes à Megève, Combloux, Praz-sur-Arly · Megève par cœur"',
     'content="Walks & snowshoe trails in Megève, Combloux, Praz-sur-Arly · Megève par cœur"'),
    ('content="Balades à pied et itinéraires raquettes balisés autour de Megève, Combloux, Demi-Quartier et Praz-sur-Arly : durée, dénivelé, distance et point de départ."',
     'content="Signposted walks and snowshoe trails around Megève, Combloux, Demi-Quartier and Praz-sur-Arly: time, elevation gain, distance and starting point."'),
    ('<h1>Balades &amp; <em>raquettes</em></h1>', '<h1>Walks &amp; <em>snowshoes</em></h1>'),
    ('<p>Des itinéraires balisés, faciles à trouver et pensés pour profiter de la montagne sans skis : en famille dans le village ou en raquettes face au Mont-Blanc.</p>',
     '<p>Signposted routes, easy to find and designed to enjoy the mountains without skis: with the family in the village, or on snowshoes facing Mont Blanc.</p>'),
    ('<span class="lab">Niveau</span>', '<span class="lab">Level</span>'),
    ('aria-pressed="true">Tous</button>', 'aria-pressed="true">All</button>'),
    ('9 fontaines, 2 torrents, 4 ponts</h2>', '9 fountains, 2 streams, 4 bridges</h2>'),
    ("Une petite boucle dans le vieux Megève, de fontaine en fontaine : l'église, le vieux pont, la place de la Résistance, la passerelle sur le torrent. Idéale avec des enfants ou en fin de journée, sous les illuminations.",
     'A short loop through old Megève, from fountain to fountain: the church, the old bridge, Place de la Résistance, the footbridge over the stream. Ideal with children or at the end of the day, under the Christmas lights.'),
    ("Une boucle tranquille, d'abord en bord de piste puis plus sauvage à travers la forêt, par Beauregard, le Châble d'en bas et le Vernay.",
     "A gentle loop, first alongside the slopes and then wilder through the forest, via Beauregard, Le Châble d'en bas and Le Vernay."),
    ("La randonnée des P'tits Loups</h2>", 'The P\'tits Loups trail</h2>'),
    ('Le circuit familial par excellence : une boucle verte avec des jeux pour les enfants, le long des pistes de ski de fond (on marche à côté des traces).',
     'The ultimate family route: an easy loop with games for children, along the cross-country ski trails (walk beside the tracks).'),
    ('Un des itinéraires raquettes balisés des Portes du Mont-Blanc, à travers bois et le long des pistes. Court, mais avec un peu de montée.',
     'One of the signposted snowshoe trails of the Portes du Mont-Blanc, through the woods and along the slopes. Short, but with some climbing.'),
    ('Du Jaillet supérieur au col du Jaillet</h2>', 'From upper Jaillet to the Col du Jaillet</h2>'),
    ("Forêt, sous-bois et col : une très belle balade avec vue sur la chaîne du Mont-Blanc, les Aravis et Megève en contrebas. Aller-retour par le même chemin ; table d'orientation et aire de pique-nique. Le Meg'bus gratuit dessert la télécabine.",
     "Forest, woodland and a mountain pass: a lovely walk with views of the Mont Blanc range, the Aravis and Megève below. Out and back on the same path; viewpoint indicator and picnic area. The free Meg'bus stops at the gondola."),
    ('Liaison Combloux – Megève</h2>', 'Combloux – Megève link</h2>'),
    ("Un itinéraire en alpage face au Mont-Blanc, par Cuchet, Maison Neuve, la Fouettaz et Odier, jusqu'à la télécabine du Jaillet à Megève. Aller simple : prévoyez le retour.",
     'A route through alpine pastures facing Mont Blanc, via Cuchet, Maison Neuve, La Fouettaz and Odier, to the Jaillet gondola in Megève. One way only: plan your return.'),
    ("Pour raquettistes confirmés : un itinéraire non damé qui monte jusqu'à 1 853 m. La descente se fait par les pistes damées.",
     'For experienced snowshoers: an ungroomed trail climbing up to 1,853 m. The way down follows the groomed slopes.'),
    ('Le sentier des Evettes</h2>', 'The Evettes trail</h2>'),
    ("Un itinéraire balisé et gratuit à travers forêt et clairières, avec de belles vues sur les Aravis et le Val d'Arly. Accessible à tous, dès 10 ans.",
     "A free signposted trail through forest and clearings, with beautiful views of the Aravis and the Val d'Arly. Open to everyone aged 10 and over."),
    (' · départ : ', ' · start: '),
    ('Centre du village de Megève', 'Megève village centre'),
    ('Parking de la Cry, Combloux', 'La Cry car park, Combloux'),
    ('Pistes de ski de fond, Combloux', 'Cross-country ski trails, Combloux'),
    ('Domaine des Portes du Mont-Blanc (Le Jaillet)', 'Portes du Mont-Blanc ski area (Le Jaillet)'),
    ('Gare supérieure de la télécabine du Jaillet', 'Top station of the Jaillet gondola'),
    ('Domaine des Portes du Mont-Blanc</p>', 'Portes du Mont-Blanc ski area</p>'),
    ('<span>Durée</span>', '<span>Time</span>'), ('<span>Dénivelé +</span>', '<span>Climb</span>'),
    ('<span>Distance</span>', '<span>Distance</span>'),
    ('>Fiche officielle &amp; tracé ↗</a>', '>Official route &amp; map ↗</a>'), ('>📍 Point de départ</a>', '>📍 Starting point</a>'),
    ('<h3>⛑️ Avant de partir</h3>', '<h3>⛑️ Before you go</h3>'),
    ("<li>Les itinéraires en domaine skiable ne sont ouverts qu'aux heures d'ouverture des pistes, et jamais la nuit.</li>",
     '<li>Trails inside the ski area are only open during lift hours, and never at night.</li>'),
    ('<li>Restez sur les tracés balisés (balisage violet pour la raquette), ne marchez pas dans les traces de ski de fond.</li>',
     '<li>Stay on the marked routes (purple markers for snowshoes), and do not walk in the cross-country ski tracks.</li>'),
    ("<li>Vérifiez la <a href=\"/meteo/\">météo &amp; la neige</a> et les <a href=\"/webcams/\">webcams</a>, et renseignez-vous à l'office de tourisme sur l'ouverture des itinéraires.</li>",
     '<li>Check the <a href="/en/meteo/">snow &amp; weather</a> and the <a href="/en/webcams/">webcams</a>, and ask the tourist office which trails are open.</li>'),
    ('<li>Location de raquettes dans les magasins de sport des villages ; sorties accompagnées avec les bureaux des guides.</li>',
     '<li>Snowshoe hire at the village sports shops; guided outings with the mountain guide offices.</li>'),
    ("Durées et dénivelés indiqués par les offices de tourisme, à titre indicatif. Sources : Megève Tourisme, Office de tourisme de Combloux, Office de tourisme de Praz-sur-Arly, Haute-Savoie Tourisme.",
     'Times and elevation gains as given by the tourist offices, for guidance only. Sources: Megève Tourisme, Combloux tourist office, Praz-sur-Arly tourist office, Haute-Savoie Tourisme.'),
    ('1,0 km', '1.0 km'), ('3,5 km', '3.5 km'), ('2,5 km', '2.5 km'), ('6,0 km', '6.0 km'), ('4,0 km', '4.0 km'), ('4,8 km', '4.8 km'),
    ('45 min', '45 min'),
]
# niveaux / types : remplacés partout (classes CSS, filtres et libellés restent cohérents)
BALADES_ALL = [('Modéré', 'Moderate'), ('Facile', 'Easy'), ('Sportif', 'Challenging'), ('À pied', 'On foot'),
               ('"Raquettes"', '"Snowshoes"'), ('>Raquettes ·', '>Snowshoes ·'), ('>On foot ·', '>On foot ·')]

# ---------------------------------------------------------------- carte
CARTE = [
    ('<title>Carte des coups de cœur · Megève, Combloux, Demi-Quartier, Praz · Megève par cœur</title>',
     '<title>Map of our favourite spots · Megève, Combloux, Demi-Quartier, Praz · Megève par cœur</title>'),
    ('content="Carte des coups de cœur · Megève, Combloux, Demi-Quartier, Praz · Megève par cœur"',
     'content="Map of our favourite spots · Megève, Combloux, Demi-Quartier, Praz · Megève par cœur"'),
    ('content="Notre carte illustrée des plus beaux coins de Megève et alentours : panoramas, balades, patrimoine et sorties en famille."',
     'content="Our illustrated map of the most beautiful spots in and around Megève: viewpoints, walks, heritage and family outings."'),
    ('<div class="kicker">📍 Nos coups de cœur</div>', '<div class="kicker">📍 Our favourites</div>'),
    ('<h1>La carte des <em>beaux coins</em></h1>', '<h1>Our map of <em>beautiful spots</em></h1>'),
    ('<p>Panoramas, balades, patrimoine et sorties en famille : nos endroits préférés autour de Megève, Combloux, Demi-Quartier et Praz-sur-Arly. Touchez une épingle.</p>',
     '<p>Viewpoints, walks, heritage and family outings: our favourite places around Megève, Combloux, Demi-Quartier and Praz-sur-Arly. Tap a pin.</p>'),
    ('aria-label="Carte illustrée de Megève, Combloux, Demi-Quartier et Praz-sur-Arly"',
     'aria-label="Illustrated map of Megève, Combloux, Demi-Quartier and Praz-sur-Arly"'),
    ('aria-pressed="true">Tout</button>', 'aria-pressed="true">All</button>'),
    ('>🏔️ Panoramas</button>', '>🏔️ Viewpoints</button>'), ('>🥾 Balades</button>', '>🥾 Walks</button>'),
    ('>⛪ Patrimoine</button>', '>⛪ Heritage</button>'), ('>🧒 Famille</button>', '>🧒 Family</button>'),
    ('Carte illustrée : les positions sont indicatives. Le bouton « Itinéraire » ouvre le lieu dans Google Maps.',
     'Illustrated map: positions are approximate. The “Directions” button opens the place in Google Maps.'),
    ('📍 Itinéraire</a>', '📍 Directions</a>'),
    ('${ICON[s.c]} ${s.c}</span>', '${ICON[s.c]} ${CAT[s.c]}</span>'),
    ('const ICON={', 'const CAT={Patrimoine:"Heritage",Balade:"Walk",Panorama:"Viewpoint",Famille:"Family"};\nconst ICON={'),
    ('"Place du village & église"', '"Village square & church"'),
    ("\"Le cœur de Megève : les rues piétonnes, l'église, le vieux pont et ses fontaines. Magique à la tombée de la nuit sous les illuminations.\"",
     '"The heart of Megève: the pedestrian streets, the church, the old bridge and its fountains. Magical at nightfall under the Christmas lights."'),
    ('"La balade des 9 fontaines"', '"The 9 fountains walk"'), ('"Webcam du village"', '"Village webcam"'),
    ('"Une promenade au-dessus du village, entre alpages et vieilles fermes, avec vue sur toute la vallée. Notre coup de cœur pour une fin d\'après-midi."',
     '"A walk above the village, between pastures and old farms, with a view over the whole valley. Our favourite for a late afternoon."'),
    ('"Le balcon de Megève face au massif du Mont-Blanc. Le plus beau lever de soleil du domaine."',
     '"Megève\'s balcony facing the Mont Blanc massif. The finest sunrise in the ski area."'),
    ('"Webcam du Mont d\'Arbois"', '"Mont d\'Arbois webcam"'),
    ('"Le domaine historique de Megève, juste au-dessus du village : vue plongeante sur les toits et le val d\'Arly."',
     '"Megève\'s historic ski area, just above the village: a bird\'s-eye view over the rooftops and the Val d\'Arly."'),
    ('"Webcam de Rochebrune"', '"Rochebrune webcam"'),
    ('"Le secteur le plus sauvage du domaine, idéal pour une journée au calme loin de l\'agitation du village."',
     '"The wildest part of the ski area, perfect for a quiet day away from the bustle of the village."'),
    ('"Webcam de la Côte 2000"', '"Côte 2000 webcam"'), ('"Les crêtes du Mont Joly"', '"The Mont Joly ridges"'),
    ('"Le grand classique des panoramas : le massif du Mont-Blanc en face, les Aravis dans le dos. Une randonnée d\'été pour bons marcheurs."',
     '"The great classic for views: the Mont Blanc massif in front of you, the Aravis behind. A summer hike for good walkers."'),
    ('"Le Jaillet & son col"', '"Le Jaillet & its pass"'),
    ('"Forêts, alpages et table d\'orientation : la balade en raquettes jusqu\'au col du Jaillet offre une vue sur le Mont-Blanc, les Aravis et Megève."',
     '"Forests, pastures and a viewpoint indicator: the snowshoe walk to the Col du Jaillet offers views of Mont Blanc, the Aravis and Megève."'),
    ('"Itinéraire raquettes"', '"Snowshoe trail"'), ('"Webcam du Jaillet"', '"Le Jaillet webcam"'),
    ('"Combloux, face au Mont-Blanc"', '"Combloux, facing Mont Blanc"'),
    ('"Le village et son église baroque au clocher à bulbe, avec l\'une des plus belles vues sur le Mont-Blanc de la région."',
     '"The village and its Baroque church with an onion-domed bell tower, with one of the finest views of Mont Blanc in the area."'),
    ('"Webcam du sommet de Combloux"', '"Combloux summit webcam"'), ('"Les raquettes à Combloux"', '"Snowshoeing in Combloux"'),
    ('"La Cry et les alpages"', '"La Cry and the pastures"'),
    ('"Le point de départ des balades raquettes faciles de Combloux, en lisière de forêt, et de la liaison vers Megève à travers les alpages."',
     '"The starting point for Combloux\'s easy snowshoe walks, at the edge of the forest, and for the link to Megève across the pastures."'),
    ('"Itinéraires au départ de la Cry"', '"Trails starting from La Cry"'),
    ('"Les hameaux de Demi-Quartier : l\'atelier-galerie d\'une artiste face au Mont-Blanc à Vauvray, et les balades en calèche des écuries du Feug."',
     '"The hamlets of Demi-Quartier: an artist\'s studio-gallery facing Mont Blanc in Vauvray, and horse-drawn carriage rides from the Feug stables."'),
    ('"Praz-sur-Arly & ses montgolfières"', '"Praz-sur-Arly & its hot-air balloons"'),
    ('"Un village-station familial du val d\'Arly. Chaque hiver, les Montgolfiades remplissent le ciel de ballons colorés au lever du jour."',
     '"A family-friendly village resort in the Val d\'Arly. Every winter, the Montgolfiades balloon festival fills the sky with colourful balloons at sunrise."'),
    ('"Les raquettes à Praz"', '"Snowshoeing in Praz"'),
    ('"/balades/"', '"/en/balades/"'), ('"/webcams/"', '"/en/webcams/"'), ('"/#agenda"', '"/en/#agenda"'),
]
CARTE_ALL = [('"Voir dans l\'agenda"', '"See what\'s on"')]

# ---------------------------------------------------------------- boutique
BOUTIQUE = [
    ('<title>Boutique solidaire · Megève par cœur</title>', '<title>Charity shop · Megève par cœur</title>'),
    ('content="La boutique solidaire Megève par cœur × Coupe des Banques Genevoises : tous les bénéfices reversés à une association."',
     'content="The Megève par cœur × Coupe des Banques Genevoises charity shop: all profits go to a charity."'),
    ('<div class="kicker">Boutique solidaire</div>', '<div class="kicker">Charity shop</div>'),
    ('<h1>Portez Megève <span class="h">sur le cœur</span></h1>', '<h1>Wear Megève <span class="h">close to your heart</span></h1>'),
    ("<p>Casquettes, tours de cou, tasses et protections solaires aux couleurs de Megève par cœur, de la Coupe des Banques Genevoises et de l'équipe The Rogue Skiers. Tous les bénéfices sont reversés à une association, annoncée prochainement.</p>",
     '<p>Caps, neck warmers, mugs and sun protection in the colours of Megève par cœur, the Coupe des Banques Genevoises and the Rogue Skiers team. All profits go to a charity, to be announced soon.</p>'),
    ('>Aller à la boutique →</a>', '>Go to the shop →</a>'), ('>Découvrir le partenariat</a>', '>About the partnership</a>'),
    ('aria-label="Les partenaires"', 'aria-label="The partners"'),
    ('alt="Logo Megève par cœur"', 'alt="Megève par cœur logo"'),
    ('alt="Logo Coupe de Ski des Banques Genevoises"', 'alt="Coupe de Ski des Banques Genevoises logo"'),
    ('alt="Blason The Rogue Skiers"', 'alt="The Rogue Skiers crest"'),
    ('<div class="kicker">Le partenariat</div>', '<div class="kicker">The partnership</div>'),
    ('<h2>Une boutique, deux passions pour la montagne</h2>', '<h2>One shop, two passions for the mountains</h2>'),
    ("<p class=\"lead\">Megève par cœur et la Coupe des Banques Genevoises se sont associés pour créer une boutique solidaire commune. La boutique est hébergée sur le site de la Coupe : c'est là que se trouvent les produits et que se feront les achats.</p>",
     "<p class=\"lead\">Megève par cœur and the Coupe des Banques Genevoises have teamed up to create a joint charity shop. The shop is hosted on the Coupe's website: that's where you'll find the products and make your purchases.</p>"),
    ('<span class="who">Le compte des amoureux de Megève</span>', '<span class="who">The account for Megève lovers</span>'),
    ('<p>Les balades, les panoramas et les rendez-vous de Megève et de ses alentours, partagés au fil des saisons sur Instagram et sur ce site.</p>',
     '<p>Walks, views and events in and around Megève, shared season after season on Instagram and on this site.</p>'),
    ('<span class="who">La course caritative des banques genevoises</span>', "<span class=\"who\">Geneva banks' charity ski race</span>"),
    ("<p>Une course de ski solidaire : chaque équipe court et lève des fonds pour une association différente. L'équipe qui récolte le plus remporte la Coupe.</p>",
     '<p>A charity ski race: each team races and raises money for a different charity. The team that raises the most wins the Cup.</p>'),
    ("<span class=\"kicker\" style=\"display:block\">L'équipe soutenue</span>", '<span class="kicker" style="display:block">The team we support</span>'),
    ("<p>L'équipe des candidats libres de la Coupe des Banques Genevoises. C'est à sa collecte que vont les bénéfices de la boutique, au profit d'une association qui sera annoncée prochainement.</p>",
     "<p>The independent entrants' team of the Coupe des Banques Genevoises. The shop's profits go to its fundraising, for a charity to be announced soon.</p>"),
    ("<b>Des produits signés</b><p>Chaque article porte les logos de Megève par cœur, de la Coupe et de The Rogue Skiers, l'équipe des candidats libres.</p>",
     "<b>Signature products</b><p>Every item carries the logos of Megève par cœur, the Coupe and the Rogue Skiers, the independent entrants' team.</p>"),
    ('<b>Une seule boutique</b><p>Les achats se font sur la boutique de la Coupe des Banques Genevoises. Ce site vous y emmène en un clic.</p>',
     '<b>One single shop</b><p>Purchases are made on the Coupe des Banques Genevoises shop. This site takes you there in one click.</p>'),
    ("<b>100 % solidaire</b><p>Les bénéfices sont versés à la collecte de The Rogue Skiers, au profit d'une association bientôt dévoilée.</p>",
     '<b>100% for charity</b><p>Profits go to the Rogue Skiers fundraising, for a charity to be revealed soon.</p>'),
    ('<div class="kicker">La cause soutenue</div>', '<div class="kicker">The cause</div>'),
    ('<h2>Une association bientôt dévoilée</h2>', '<h2>A charity to be revealed soon</h2>'),
    ("<p>Le choix de l'association qui recevra les bénéfices de la boutique est en cours. Elle sera annoncée ici et sur Instagram très bientôt.</p>",
     "<p>The charity that will receive the shop's profits is being chosen. It will be announced here and on Instagram very soon.</p>"),
    ("<div class=\"big\">100 %<small>des bénéfices reversés à l'association</small></div>", '<div class="big">100%<small>of profits go to the charity</small></div>'),
    ('<div class="kicker">Les produits</div>', '<div class="kicker">The products</div>'),
    ('<h2>Au programme <span class="soon">Bientôt disponibles</span></h2>', '<h2>Coming up <span class="soon">Available soon</span></h2>'),
    ('</svg>Casquette<small>Brodée aux trois logos</small>', '</svg>Cap<small>Embroidered with all three logos</small>'),
    ('</svg>Tour de cou<small>Pour les matins frais</small>', '</svg>Neck warmer<small>For chilly mornings</small>'),
    ("</svg>Tasse<small>Pour le vin chaud d'après-ski</small>", '</svg>Mug<small>For après-ski mulled wine</small>'),
    ('</svg>Crème solaire &amp; stick lèvres<small>La protection en altitude</small>', '</svg>Sunscreen &amp; lip balm<small>Protection at altitude</small>'),
    ('<h2>Envie de soutenir la cause ?</h2>', '<h2>Want to support the cause?</h2>'),
    ('<p>Rendez-vous sur la boutique solidaire de la Coupe des Banques Genevoises pour découvrir les produits dès leur sortie.</p>',
     '<p>Head to the Coupe des Banques Genevoises charity shop to discover the products as soon as they are released.</p>'),
    ('>Aller à la boutique solidaire →</a>', '>Go to the charity shop →</a>'),
    ('<span>© Megève par cœur · en partenariat avec la Coupe des Banques Genevoises</span>',
     '<span>© Megève par cœur · in partnership with the Coupe des Banques Genevoises</span>'),
    ('>Instagram : @megeveparcoeur</a>', '>Instagram: @megeveparcoeur</a>'),
]

PAGES = [
    ("", HOME, [], home_special),
    ("meteo/", METEO, [], None),
    ("webcams/", WEBCAMS, [], None),
    ("balades/", BALADES, BALADES_ALL, None),
    ("carte/", CARTE, CARTE_ALL, None),
    ("boutique/", BOUTIQUE, [], None),
]


def build():
    for path, pairs, glob, special in PAGES:
        src = os.path.join(ROOT, path, "index.html")
        fr = open(src, encoding="utf-8").read()
        # --- page FR : nav + hreflang (idempotent)
        fr2 = set_nav(fr, NAV_FR, "/", path, (f"/en/{path}", "EN", "en"))
        fr2 = head_links(fr2, path, "fr")
        if fr2 != fr:
            open(src, "w", encoding="utf-8").write(fr2)
        # --- page EN
        en = fr2.replace('<html lang="fr">', '<html lang="en">', 1)
        en = head_links(en, path, "en")
        en = apply(en, pairs, path or "accueil")
        for a, b in glob:
            en = en.replace(a, b)
        if special:
            en = special(en)
        en = rewrite_links(en, path)
        en = set_nav(en, NAV_EN, "/en/", path, (f"/{path}", "FR", "fr"))
        en = apply(en, COMMON, "commun", strict=False)
        dst = os.path.join(ROOT, "en", path, "index.html")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, "w", encoding="utf-8").write(en)
        print("ok", "/en/" + path)


if __name__ == "__main__":
    build()
