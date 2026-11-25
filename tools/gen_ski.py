#!/usr/bin/env python3
"""Page « Skier à Megève & Combloux » (FR /skier/, EN /en/skiing/).

Usage : python3 tools/gen_ski.py   (depuis la racine du dépôt). Écrit directement les deux langues,
build_en.py n'est pas nécessaire pour cette page.
Tarifs : grilles officielles hiver 2026-2027 (Remontées mécaniques de Megève, màj 14/04/26 ;
SEM Les Portes du Mont-Blanc). À mettre à jour chaque automne (SAISON, PRIX_*, DATES).
"""
import html as H
from gen_pages import page, write, faq_html, faq_ld

SAISON = "2026-2027"

# ---------------------------------------------------------------- tarifs (adulte 15-64, enfant 5-14, senior 65-79)
PRIX_EVA = [  # durée FR, durée EN, haute saison (19/12 → 19/03), début & fin de saison -20 %
    ("4 heures", "4 hours", (58.5, 50, 52.5), (47, 40, 42)),
    ("1 jour", "1 day", (65, 55.5, 58.5), (52, 44.5, 47)),
    ("2 jours", "2 days", (122.5, 104, 110.5), (98, 83, 88.5)),
    ("3 jours", "3 days", (180, 153, 162), (144, 122.5, 129.5)),
    ("6 jours", "6 days", (324.5, 276, 292), (259.5, 221, 233.5)),
    ("6 jours web (J-10)", "6 days online (10 days ahead)", (289.5, 246, 260.5), (231.5, 197, 208.5)),
    ("7 jours", "7 days", (369, 313.5, 332), (295, 251, 265.5)),
    ("Saison", "Season", (1189, 1010.5, 1070), None),
]
PRIX_PMB = [
    ("4 heures", "4 hours", (49, 42, 44)),
    ("1 jour", "1 day", (52.5, 45, 47.5)),
    ("6 jours <small>(+ 1 journée Évasion offerte)</small>", "6 days <small>(+ 1 free Évasion day)</small>", (262.5, 225, 237.5)),
]


def eur(x, lang):
    s = f"{x:,.2f}".replace(",", " ")
    if s.endswith(".00"): s = s[:-3]
    return (s.replace(".", ",") + " €") if lang == "fr" else ("€" + s)


def table(rows, head, lang, cls=""):
    th = "".join(f"<th>{h}</th>" for h in head)
    out = []
    for r in rows:
        label, vals = r[0], r[1:]
        tds = "".join(f"<td>{eur(v, lang)}</td>" if v is not None else "<td>–</td>" for v in vals)
        out.append(f"<tr><th scope=row>{label}</th>{tds}</tr>")
    return f'<div class="tw"><table class="px{cls}"><thead><tr><th></th>{th}</tr></thead><tbody>{"".join(out)}</tbody></table></div>'


T = {
 "fr": dict(
  title=f"Skier à Megève & Combloux {SAISON} : domaines, forfaits, prix, parkings, plan des pistes · Megève par cœur",
  desc=f"Tout pour skier à Megève et Combloux en {SAISON} : domaines Évasion Mont-Blanc et Portes du Mont-Blanc, prix des forfaits, où se garer au pied des pistes, plans des pistes, débutants, ski de fond et bons plans.",
  h1="Skier à Megève <em>&amp; Combloux</em>",
  intro=f"Les domaines, les forfaits et leurs prix, où se garer, les plans des pistes et nos bons plans : l'essentiel pour l'hiver {SAISON}, sur une seule page.",
  kicker="⛷️ Hiver " + SAISON,
  stats=[("400 km", "Évasion Mont-Blanc", "227 pistes · Megève, Saint-Gervais, Combloux, La Giettaz, Les Contamines"),
         ("100 km", "Portes du Mont-Blanc", "69 pistes · Combloux, Megève-Jaillet, La Giettaz, Cordon"),
         ("19 déc.", "Ouverture générale", "Pré-ouverture à Megève les 5-6 déc., puis dès le 12 déc."),
         ("4 avril", "Fermeture", "Rochebrune &amp; Mont d'Arbois · Portes du Mont-Blanc : 21 mars")],
  dom_h="Deux forfaits, deux versants",
  dom_p="Il existe <b>deux forfaits</b> : l'<b>Évasion Mont-Blanc</b>, qui donne accès à tout, et le <b>Portes du Mont-Blanc</b>, moins cher, limité à Combloux, au Jaillet et à La Giettaz.<br><br>Côté pistes, Megève a <b>deux versants qui ne sont pas reliés skis aux pieds</b> :<ul><li><b>Rochebrune, Côte 2000, Mont d'Arbois, la Princesse, Saint-Gervais et Saint-Nicolas-de-Véroce</b> sont reliés entre eux (forfait Évasion).</li><li><b>Le Jaillet, Combloux et La Giettaz</b> sont sur l'autre versant, reliés entre eux mais pas au Mont d'Arbois ni à Rochebrune (forfait Portes du Mont-Blanc ou Évasion).</li></ul>Pour passer d'un versant à l'autre, on traverse Megève en voiture ou en Meg'bus gratuit. Les Contamines, aussi incluses dans l'Évasion, sont à part, en voiture.",
  secteurs=[
   ("🏔️ Rochebrune &amp; Côte 2000", "Évasion", "Le domaine « historique », juste au-dessus du village : téléphérique de Rochebrune depuis le centre, pistes en forêt et, à Côte 2000, le point culminant du secteur. Le téléphérique de <b>Rocharbois</b> le relie au Mont d'Arbois."),
   ("🌲 Mont d'Arbois · Princesse → Saint-Gervais", "Évasion", "Le plus vaste : télécabines du Mont d'Arbois et de la Princesse (Demi-Quartier), puis liaison vers Saint-Gervais et Saint-Nicolas-de-Véroce, jusqu'au Mont Joly (2 350 m) face au Mont-Blanc."),
   ("☀️ Le Jaillet → Combloux &amp; La Giettaz", "Portes du Mont-Blanc + Évasion", "Versant ensoleillé et plus calme, idéal en famille. Depuis la télécabine du Jaillet, on rejoint Combloux, la Tête du Torraz et La Giettaz (côté Aravis). Les premières descentes du matin, face au Mont-Blanc, y sont souvent désertes."),
   ("🏡 Combloux", "Portes du Mont-Blanc + Évasion", "« La perle du Mont-Blanc » : un domaine familial entre sapins et alpages, avec ses parkings gratuits au pied des pistes (Brons, la Cry, Cuchet), un espace débutants et un domaine handiski."),
   ("⛰️ Les Contamines-Hauteluce", "Évasion", "Inclus dans l'Évasion mais à une quarantaine de minutes de route : un domaine plus haut, utile quand la neige manque en bas."),
  ],
  px_h=f"Prix des forfaits {SAISON}",
  px_p="Tarifs publics officiels, en euros. Adulte 15-64 ans, enfant 5-14 ans, senior 65-79 ans.",
  eva_h="Évasion Mont-Blanc (400 km)",
  eva_head=("Adulte", "Enfant", "Senior", "Adulte -20 %*", "Enfant -20 %*", "Senior -20 %*"),
  eva_note="* « Premières neiges » du 12 au 18 décembre 2026 et « printemps » du 20 mars au 4 avril 2027 : -20 %. Haute saison du 19 décembre au 19 mars.",
  pmb_h="Portes du Mont-Blanc (100 km)",
  pmb_head=("Adulte", "Enfant", "Senior"),
  pmb_note="Dès 6 jours aux Portes du Mont-Blanc, une journée Évasion Mont-Blanc est incluse.",
  deals_h="💡 Bons plans &amp; réductions",
  deals=[
   "<b>Moins de 5 ans</b> : forfait gratuit (seul le support mains-libres à 2 € est payant). <b>80 ans et plus</b> : -50 % sur le tarif adulte.",
   "<b>Megève Skideal</b> : en achetant en ligne au moins 3 jours avant, le forfait journée Évasion démarre à <b>32 €</b> (prix dynamique).",
   "<b>6 jours au prix de 5</b> sur l'Évasion si acheté en ligne 10 jours avant (289,50 € adulte au lieu de 324,50 €).",
   "<b>Famille</b> : -10 % pour au moins 4 forfaits achetés ensemble, dont 2 enfants (de 1 à 21 jours).",
   "<b>Saison Évasion en promo jusqu'au 30 novembre 2026</b> : 890 € adulte au lieu de 1 189 €. Même date limite pour le « 7 jours Liberté » (7 jours non consécutifs, hiver et été) à 387 €.",
   "<b>Inclus avec un forfait Évasion acheté à Megève</b> : le Meg'bus gratuit, la Luge Princesse (3 km de luge sur neige) et -50 % à la Balnéoforme du Palais (forfaits de 2 à 21 jours).",
   "<b>Assurance secours</b> en option : environ 3,50 € par jour. Pensez-y : un secours sur piste se paie cher.",
   "<b>Handiski</b> aux Portes du Mont-Blanc : -50 % pour la personne en situation de handicap et son accompagnant (en caisse).",
  ],
  deb_h="🐣 Débutants &amp; piétons",
  deb=[
   "<b>Forfait débutant Rochebrune / Mont d'Arbois</b> : 29 € la journée (tapis et petits téléskis, télécabine du Chamois, téléphérique de Rocharbois). Petit Rochebrune seul : 15 €, en caisse.",
   "<b>Forfait débutant Portes du Mont-Blanc</b> : 18 € la journée (Mowgli, Brons, Garettes, Plan, Covagnet, Grande Rare, tapis des Pattes), en caisse.",
   "<b>Piétons</b> : 23 € la journée Évasion (20,50 € enfant) pour monter aux restaurants d'altitude ; aux Portes du Mont-Blanc, 11,50 € l'aller simple et 19,50 € l'aller-retour (enfant 9,50 / 15 €).",
  ],
  park_h="🅿️ Où se garer au pied des pistes",
  park_head=("Parking", "Remontée", "Prix"),
  parks=[
   ("Megève", [
    ("Rochebrune (souterrain, ~400 pl.)", "Téléphérique de Rochebrune", "Payant · 30 min gratuites"),
    ("Rochebrune (extérieur)", "Téléphérique de Rochebrune", "Zone bleue 4 h (disque)"),
    ("Mont d'Arbois (couvert, ~300 pl., 2,10 m)", "Télécabine du Mont d'Arbois · Rocharbois", "Payant · 30 min gratuites"),
    ("Côte 2000", "Secteur Côte 2000", "Gratuit"),
    ("Princesse (Demi-Quartier, ~900 pl.)", "Télécabine de la Princesse", "Gratuit"),
    ("Le Jaillet", "Télécabine du Jaillet", "Zone bleue 7 h (10 h en partie basse)"),
   ]),
   ("Combloux &amp; La Giettaz", [
    ("Les Brons (540 pl., 3 niveaux)", "Téléski Mowgli · caisse centrale", "Gratuit"),
    ("La Cry (127 pl.)", "Mowgli · télésiège de Beauregard", "Gratuit"),
    ("Cuchet (217 pl.)", "Télésiège de Beauregard · handiski", "Gratuit"),
    ("Le Plan, La Giettaz (P1 et P2)", "Grande Rare · Tête du Torraz", "Gratuit"),
   ]),
  ],
  park_note="Le plus simple à Megève : laisser la voiture et prendre le <b>Meg'bus</b>, gratuit (3 lignes en hiver) et suivi en temps réel dans l'appli Pysae. Les samedis de vacances, les parkings gratuits de Combloux et de la Princesse se remplissent vite : arrivez tôt.",
  plan_h="🗺️ Plans des pistes",
  plans=[("https://forfait.megeve.com/hiver/plan-des-pistes-temps-reel/", "Plan en temps réel Évasion Mont-Blanc"),
         ("https://forfait.megeve.com/hiver/wp-content/uploads/sites/7/2025/11/2025-Plan-Megeve-Evasion-basseDef.pdf", "Plan Évasion (PDF)"),
         ("https://www.lesportesdumontblanc.fr/hiver/plan-des-pistes-megeve-saintgervais-combloux-lagiettaz/", "Plan Portes du Mont-Blanc"),
         ("https://www.lesportesdumontblanc.fr/hiver/infoneige-portes-du-mont-blanc/", "Pistes ouvertes aujourd'hui (Portes du Mont-Blanc)")],
  plan_p="Pour l'état de la neige et des pistes avant de partir, voyez aussi nos pages <a href=\"/meteo/\">Météo &amp; neige</a> et <a href=\"/webcams/\">Webcams</a>.",
  more_h="✨ Et aussi",
  more=[
   ("🎿 Ski de fond", "Une quarantaine de kilomètres à Megève, sur trois sites : la Livraz – Côte 2000 (le principal, vers l'altiport), le golf du Mont d'Arbois et Odier, relié à Combloux. Redevance obligatoire, en vente au chalet d'accueil."),
   ("🥾 Ski de randonnée", "12 itinéraires balisés sur le domaine des Portes du Mont-Blanc, qui séparent randonneurs et skieurs. Le forfait « Combloux Rando » permet de remonter par les télésièges de Beauregard, Pertuis et Jouty."),
   ("🛷 Luge", "La Luge Princesse, 3 km sur neige au départ de la Princesse, offerte avec un forfait Évasion acheté à Megève, et la luge 4S de Combloux."),
   ("👶 Cours de ski", "Écoles de ski (ESF et écoles indépendantes) à Megève comme à Combloux, avec des jardins des neiges pour les tout-petits. Réservez tôt pour Noël et février."),
  ],
  faq=[
   ("Quel forfait prendre pour skier à Megève ?", "Pour Rochebrune, Côte 2000, le Mont d'Arbois et Saint-Gervais, il faut le forfait Évasion Mont-Blanc. Si vous skiez seulement côté Jaillet, Combloux et La Giettaz, le forfait Portes du Mont-Blanc suffit et coûte moins cher (52,50 € la journée adulte contre 65 €)."),
   ("Peut-on aller de Megève à Combloux skis aux pieds ?", "Oui, par le Jaillet : depuis la télécabine du Jaillet à Megève, les pistes rejoignent Combloux et La Giettaz. En revanche, le Jaillet n'est pas relié skis aux pieds à Rochebrune ni au Mont d'Arbois : il faut traverser le village (Meg'bus gratuit)."),
   ("Où se garer gratuitement pour skier ?", "À Megève : parkings de la Princesse (Demi-Quartier) et de Côte 2000. À Combloux : les Brons, la Cry et Cuchet, tous gratuits au pied des pistes. Au Jaillet, le parking est en zone bleue (disque)."),
   ("Quand ouvrent les pistes cet hiver ?", "Megève prévoit une pré-ouverture le week-end des 5-6 décembre 2026, une ouverture partielle dès le 12 décembre et l'ouverture générale le 19 décembre, jusqu'au 4 avril 2027. Les Portes du Mont-Blanc ouvrent du 19 décembre 2026 au 21 mars 2027. Tout dépend de la neige."),
   ("Comment payer son forfait moins cher ?", "Acheter en ligne à l'avance (dès 32 € la journée Évasion à J-3, 6 jours au prix de 5 à J-10), skier en début ou fin de saison (-20 %), profiter de la réduction famille, et garder son support mains-libres pour le recharger."),
  ],
  note=f"Tarifs publics officiels {SAISON} (Remontées mécaniques de Megève et SEM Les Portes du Mont-Blanc), donnés à titre indicatif : vérifiez avant d'acheter. Ouvertures sous réserve d'enneigement.",
  links=[("https://forfait.megeve.com/hiver/", "Forfaits Megève (Évasion)"), ("https://www.lesportesdumontblanc.fr/hiver/", "Les Portes du Mont-Blanc"),
         ("https://www.megeve-tourisme.fr/", "Megève Tourisme"), ("https://www.combloux.com/", "Office de tourisme de Combloux")],
 ),
 "en": dict(
  title=f"Skiing in Megève & Combloux {SAISON}: ski areas, lift passes, prices, parking, piste maps · Megève par cœur",
  desc=f"Everything for skiing in Megève and Combloux in {SAISON}: the Évasion Mont-Blanc and Portes du Mont-Blanc areas, lift pass prices, where to park by the slopes, piste maps, beginners, cross-country skiing and money-saving tips.",
  h1="Skiing in Megève <em>&amp; Combloux</em>",
  intro=f"Ski areas, lift passes and prices, where to park, piste maps and our tips: the essentials for winter {SAISON}, on one page.",
  kicker="⛷️ Winter " + SAISON,
  stats=[("400 km", "Évasion Mont-Blanc", "227 runs · Megève, Saint-Gervais, Combloux, La Giettaz, Les Contamines"),
         ("100 km", "Portes du Mont-Blanc", "69 runs · Combloux, Megève-Jaillet, La Giettaz, Cordon"),
         ("19 Dec", "Full opening", "Early opening in Megève on 5-6 Dec, then from 12 Dec"),
         ("4 April", "Closing", "Rochebrune &amp; Mont d'Arbois · Portes du Mont-Blanc: 21 March")],
  dom_h="Two passes, two sides of the valley",
  dom_p="There are <b>two lift passes</b>: <b>Évasion Mont-Blanc</b>, which covers everything, and the cheaper <b>Portes du Mont-Blanc</b>, limited to Combloux, Le Jaillet and La Giettaz.<br><br>On the slopes, Megève has <b>two sides that are not linked on skis</b>:<ul><li><b>Rochebrune, Côte 2000, Mont d'Arbois, the Princesse, Saint-Gervais and Saint-Nicolas-de-Véroce</b> are linked together (Évasion pass).</li><li><b>Le Jaillet, Combloux and La Giettaz</b> are on the other side, linked together but not to Mont d'Arbois or Rochebrune (Portes du Mont-Blanc or Évasion pass).</li></ul>To switch sides, cross Megève by car or on the free Meg'bus. Les Contamines, also included in Évasion, is separate, by car.",
  secteurs=[
   ("🏔️ Rochebrune &amp; Côte 2000", "Évasion", "The \"historic\" area right above the village: the Rochebrune cable car from the centre, runs through the forest and, at Côte 2000, the highest point of the sector. The <b>Rocharbois</b> cable car links it to Mont d'Arbois."),
   ("🌲 Mont d'Arbois · Princesse → Saint-Gervais", "Évasion", "The largest sector: the Mont d'Arbois and Princesse (Demi-Quartier) gondolas, then the link to Saint-Gervais and Saint-Nicolas-de-Véroce, up to Mont Joly (2,350 m) facing Mont Blanc."),
   ("☀️ Le Jaillet → Combloux &amp; La Giettaz", "Portes du Mont-Blanc + Évasion", "The sunny, quieter side, ideal for families. From the Jaillet gondola you reach Combloux, the Tête du Torraz and La Giettaz (Aravis side). The first morning runs, facing Mont Blanc, are often empty."),
   ("🏡 Combloux", "Portes du Mont-Blanc + Évasion", "\"The pearl of Mont Blanc\": a family area among fir trees and pastures, with free car parks at the foot of the slopes (Brons, la Cry, Cuchet), a beginners' area and an adaptive-ski area."),
   ("⛰️ Les Contamines-Hauteluce", "Évasion", "Included in Évasion but about forty minutes away by road: a higher area, handy when snow is short lower down."),
  ],
  px_h=f"Lift pass prices {SAISON}",
  px_p="Official public prices, in euros. Adult 15-64, child 5-14, senior 65-79.",
  eva_h="Évasion Mont-Blanc (400 km)",
  eva_head=("Adult", "Child", "Senior", "Adult -20%*", "Child -20%*", "Senior -20%*"),
  eva_note="* \"First snow\" 12-18 December 2026 and \"spring\" 20 March - 4 April 2027: 20% off. High season 19 December - 19 March.",
  pmb_h="Portes du Mont-Blanc (100 km)",
  pmb_head=("Adult", "Child", "Senior"),
  pmb_note="From 6 days on Portes du Mont-Blanc, one Évasion Mont-Blanc day is included.",
  deals_h="💡 Tips &amp; discounts",
  deals=[
   "<b>Under 5</b>: free pass (only the €2 hands-free card is charged). <b>80 and over</b>: 50% off the adult price.",
   "<b>Megève Skideal</b>: buy online at least 3 days ahead and the Évasion day pass starts at <b>€32</b> (dynamic pricing).",
   "<b>6 days for the price of 5</b> on Évasion when bought online 10 days ahead (€289.50 adult instead of €324.50).",
   "<b>Family</b>: 10% off for at least 4 passes bought together, including 2 children (1 to 21 days).",
   "<b>Évasion season pass on offer until 30 November 2026</b>: €890 adult instead of €1,189. Same deadline for the \"7 Liberty days\" (7 non-consecutive days, winter and summer) at €387.",
   "<b>Included with an Évasion pass bought in Megève</b>: the free Meg'bus, the Luge Princesse (3 km snow sledging run) and 50% off the Palais Balnéoforme spa (2 to 21-day passes).",
   "<b>Rescue insurance</b> (optional): about €3.50 a day. Worth it: a rescue on the slopes is expensive.",
   "<b>Adaptive skiing</b> at Portes du Mont-Blanc: 50% off for the skier with a disability and their companion (at the ticket office).",
  ],
  deb_h="🐣 Beginners &amp; pedestrians",
  deb=[
   "<b>Rochebrune / Mont d'Arbois beginner pass</b>: €29 a day (carpets and small drag lifts, Chamois gondola, Rocharbois cable car). Petit Rochebrune only: €15, at the ticket office.",
   "<b>Portes du Mont-Blanc beginner pass</b>: €18 a day (Mowgli, Brons, Garettes, Plan, Covagnet, Grande Rare, Pattes carpet), at the ticket office.",
   "<b>Pedestrians</b>: €23 for an Évasion day (€20.50 child) to ride up to mountain restaurants; on Portes du Mont-Blanc, €11.50 one way and €19.50 return (child €9.50 / €15).",
  ],
  park_h="🅿️ Where to park by the slopes",
  park_head=("Car park", "Lift", "Price"),
  parks=[
   ("Megève", [
    ("Rochebrune (underground, ~400 spaces)", "Rochebrune cable car", "Paid · first 30 min free"),
    ("Rochebrune (outdoor)", "Rochebrune cable car", "Blue zone 4 h (parking disc)"),
    ("Mont d'Arbois (covered, ~300 spaces, 2.10 m)", "Mont d'Arbois gondola · Rocharbois", "Paid · first 30 min free"),
    ("Côte 2000", "Côte 2000 sector", "Free"),
    ("Princesse (Demi-Quartier, ~900 spaces)", "Princesse gondola", "Free"),
    ("Le Jaillet", "Jaillet gondola", "Blue zone 7 h (10 h lower section)"),
   ]),
   ("Combloux &amp; La Giettaz", [
    ("Les Brons (540 spaces, 3 levels)", "Mowgli drag lift · main ticket office", "Free"),
    ("La Cry (127 spaces)", "Mowgli · Beauregard chairlift", "Free"),
    ("Cuchet (217 spaces)", "Beauregard chairlift · adaptive ski", "Free"),
    ("Le Plan, La Giettaz (P1 and P2)", "Grande Rare · Tête du Torraz", "Free"),
   ]),
  ],
  park_note="The easiest in Megève: leave the car and take the free <b>Meg'bus</b> (3 lines in winter), tracked live in the Pysae app. On holiday Saturdays the free car parks in Combloux and at the Princesse fill up fast: arrive early.",
  plan_h="🗺️ Piste maps",
  plans=[("https://forfait.megeve.com/hiver/en/ski-resort-map/", "Évasion Mont-Blanc live map"),
         ("https://forfait.megeve.com/hiver/wp-content/uploads/sites/7/2025/11/2025-Plan-Megeve-Evasion-basseDef.pdf", "Évasion map (PDF)"),
         ("https://www.lesportesdumontblanc.fr/hiver/plan-des-pistes-megeve-saintgervais-combloux-lagiettaz/", "Portes du Mont-Blanc map"),
         ("https://www.lesportesdumontblanc.fr/hiver/infoneige-portes-du-mont-blanc/", "Runs open today (Portes du Mont-Blanc)")],
  plan_p="For snow and piste conditions before you go, see also our <a href=\"/en/meteo/\">Snow &amp; weather</a> and <a href=\"/en/webcams/\">Webcams</a> pages.",
  more_h="✨ Also",
  more=[
   ("🎿 Cross-country skiing", "About forty kilometres in Megève, on three sites: la Livraz – Côte 2000 (the main one, towards the altiport), the Mont d'Arbois golf course and Odier, linked to Combloux. A trail pass is required, sold at the welcome chalet."),
   ("🥾 Ski touring", "12 signposted routes on the Portes du Mont-Blanc area, keeping tourers apart from skiers. The \"Combloux Rando\" pass lets you ride the Beauregard, Pertuis and Jouty chairlifts."),
   ("🛷 Sledging", "The Luge Princesse, 3 km on snow from the Princesse, free with an Évasion pass bought in Megève, and the Luge 4S in Combloux."),
   ("👶 Ski lessons", "Ski schools (ESF and independent schools) in both Megève and Combloux, with snow gardens for little ones. Book early for Christmas and February."),
  ],
  faq=[
   ("Which lift pass do I need to ski in Megève?", "For Rochebrune, Côte 2000, Mont d'Arbois and Saint-Gervais you need the Évasion Mont-Blanc pass. If you only ski the Jaillet, Combloux and La Giettaz side, the Portes du Mont-Blanc pass is enough and cheaper (€52.50 an adult day vs €65)."),
   ("Can you ski from Megève to Combloux?", "Yes, via Le Jaillet: from the Jaillet gondola in Megève, the runs lead to Combloux and La Giettaz. However, Le Jaillet is not linked on skis to Rochebrune or Mont d'Arbois: you cross the village (free Meg'bus)."),
   ("Where can I park for free to ski?", "In Megève: the Princesse (Demi-Quartier) and Côte 2000 car parks. In Combloux: Les Brons, la Cry and Cuchet, all free at the foot of the slopes. At Le Jaillet, parking is a blue zone (disc)."),
   ("When do the slopes open this winter?", "Megève plans an early opening on the weekend of 5-6 December 2026, partial opening from 12 December and full opening on 19 December, until 4 April 2027. Portes du Mont-Blanc is open from 19 December 2026 to 21 March 2027. Everything depends on snow."),
   ("How can I pay less for my lift pass?", "Buy online in advance (Évasion day from €32 three days ahead, 6 days for the price of 5 ten days ahead), ski early or late season (20% off), use the family discount, and keep your hands-free card to reload it."),
  ],
  note=f"Official public prices {SAISON} (Remontées mécaniques de Megève and SEM Les Portes du Mont-Blanc), for information only: check before buying. Openings subject to snow.",
  links=[("https://forfait.megeve.com/hiver/en/", "Megève lift passes (Évasion)"), ("https://www.lesportesdumontblanc.fr/hiver/en/", "Les Portes du Mont-Blanc"),
         ("https://www.megeve-tourisme.fr/en/", "Megève Tourisme"), ("https://www.combloux.com/en/", "Combloux tourist office")],
 ),
}

CSS = """
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:0 0 20px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:16px 18px;box-shadow:0 8px 24px rgba(10,20,40,.06)}
.stat b{display:block;font-family:var(--display,Fraunces,serif);font-size:1.7rem;color:var(--heart);line-height:1.1}
.stat strong{display:block;margin:4px 0 2px}.stat span{color:var(--muted);font-size:.86rem;line-height:1.35;display:block}
 .domp ul{margin:8px 0}.domp li{margin:6px 0}
.sect{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:14px}
.sec{border:1px solid var(--line);border-radius:16px;padding:14px 16px}.sec:last-child{grid-column:1/-1}
.sec h3{font-size:1.1rem;margin:0 0 4px}.sec p{margin:6px 0 0;font-size:.95rem}
.tag{display:inline-block;font-size:.74rem;font-weight:800;border-radius:999px;padding:2px 9px;background:rgba(75,143,214,.14);color:var(--sky)}
.tw{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:8px 0}
table.px{border-collapse:collapse;width:100%;font-size:.94rem;min-width:520px}
.px th,.px td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}
.px thead th{font-size:.8rem;text-transform:uppercase;letter-spacing:.03em;color:var(--muted)}
.px tbody th{text-align:left;font-weight:700;white-space:normal}
.px td:nth-child(n+5){color:var(--muted)}
.px.pk{min-width:560px}.px.pk td,.px.pk th{text-align:left;white-space:normal}
.px.pk td:nth-child(n+3){color:inherit}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:0 20px}
.box ul{margin:6px 0 0;padding-left:20px}.box li{margin:6px 0}
.box h3{font-size:1.15rem;margin:16px 0 2px}
.more{display:grid;grid-template-columns:1fr 1fr;gap:14px}.more div{border:1px solid var(--line);border-radius:16px;padding:14px 16px}
.more b{display:block;margin-bottom:4px}.more p{margin:0;font-size:.95rem;color:var(--muted)}
@media(max-width:860px){.stats{grid-template-columns:1fr 1fr}}
.px.sm{min-width:0}
@media(max-width:760px){.px th,.px td{padding:7px 6px;font-size:.86rem}.px tbody th{white-space:nowrap}table.px{min-width:480px}.px.sm{min-width:0}.px.sm tbody th{white-space:normal}.px.pk{min-width:0}.px.pk thead{display:none}.px.pk tr{display:block;border-bottom:1px solid var(--line);padding:8px 0}.px.pk th,.px.pk td{display:block;border:0;padding:1px 0;white-space:normal!important}.px.pk td:last-child{font-weight:800;color:var(--pine)}.sect,.grid2,.more{grid-template-columns:1fr}.stat b{font-size:1.4rem}}
"""


def build(lang):
    d = T[lang]
    path, alt = ("/skier/", "/en/skiing/") if lang == "fr" else ("/en/skiing/", "/skier/")
    stats = '<div class="stats lift">' + "".join(f'<div class="stat"><b>{a}</b><strong>{b}</strong><span>{c}</span></div>' for a, b, c in d["stats"]) + "</div>"
    sect = "".join(f'<div class="sec"><h3>{t}</h3><span class="tag">{g}</span><p>{p}</p></div>' for t, g, p in d["secteurs"])
    dom = f'<section class="box"><h2>{d["dom_h"]}</h2><div class="domp">{d["dom_p"]}</div><div class="sect">{sect}</div></section>'
    i = 0 if lang == "fr" else 1
    eva_rows = [(r[i],) + r[2] + (r[3] if r[3] else (None, None, None)) for r in PRIX_EVA]
    pmb_rows = [(r[i],) + r[2] for r in PRIX_PMB]
    px = (f'<section class="box" id="{"prix" if lang == "fr" else "prices"}"><h2>{d["px_h"]}</h2><p class="note">{d["px_p"]}</p>'
          f'<h3>{d["eva_h"]}</h3>{table(eva_rows, d["eva_head"], lang)}<p class="note">{d["eva_note"]}</p>'
          f'<h3>{d["pmb_h"]}</h3>{table(pmb_rows, d["pmb_head"], lang, " sm")}<p class="note">{d["pmb_note"]}</p></section>')
    ul = lambda xs: "<ul>" + "".join(f"<li>{x}</li>" for x in xs) + "</ul>"
    deals = f'<div class="grid2"><section class="box"><h2>{d["deals_h"]}</h2>{ul(d["deals"])}</section><section class="box"><h2>{d["deb_h"]}</h2>{ul(d["deb"])}</section></div>'
    pk = ""
    for zone, rows in d["parks"]:
        trs = "".join(f"<tr><th scope=row>{a}</th><td>{b}</td><td>{c}</td></tr>" for a, b, c in rows)
        pk += f'<h3>{zone}</h3><div class="tw"><table class="px pk"><thead><tr>{"".join(f"<th>{h}</th>" for h in d["park_head"])}</tr></thead><tbody>{trs}</tbody></table></div>'
    park = f'<section class="box" id="parkings"><h2>{d["park_h"]}</h2>{pk}<p>{d["park_note"]}</p></section>'
    plans = ('<div class="links">' + "".join(f'<a href="{u}" target="_blank" rel="noopener">{l} ↗</a>' for u, l in d["plans"]) + "</div>")
    plan = f'<section class="box"><h2>{d["plan_h"]}</h2>{plans}<p>{d["plan_p"]}</p></section>'
    more = f'<section class="box"><h2>{d["more_h"]}</h2><div class="more">' + "".join(f"<div><b>{t}</b><p>{p}</p></div>" for t, p in d["more"]) + "</div></section>"
    links = '<div class="links">' + "".join(f'<a href="{u}" target="_blank" rel="noopener">{l} ↗</a>' for u, l in d["links"]) + "</div>"
    body = (stats + dom + px + deals + park + plan + more + faq_html(d["faq"], lang) +
            f'<section class="box"><h2>{"Liens utiles" if lang == "fr" else "Useful links"}</h2>{links}<p class="note">{d["note"]}</p></section>')
    write(path, page(lang, path, alt, d["title"], H.escape(d["desc"]), d["kicker"], d["h1"], d["intro"], body,
                     css=CSS, extra_head=faq_ld(d["faq"])))


if __name__ == "__main__":
    build("fr"); build("en")
