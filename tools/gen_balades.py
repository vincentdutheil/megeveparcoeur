#!/usr/bin/env python3
"""Génère le bloc « itinéraires » de /balades/ (saisons, filtres, fiches, conseils).

Les données vivent ici, en FR et EN. `python3 tools/gen_balades.py` réécrit le bloc
entre <!--WALKS--> et <!--/WALKS--> dans balades/index.html ; tools/build_en.py
appelle render("en") pour la version anglaise.
Chiffres : fiches officielles des offices de tourisme (Megève, Combloux, Praz-sur-Arly,
Haute-Savoie / Haute-Savoie Mont-Blanc Tourisme, Savoie Mont Blanc).
"""
import os, re, html
from urllib.parse import quote_plus

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MT = "https://www.megeve-tourisme.fr/en/itineraires/"
HSMB = "https://hautesavoiemontblanc-tourisme.com/offres/"
HST = "https://www.haute-savoie-tourisme.org/nature/"

# s = saison (hiver/ete) · t = type (skr ski de rando, raq raquettes, pied à pied, rando randonnée)
# l = niveau (f facile, m modéré, s sportif, "" non précisé) · v = village
# d durée, dp dénivelé +, km distance (None si la fiche ne le donne pas)
# fr/en = (titre, départ, description)
W = [
    # ------------------------------------------------------------ HIVER · ski de randonnée
    dict(s="hiver", t="skr", v="Megève", l="f", d="1h45", dp=None, km="3,6",
         fr=("Rand'Arbois", "Mont d'Arbois, route Edmond de Rothschild",
             "L'itinéraire pour débuter : une montée régulière sur le secteur du Mont d'Arbois, retour par les pistes."),
         en=("Rand'Arbois", "Mont d'Arbois, route Edmond de Rothschild",
             "The route to get started: a steady climb on the Mont d'Arbois side, back down on the pistes."),
         url=HST + "itineraires-ski/5697480-rand-arbois", q="Mont d'Arbois Megève"),
    dict(s="hiver", t="skr", v="Megève", l="s", d="2h15", dp="≈ 700 m", km="3,8",
         fr=("Randoroche", "Téléphérique de Rochebrune",
             "Pour skieurs aguerris : une montée raide et soutenue jusqu'en haut de Rochebrune."),
         en=("Randoroche", "Rochebrune cable car",
             "For experienced skiers: a steep, sustained climb to the top of Rochebrune."),
         url=HST + "itineraires-ski/5697476-randoroche", q="Téléphérique de Rochebrune Megève"),
    dict(s="hiver", t="skr", v="Megève", l="m", d="1h30", dp="455 m", km="2,8",
         fr=("La Charlotte", "Secteur du Jaillet",
             "Une belle montée en forêt jusqu'à l'arrivée de la télécabine du Jaillet, à 1 575 m."),
         en=("La Charlotte", "Le Jaillet area",
             "A lovely climb through the forest up to the top of the Jaillet gondola, at 1,575 m."),
         url="https://www.megeve-tourisme.fr/itineraires/itineraire-ski-de-randonnee-la-charlotte/", q="Télécabine du Jaillet Megève"),
    dict(s="hiver", t="skr", v="Megève", l="f", d="40 min", dp="155 m", km="2,5",
         fr=("L'Elise Allais", "Parking des Frasses",
             "Court et accessible : du parking des Frasses jusqu'au sommet de la télécabine du Jaillet."),
         en=("L'Elise Allais", "Les Frasses car park",
             "Short and accessible: from Les Frasses car park to the top of the Jaillet gondola."),
         url=HSMB + "itineraire-ski-de-randonnee-lelise-allais-megeve-fr-5885458/", q="Parking des Frasses Megève"),
    dict(s="hiver", t="skr", v="Megève", l="f", d="35 min", dp="180 m", km="1,8",
         fr=("La Cabane des Frasses", "Piste du Bel Ava",
             "Une petite montée de la piste du Bel Ava vers le chemin du col du Jaillet, parfaite pour un premier essai."),
         en=("La Cabane des Frasses", "Bel Ava piste",
             "A short climb from the Bel Ava piste towards the Col du Jaillet path, perfect for a first try."),
         url=HST + "itineraires-ski/5621716-itineraire-ski-de-randonnee-cabane-des-frasses", q="Les Frasses Megève"),
    dict(s="hiver", t="skr", v="Demi-Quartier", l="f", d="40 min", dp="200 m", km="1,2",
         fr=("Chez Fernand", "Parking de la Fouettaz",
             "Du parking de la Fouettaz par le chemin de la Ravine : court, efficace, face au Mont-Blanc."),
         en=("Chez Fernand", "La Fouettaz car park",
             "From La Fouettaz car park along the Ravine path: short and sweet, facing Mont Blanc."),
         url="https://www.megeve-tourisme.fr/itineraires/itineraire-ski-de-randonnee-chez-fernand/", q="Parking de la Fouettaz Demi-Quartier"),
    dict(s="hiver", t="skr", v="Combloux", l="f", d="30 min", dp="145 m", km="2",
         fr=("La Ravine à Claudius", "Ferme de Beauregard",
             "De la ferme de Beauregard jusqu'au sommet de la télécabine du Jaillet, en douceur."),
         en=("La Ravine à Claudius", "Beauregard farm",
             "From Beauregard farm to the top of the Jaillet gondola, at a gentle pace."),
         url=HSMB + "itineraire-ski-de-randonnee-la-ravine-a-claudius-combloux-fr-5885329/", q="Beauregard Combloux"),
    dict(s="hiver", t="skr", v="Combloux", l="s", d="1h45", dp="612 m", km="5",
         fr=("Le Plan des Dames", "Cuchet / La Cry",
             "De Cuchet au sommet des Salles (1 757 m), le point culminant de Combloux, par le Plan des Dames."),
         en=("Le Plan des Dames", "Cuchet / La Cry",
             "From Cuchet to the Sommet des Salles (1,757 m), Combloux's highest point, via the Plan des Dames."),
         url=HST + "itineraires-ski/622734-itineraire-ski-de-randonnee-le-plan-des-dames", q="Parking de la Cry Combloux"),
    dict(s="hiver", t="skr", v="Combloux", l="s", d="2h30", dp="737 m", km="5,6",
         fr=("La Crève-Cœur", "Parking du Bouchet (1 020 m)",
             "Le plus long de Combloux : loin des pistes, au calme, du Bouchet jusqu'au sommet des Salles."),
         en=("La Crève-Cœur", "Le Bouchet car park (1,020 m)",
             "Combloux's longest: away from the pistes, in peace and quiet, from Le Bouchet to the Sommet des Salles."),
         url=HST + "itineraires-ski/622736-itineraire-ski-de-randonnee-la-creve-coeur", q="Le Bouchet Combloux"),
    dict(s="hiver", t="skr", v="Praz-sur-Arly", l="", d="2 à 3 h", dp="≈ 630 m", km=None,
         fr=("« La Drè Yo », sur la trace des Martres", "Front de neige, face au chalet de l'ESF",
             "L'itinéraire balisé de Praz : départ sous le restaurant Le Serasson, descente par les pistes."),
         en=("“La Drè Yo”, on the martens' trail", "Bottom of the slopes, opposite the ESF chalet",
             "Praz's marked route: starts below Le Serasson restaurant, way down on the pistes."),
         url="https://www.prazsurarly.com/en/ski-touring", q="ESF Praz-sur-Arly"),
    # ------------------------------------------------------------ HIVER · raquettes
    dict(s="hiver", t="raq", v="Combloux", l="f", d="1h40", dp="160 m", km="3,5",
         fr=("Le Vernay – Châble d'en bas", "Parking de la Cry",
             "Une boucle tranquille, d'abord en bord de piste puis plus sauvage à travers la forêt, par Beauregard, le Châble d'en bas et le Vernay."),
         en=("Le Vernay – Châble d'en bas", "La Cry car park",
             "A gentle loop, first alongside the slopes and then wilder through the forest, via Beauregard, Le Châble d'en bas and Le Vernay."),
         url=HST + "itineraires-raquettes/103246-itineraire-raquettes-le-vernay-chable-d-en-bas", q="Parking de la Cry Combloux"),
    dict(s="hiver", t="raq", v="Combloux", l="f", d="45 min", dp=None, km="2",
         fr=("La randonnée des P'tits Loups", "Pistes de ski de fond",
             "Le circuit familial par excellence : une boucle avec des jeux pour les enfants, le long des pistes de ski de fond (on marche à côté des traces)."),
         en=("The P'tits Loups trail", "Cross-country ski trails",
             "The ultimate family route: a loop with games for children, along the cross-country ski trails (walk beside the tracks)."),
         url=HST + "itineraires-raquettes/623096-itineraire-raquettes-la-randonnee-des-p-tits-loups", q="Pistes de ski de fond Combloux"),
    dict(s="hiver", t="raq", v="Combloux", l="m", d="1h45", dp="160 m", km="4",
         fr=("Liaison Combloux – Megève", "Parking de la Cry",
             "En alpage face au Mont-Blanc, par Cuchet, Maison Neuve, la Fouettaz et Odier, jusqu'à la télécabine du Jaillet. Aller simple : prévoyez le retour."),
         en=("Combloux – Megève link", "La Cry car park",
             "Through alpine pastures facing Mont Blanc, via Cuchet, Maison Neuve, La Fouettaz and Odier, to the Jaillet gondola. One way only: plan your return."),
         url="https://www.combloux.com/itineraires/itineraire-raquettes-liaison-megeve/", q="Parking de la Cry Combloux"),
    dict(s="hiver", t="raq", v="Combloux", l="s", d=None, dp=None, km=None,
         fr=("Boucle du sommet des Salles", "Parking de la Cry",
             "Forêts et alpages jusqu'au point culminant de Combloux, avec le belvédère de la Croix des Salles. Montée par le Plan des Dames, descente par la Crève-Cœur."),
         en=("Sommet des Salles loop", "La Cry car park",
             "Forests and pastures up to Combloux's highest point, with the Croix des Salles viewpoint. Up via the Plan des Dames, down via the Crève-Cœur."),
         url=HSMB + "itineraire-raquettes-boucle-du-sommet-des-salles-combloux-fr-5982688/", q="Parking de la Cry Combloux"),
    dict(s="hiver", t="raq", v="Megève", l="m", d="40 min", dp="155 m", km="2,5",
         fr=("L'Elise Allais", "Secteur du Jaillet",
             "Un des itinéraires raquettes balisés des Portes du Mont-Blanc, à travers bois et le long des pistes. Court, mais avec un peu de montée."),
         en=("L'Elise Allais", "Le Jaillet area",
             "One of the marked snowshoe trails of the Portes du Mont-Blanc, through the woods and along the slopes. Short, but with some climbing."),
         url="https://www.megeve-tourisme.fr/itineraires/itineraire-raquette-lelise-allais/", q="Télécabine du Jaillet Megève"),
    dict(s="hiver", t="raq", v="Megève", l="m", d="1h30", dp="455 m", km="2,2",
         fr=("La Charlotte", "Parking de la télécabine du Jaillet",
             "Une vraie montée en raquettes, de la gare du Jaillet jusqu'en haut de la télécabine."),
         en=("La Charlotte", "Jaillet gondola car park",
             "A proper snowshoe climb, from the Jaillet station to the top of the gondola."),
         url=HSMB + "itineraire-raquettes-la-charlotte-megeve-fr-6083140/", q="Télécabine du Jaillet Megève"),
    dict(s="hiver", t="raq", v="Megève", l="m", d="2h", dp="212 m", km="6",
         fr=("Du Jaillet supérieur au col du Jaillet", "Haut de la télécabine du Jaillet",
             "Forêt, sous-bois et col, avec vue sur le Mont-Blanc, les Aravis et Megève en contrebas. Aller-retour ; table d'orientation et aire de pique-nique."),
         en=("Upper Jaillet to the Col du Jaillet", "Top of the Jaillet gondola",
             "Forest, woodland and a pass, with views of Mont Blanc, the Aravis and Megève below. Out and back; viewpoint indicator and picnic area."),
         url="https://www.megeve-tourisme.fr/itineraires/itineraire-raquette-du-jaillet-superieur-au-col-du-jaillet/", q="Télécabine du Jaillet Megève"),
    dict(s="hiver", t="raq", v="Megève", l="m", d=None, dp=None, km=None,
         fr=("Le Leutellet", "Chalet de la Livraz (1 400 m)",
             "Au calme du plateau de la Livraz, avec vue sur Rochebrune, le Mont Joly et l'altiport."),
         en=("Le Leutellet", "Chalet de la Livraz (1,400 m)",
             "On the quiet Livraz plateau, with views of Rochebrune, Mont Joly and the altiport."),
         url=HST + "itineraires-raquettes/6353540-itineraire-raquette-le-leutellet", q="La Livraz Megève"),
    dict(s="hiver", t="raq", v="Megève", l="s", d="1h", dp="278 m", km="4,8",
         fr=("Pierrot du Col", "Haut de la télécabine du Jaillet",
             "Pour raquettistes confirmés : un itinéraire non damé jusqu'au Christomet, à 1 853 m. Descente par les pistes damées."),
         en=("Pierrot du Col", "Top of the Jaillet gondola",
             "For experienced snowshoers: an ungroomed trail up to the Christomet, at 1,853 m. Down on the groomed slopes."),
         url="https://www.megeve-tourisme.fr/itineraires/itineraire-raquettes-pierrot-du-col/", q="Télécabine du Jaillet Megève"),
    dict(s="hiver", t="raq", v="Praz-sur-Arly", l="f", d=None, dp=None, km=None,
         fr=("Le sentier des Evettes", "Praz-sur-Arly",
             "Balisé et gratuit, à travers forêt et clairières, avec de belles vues sur les Aravis et le Val d'Arly. Accessible à tous, dès 10 ans."),
         en=("The Evettes trail", "Praz-sur-Arly",
             "Marked and free, through forest and clearings, with beautiful views of the Aravis and the Val d'Arly. For everyone aged 10 and over."),
         url="https://www.prazsurarly.com/en/snowshoeing", q="Office de tourisme Praz-sur-Arly"),
    dict(s="hiver", t="raq", v="Praz-sur-Arly", l="", d="1h40", dp=None, km=None,
         fr=("Cassioz et Thouvassières", "Parking du domaine skiable",
             "Une boucle d'environ 1h40 aller-retour au départ du domaine, entre hameaux et forêt."),
         en=("Cassioz and Thouvassières", "Ski area car park",
             "A round trip of about 1h40 from the ski area, between hamlets and forest."),
         url="https://www.prazsurarly.com/en/snowshoeing", q="Praz-sur-Arly domaine skiable parking"),
    # ------------------------------------------------------------ HIVER · à pied
    dict(s="hiver", t="pied", v="Megève", l="f", d="1h15", dp="18 m", km="1",
         fr=("9 fontaines, 2 torrents, 4 ponts", "Centre du village",
             "Une petite boucle dans le vieux Megève, de fontaine en fontaine : l'église, le vieux pont, la place de la Résistance, la passerelle sur le torrent. Idéale en fin de journée, sous les illuminations."),
         en=("9 fountains, 2 streams, 4 bridges", "Village centre",
             "A short loop through old Megève, from fountain to fountain: the church, the old bridge, Place de la Résistance, the footbridge over the stream. Ideal at dusk, under the Christmas lights."),
         url="https://www.megeve-tourisme.fr/itineraires/itineraire-hiver-9-fontaines-2-torrents-4-ponts/", q="Église Saint-Jean-Baptiste Megève"),
    dict(s="hiver", t="pied", v="Megève", l="f", d=None, dp=None, km="22,5",
         fr=("Les sentiers piétons de la Livraz", "Site nordique de la Livraz",
             "22,5 km de chemins damés pour les piétons, gratuits, sur le plateau nordique : on marche en chaussures de neige, sans raquettes."),
         en=("La Livraz footpaths", "La Livraz Nordic area",
             "22.5 km of groomed paths for walkers, free, on the Nordic plateau: just snow boots, no snowshoes needed."),
         url=None, q="Site nordique de la Livraz Megève"),
    # ------------------------------------------------------------ ÉTÉ · Megève
    dict(s="ete", v="Megève", l="f", d="20 min", dp="50 m", km="1,2",
         fr=("La boucle du lac", "Lac de Megève",
             "Le petit tour du lac, pour une première sortie avec les tout-petits."),
         en=("The lake loop", "Megève lake",
             "A short walk around the lake, perfect as a first outing with little ones."),
         url=MT + "itineraire-pieton-boucle-du-lac/", q="Lac de Megève"),
    dict(s="ete", v="Megève", l="f", d="1h15", dp="18 m", km="1",
         fr=("9 fontaines, 2 torrents, 4 ponts", "Centre du village",
             "De fontaine en fontaine dans le vieux Megève : l'église, le vieux pont et la passerelle sur le torrent."),
         en=("9 fountains, 2 streams, 4 bridges", "Village centre",
             "From fountain to fountain in old Megève: the church, the old bridge and the footbridge over the stream."),
         url=MT + "itineraire-9-fontaines-2-torrents-4-ponts/", q="Église Saint-Jean-Baptiste Megève"),
    dict(s="ete", v="Megève", l="f", d="1h", dp="155 m", km="1,6",
         fr=("Le chemin du Calvaire", "Centre du village",
             "Les chapelles du Calvaire au-dessus du village, et la vue sur toute la vallée."),
         en=("The Calvaire path", "Village centre",
             "The Calvaire chapels above the village, with a view over the whole valley."),
         url=MT + "le-chemin-du-calvaire/", q="Calvaire Megève"),
    dict(s="ete", v="Megève", l="f", d="1h", dp="80 m", km="1,8",
         fr=("Le sentier nature du Calvaire", "Le Calvaire",
             "Une boucle courte autour du Calvaire, pour découvrir la faune et la flore en famille."),
         en=("The Calvaire nature trail", "Le Calvaire",
             "A short loop around the Calvaire, to discover plants and wildlife with the family."),
         url=MT + "sentier-nature-du-calvaire/", q="Calvaire Megève"),
    dict(s="ete", v="Megève", l="f", d="1h", dp="38 m", km="2,5",
         fr=("Le chemin de Fanou", "Megève",
             "Une promenade presque à plat, facile avec une poussette tout-terrain."),
         en=("The Fanou path", "Megève",
             "An almost flat stroll, easy with an all-terrain pushchair."),
         url=MT + "le-chemin-de-fanou/", q="Megève"),
    dict(s="ete", v="Megève", l="f", d="1h05", dp="116 m", km="3,8",
         fr=("Le Moulin Contant", "Megève",
             "Au fil de l'eau jusqu'au vieux moulin, entre prés et forêt."),
         en=("Le Moulin Contant", "Megève",
             "Along the water to the old mill, between meadows and forest."),
         url=MT + "itineraire-rando-moulin-contant/", q="Megève"),
    dict(s="ete", v="Megève", l="f", d="1h30", dp="103 m", km="4,4",
         fr=("La boucle de la Croix du Bouchet", "Megève",
             "Une boucle facile et ensoleillée, avec le Mont-Blanc en ligne de mire."),
         en=("The Croix du Bouchet loop", "Megève",
             "An easy, sunny loop with Mont Blanc in sight."),
         url=MT + "itineraire-rando-boucle-de-la-croix-du-bouchet/", q="Croix du Bouchet Megève"),
    dict(s="ete", v="Megève", l="f", d="2h", dp="192 m", km="4",
         fr=("Vauvray – Ormaret", "Près du Palais",
             "Par le chemin des Ânes et la petite route de Vauvray : très facile, et un magnifique point de vue sur la chaîne du Mont-Blanc."),
         en=("Vauvray – Ormaret", "Near the Palais",
             "Via the Chemin des Ânes and the little Vauvray road: very easy, with a superb view of the Mont Blanc range."),
         url=MT + "itineraire-rando-vauvray-ormaret/", q="Le Palais Megève"),
    dict(s="ete", v="Megève", l="f", d="1h30", dp="133 m", km="5,6",
         fr=("Le chemin de Lady – Les Granges", "Megève",
             "Une jolie balade de hameau en hameau, sans difficulté."),
         en=("Chemin de Lady – Les Granges", "Megève",
             "A pretty walk from hamlet to hamlet, with no difficulty."),
         url=MT + "itineraire-rando-chemin-de-lady-les-granges/", q="Megève"),
    dict(s="ete", v="Megève", l="f", d="1h30", dp="135 m", km="4,2",
         fr=("Le Planellet – Les Pettoreaux par le Stepan", "Le Planellet",
             "Au pied du Mont d'Arbois, par le hameau des Pettoreaux : une balade surtout en descente."),
         en=("Le Planellet – Les Pettoreaux via Le Stepan", "Le Planellet",
             "At the foot of Mont d'Arbois, via the hamlet of Les Pettoreaux: a walk that is mostly downhill."),
         url=MT + "itineraire-rando-le-planellet-les-pettoreaux-par-le-stepan/", q="Le Planellet Megève"),
    dict(s="ete", v="Megève", l="f", d="2h", dp="172 m", km="4,3",
         fr=("Le Jaillet – Villard / Villaret", "Secteur du Jaillet",
             "Un secteur calme de Megève, où le Mont-Blanc se dévoile au fil du chemin."),
         en=("Le Jaillet – Villard / Villaret", "Le Jaillet area",
             "A quiet corner of Megève, where Mont Blanc slowly comes into view."),
         url=MT + "itineraire-rando-au-jaillet-villard-villaret/", q="Télécabine du Jaillet Megève"),
    dict(s="ete", v="Megève", l="m", d="1h30", dp=None, km="4",
         fr=("La cascade de la Belle au Bois", "Megève",
             "Une balade rafraîchissante jusqu'à la cascade, idéale par grosse chaleur."),
         en=("The Belle au Bois waterfall", "Megève",
             "A refreshing walk to the waterfall, ideal on a hot day."),
         url=MT + "itineraire-rando-la-cascade-de-la-belle-au-bois/", q="Cascade de la Belle au Bois Megève"),
    dict(s="ete", v="Megève", l="m", d="1h30", dp="307 m", km="4,4",
         fr=("Le lac de Javen", "Megève",
             "Une montée en forêt jusqu'au petit lac de montagne de Javen, coin pique-nique parfait."),
         en=("Lac de Javen", "Megève",
             "A climb through the forest to the little mountain lake of Javen, a perfect picnic spot."),
         url=MT + "itineraire-rando-le-lac-de-javen/", q="Lac de Javen Megève"),
    dict(s="ete", v="Megève", l="m", d="1h30", dp="472 m", km="5,6",
         fr=("Le chalet de la Vieille", "Megève",
             "Une montée franche vers les alpages et le chalet de la Vieille."),
         en=("Chalet de la Vieille", "Megève",
             "A steady climb to the high pastures and the Chalet de la Vieille."),
         url=MT + "itineraire-rando-chalet-de-la-vieille/", q="Megève"),
    dict(s="ete", v="Megève", l="m", d="2h30", dp="427 m", km="4,2",
         fr=("Sur la crête de Rochebrune", "Rochebrune",
             "Une crête facile d'accès et très panoramique, appréciée des familles."),
         en=("Along the Rochebrune ridge", "Rochebrune",
             "An easy-to-reach, very scenic ridge, popular with families."),
         url=MT + "itineraire-rando-ete-sur-la-crete-de-rochebrune/", q="Téléphérique de Rochebrune Megève"),
    dict(s="ete", v="Megève", l="m", d="2h30", dp="213 m", km="2,3",
         fr=("Le sentier du Tétras-Lyre", "Le Jaillet",
             "Sur la crête du Jaillet, avec le Mont-Blanc, les Aravis, le Beaufortain et la Vanoise au loin."),
         en=("The Tétras-Lyre trail", "Le Jaillet",
             "On the Jaillet ridge, with Mont Blanc, the Aravis, the Beaufortain and the Vanoise in the distance."),
         url=MT + "sentier-du-tetras-lyre/", q="Télécabine du Jaillet Megève"),
    dict(s="ete", v="Megève", l="m", d="2h30", dp="79 m", km="6",
         fr=("Du Jaillet supérieur au village", "Haut de la télécabine du Jaillet",
             "On monte en télécabine, on redescend à pied jusqu'au village (531 m de descente)."),
         en=("From upper Jaillet down to the village", "Top of the Jaillet gondola",
             "Ride up the gondola, walk back down to the village (531 m of descent)."),
         url=MT + "itineraires-rando-du-jaillet-superieur-au-village/", q="Télécabine du Jaillet Megève"),
    dict(s="ete", v="Megève", l="m", d="3h", dp="265 m", km="10",
         fr=("Au Leutaz", "Megève",
             "Une longue balade jusqu'au vallon du Leutaz, ses chalets et ses alpages."),
         en=("To Le Leutaz", "Megève",
             "A long walk to the Leutaz valley, its chalets and pastures."),
         url=MT + "itineraire-rando-au-leutaz/", q="Le Leutaz Megève"),
    dict(s="ete", v="Megève", l="s", d="3h45", dp="673 m", km="11,7",
         fr=("Le Mont d'Arbois – Mont Joux", "Mont d'Arbois",
             "L'incontournable : jusqu'au Mont Joux (1 958 m), avec le Mont-Blanc droit devant."),
         en=("Mont d'Arbois – Mont Joux", "Mont d'Arbois",
             "The must-do: up to Mont Joux (1,958 m), with Mont Blanc straight ahead."),
         url=MT + "itineraire-rando-le-mont-darbois-mont-joux/", q="Mont d'Arbois Megève"),
    dict(s="ete", v="Megève", l="s", d="3h30", dp="709 m", km="9,8",
         fr=("Le Christomet par les Frasses et le Mont Platard", "Les Frasses",
             "Une belle montée jusqu'au Christomet et sa vue à 360° sur les Aravis et le Mont-Blanc."),
         en=("The Christomet via Les Frasses and Mont Platard", "Les Frasses",
             "A fine climb to the Christomet and its 360° view over the Aravis and Mont Blanc."),
         url=MT + "itineraire-rando-le-christomet-par-les-frasses-et-le-mont-platard/", q="Les Frasses Megève"),
    dict(s="ete", v="Megève", l="s", d="4h", dp="806 m", km="15,2",
         fr=("Du village à Rochebrune – Côte 2000", "Parking de Rochebrune",
             "Une grande boucle par le massif de Rochebrune jusqu'à la Côte 2000, le coin le plus sauvage."),
         en=("From the village to Rochebrune – Côte 2000", "Rochebrune car park",
             "A big loop through the Rochebrune massif to Côte 2000, the wildest corner."),
         url=MT + "itineraire-rando-ete-boucle-du-village-a-rochebrune-cote-2000/", q="Téléphérique de Rochebrune Megève"),
    dict(s="ete", v="Megève", l="s", d="4h", dp="908 m", km="14",
         fr=("Le col de Véry", "Megève",
             "Une vraie randonnée de montagne jusqu'au col de Véry, entre Megève et le Beaufortain."),
         en=("Col de Véry", "Megève",
             "A proper mountain hike up to the Col de Véry, between Megève and the Beaufortain."),
         url=MT + "randonnee-col-de-very/", q="Megève"),
    dict(s="ete", v="Megève", l="s", d="5h30", dp="962 m", km="14,5",
         fr=("Col du Jaillet – Petit Croisse Baulet", "Col du Jaillet",
             "La grande crête au-dessus de Megève et Combloux, entre Aravis et vallée de l'Arve."),
         en=("Col du Jaillet – Petit Croisse Baulet", "Col du Jaillet",
             "The great ridge above Megève and Combloux, between the Aravis and the Arve valley."),
         url=MT + "itineraire-rando-col-du-jaillet-petit-croisse-baulet/", q="Col du Jaillet"),
    dict(s="ete", v="Megève", l="s", d="8h", dp="1 300 m", km="16,6",
         fr=("Le Mont Joly", "Megève",
             "Pour marcheurs confirmés : par les chalets d'Hermance jusqu'au sommet (2 525 m) et sa table d'orientation, face au Mont-Blanc, au Beaufortain, aux Aravis et aux Bauges."),
         en=("Mont Joly", "Megève",
             "For experienced walkers: via the Hermance chalets to the summit (2,525 m) and its viewpoint indicator, facing Mont Blanc, the Beaufortain, the Aravis and the Bauges."),
         url=MT + "randonnee-du-mont-joly/", q="Megève"),
    # ------------------------------------------------------------ ÉTÉ · Combloux
    dict(s="ete", v="Combloux", l="m", d="2h", dp=None, km="4,5",
         fr=("Champet – Balancerie", "Office de tourisme de Combloux",
             "Une boucle depuis le village par les petits chemins jusqu'à Ormaret et sa chapelle, face au Mont-Blanc, entre fermes et traditions agricoles."),
         en=("Champet – Balancerie", "Combloux tourist office",
             "A loop from the village along little paths to Ormaret and its chapel, facing Mont Blanc, among working farms."),
         url=HSMB + "balade-pedestre-panoramique-champet-balancerie-combloux-fr-5866473/", q="Office de tourisme Combloux"),
    dict(s="ete", v="Combloux", l="m", d="1h40", dp=None, km="5,1",
         fr=("Les alpages de Prapacot et de Planset", "Parking des Intages",
             "Une boucle tranquille entre alpages et vieux bâtis, avec vue sur la vallée de l'Arve et les Fiz. Pas de point d'eau : emportez de quoi boire."),
         en=("Prapacot and Planset pastures", "Les Intages car park",
             "A quiet loop among pastures and old buildings, with views of the Arve valley and the Fiz. No water on the way: bring your own."),
         url=HSMB + "boucle-pedestre-alpages-de-prapacot-et-de-planset-combloux-fr-5866955/", q="Les Intages Combloux"),
    dict(s="ete", v="Combloux", l="m", d="2h15", dp=None, km="5,7",
         fr=("La P'tite Ravine – Fouettaz", "Parking de Cuchet",
             "Une boucle familiale en forêt et en alpage, avec de grandes vues sur la chaîne du Mont-Blanc. Navette gratuite jusqu'à Cuchet."),
         en=("La P'tite Ravine – Fouettaz", "Cuchet car park",
             "A family loop through forest and pasture, with wide views of the Mont Blanc range. Free shuttle to Cuchet."),
         url=HSMB + "randonnee-pedestre-boucle-la-petite-ravine-fouettaz-combloux-fr-6338454/", q="Cuchet Combloux"),
    dict(s="ete", v="Combloux", l="s", d="3h30", dp=None, km="9,1",
         fr=("La Croix des Salles", "Parking de Cuchet",
             "Une demi-journée jusqu'au sommet du domaine et à la Croix des Salles, vue à 360° sur le Mont-Blanc, les Aravis et les Fiz. Retour par le lac du Jaillet."),
         en=("La Croix des Salles", "Cuchet car park",
             "A half-day up to the top of the ski area and the Croix des Salles, with a 360° view of Mont Blanc, the Aravis and the Fiz. Back via Lac du Jaillet."),
         url=HSMB + "randonnee-pedestre-la-croix-des-salles-combloux-fr-5865341/", q="Cuchet Combloux"),
    # ------------------------------------------------------------ ÉTÉ · Praz-sur-Arly
    dict(s="ete", v="Praz-sur-Arly", l="f", d=None, dp=None, km=None,
         fr=("Le Mont du Villard", "Route de Bellevarde",
             "Une petite balade entre Praz et Megève, avec un beau panorama sur le Mont-Blanc."),
         en=("Le Mont du Villard", "Route de Bellevarde",
             "A short walk between Praz and Megève, with a fine view of Mont Blanc."),
         url=HSMB + "petites-balades-le-mont-du-villard-praz-sur-arly-fr-5869510/", q="Route de Bellevarde Praz-sur-Arly"),
    dict(s="ete", v="Praz-sur-Arly", l="f", d=None, dp=None, km=None,
         fr=("Les Granges", "Praz-sur-Arly",
             "Une petite balade du Val d'Arly, entre hameaux et prairies."),
         en=("Les Granges", "Praz-sur-Arly",
             "A short Val d'Arly walk, between hamlets and meadows."),
         url=HSMB + "petites-balades-les-granges-praz-sur-arly-fr-5868388/", q="Praz-sur-Arly"),
    dict(s="ete", v="Praz-sur-Arly", l="f", d=None, dp=None, km=None,
         fr=("Le lac des Evettes", "Parking des Grabilles",
             "Le petit lac au milieu des sapins, avec les parcours ludiques Étoiles et Tétras Randos, accessibles dès 3-4 ans."),
         en=("Lac des Evettes", "Les Grabilles car park",
             "The little lake among the fir trees, with the Étoiles and Tétras Randos fun trails, suitable from age 3-4."),
         url="https://hautesavoiemontblanc-tourisme.com/a-la-une/praz-sur-arly/", q="Lac des Evettes Praz-sur-Arly"),
    dict(s="ete", v="Praz-sur-Arly", l="", d="2h30", dp=None, km=None,
         fr=("Le chemin des Contrebandiers", "Télésiège du Crêt du Midi",
             "Le télésiège monte à 1 700 m en 10 minutes ; de là, le chemin des Contrebandiers part à travers les alpages."),
         en=("The Smugglers' path", "Crêt du Midi chairlift",
             "The chairlift takes you up to 1,700 m in 10 minutes; from there, the Smugglers' path heads off across the pastures."),
         url="https://www.prazsurarly.com/en/hiking", q="Télésiège du Crêt du Midi Praz-sur-Arly"),
    dict(s="ete", v="Praz-sur-Arly", l="s", d="4h50", dp=None, km=None,
         fr=("Le Crêt du Midi", "Praz-sur-Arly",
             "Pour marcheurs confirmés (3h de montée) : une vue superbe sur toutes les montagnes alentour, au cœur des alpages de Praz."),
         en=("Le Crêt du Midi", "Praz-sur-Arly",
             "For experienced walkers (3h up): a superb view of all the surrounding mountains, in the heart of the Praz pastures."),
         url="https://www.savoie-mont-blanc.com/en/walking/confirmed-walkers-le-cret-du-midi-180155/", q="Crêt du Midi Praz-sur-Arly"),
]

VILLAGES = ["Megève", "Combloux", "Demi-Quartier", "Praz-sur-Arly"]
LV = {"f": "Facile", "m": "Modéré", "s": "Sportif"}
T = {
    "fr": dict(
        lv={"f": "Facile", "m": "Modéré", "s": "Sportif"},
        ty={"skr": "Ski de rando", "raq": "Raquettes", "pied": "À pied", "rando": "Randonnée"},
        ic={"skr": "🎿", "raq": "❄️", "pied": "🚶", "rando": "🥾"},
        winter="Balades hivernales", winter_sub="Raquettes, ski de rando &amp; balades dans la neige",
        summer="Balades estivales", summer_sub="Randonnées &amp; balades dans les alpages",
        n="itinéraires", type="Activité", vil="Village", lev="Niveau", all="Tous", start="départ",
        dur="Durée", dp="Dénivelé +", dist="Distance", off="Fiche officielle &amp; tracé ↗", pin="📍 Point de départ",
        none="Aucun itinéraire avec ces filtres.", choose="Choisis ta saison",
        before="⛑️ Avant de partir",
        safe_w=[
            "Les itinéraires en domaine skiable ne sont ouverts qu'aux heures d'ouverture des pistes (9h–16h30), et jamais la nuit : les dameuses circulent.",
            "Ski de rando : balisage jaune, descente par les pistes ; une participation de 5 € la journée ou 50 € la saison est proposée sur les Portes du Mont-Blanc. Itinéraires ouverts selon l'enneigement, de mi-décembre à fin mars environ.",
            "Raquettes : balisage violet ; ne marchez jamais dans les traces de ski de fond.",
            "Un itinéraire peut être fermé après de fortes chutes de neige ou en cas de risque d'avalanche : vérifiez la <a href=\"/meteo/\">météo &amp; la neige</a> et les <a href=\"/webcams/\">webcams</a>, et renseignez-vous à l'office de tourisme.",
            "Ne partez jamais seul, prévenez quelqu'un de votre itinéraire ; location de matériel dans les magasins de sport, sorties encadrées avec l'ESF et les bureaux des guides.",
        ],
        safe_s=[
            "La météo change vite en montagne : regardez la <a href=\"/meteo/\">météo</a> avant de partir et emportez une couche chaude et imperméable.",
            "De l'eau en quantité, de bonnes chaussures, de la crème solaire : beaucoup de sentiers n'ont aucun point d'eau.",
            "En alpage, refermez les clôtures, tenez votre chien en laisse et contournez les troupeaux et leurs chiens de protection.",
            "Les télécabines et télésièges d'été (Jaillet, Mont d'Arbois, Rochebrune, Crêt du Midi) raccourcissent bien des montées : vérifiez leurs dates d'ouverture.",
            "La carte « Belvédères du Mont-Blanc » (plus de 50 itinéraires, 300 km de sentiers) est en vente à l'office de tourisme de Praz-sur-Arly.",
        ],
        note="Durées, dénivelés et distances indiqués par les offices de tourisme, à titre indicatif ; « — » quand la fiche ne le précise pas. Sources : Megève Tourisme, offices de tourisme de Combloux et de Praz-sur-Arly, Haute-Savoie Tourisme, Haute-Savoie Mont-Blanc Tourisme, Savoie Mont Blanc.",
        meteo="/meteo/",
    ),
    "en": dict(
        lv={"f": "Easy", "m": "Moderate", "s": "Challenging"},
        ty={"skr": "Ski touring", "raq": "Snowshoes", "pied": "On foot", "rando": "Hike"},
        ic={"skr": "🎿", "raq": "❄️", "pied": "🚶", "rando": "🥾"},
        winter="Winter walks", winter_sub="Snowshoes, ski touring &amp; walks in the snow",
        summer="Summer walks", summer_sub="Hikes &amp; walks in the alpine pastures",
        n="routes", type="Activity", vil="Village", lev="Level", all="All", start="start",
        dur="Time", dp="Climb", dist="Distance", off="Official route &amp; map ↗", pin="📍 Starting point",
        none="No route matches these filters.", choose="Pick your season",
        before="⛑️ Before you go",
        safe_w=[
            "Routes inside the ski area are only open during lift hours (9am–4.30pm), never at night: the snow groomers are out.",
            "Ski touring: yellow markers, way down on the pistes; a contribution of €5 a day or €50 a season is suggested on the Portes du Mont-Blanc. Routes open depending on snow, roughly mid-December to late March.",
            "Snowshoes: purple markers; never walk in the cross-country ski tracks.",
            "A route may close after heavy snowfall or when there is avalanche risk: check the <a href=\"/en/meteo/\">snow &amp; weather</a> and the <a href=\"/en/webcams/\">webcams</a>, and ask at the tourist office.",
            "Never go alone, and tell someone your route; gear hire at the sports shops, guided outings with the ESF and the mountain guide offices.",
        ],
        safe_s=[
            "Mountain weather changes fast: check the <a href=\"/en/meteo/\">forecast</a> before you set off and take a warm, waterproof layer.",
            "Plenty of water, good shoes, sun cream: many trails have no water point at all.",
            "In the pastures, close the gates, keep your dog on a lead, and walk around herds and their guard dogs.",
            "The summer gondolas and chairlifts (Jaillet, Mont d'Arbois, Rochebrune, Crêt du Midi) cut many climbs short: check their opening dates.",
            "The “Belvédères du Mont-Blanc” map (over 50 routes, 300 km of trails) is on sale at the Praz-sur-Arly tourist office.",
        ],
        note="Times, climbs and distances as given by the tourist offices, for guidance only; “—” when the official page does not say. Sources: Megève Tourisme, Combloux and Praz-sur-Arly tourist offices, Haute-Savoie Tourisme, Haute-Savoie Mont-Blanc Tourisme, Savoie Mont Blanc.",
        meteo="/en/meteo/",
    ),
}


def e(x):
    return html.escape(x, quote=False)


def km(x, lang):
    return (x if lang == "fr" else x.replace(",", ".")) + " km"


def card(w, lang):
    L = T[lang]
    t = w.get("t", "rando")
    title, start, desc = w[lang]
    lv = w["l"]
    badge = f'<span class="lv {LV[lv]}">{L["lv"][lv]}</span>' if lv else ""
    def dp(x):
        return x if lang == "fr" else x.replace("1 300", "1,300")
    facts = [(w["d"], L["dur"]), (dp(w["dp"]) if w["dp"] else None, L["dp"]),
             (km(w["km"], lang) if w["km"] else None, L["dist"])]
    facts = "".join(f'<div><b>{v or "—"}</b><span>{k}</span></div>' for v, k in facts)
    links = ""
    if w["url"]:
        links += f'<a href="{w["url"]}" target="_blank" rel="noopener">{L["off"]}</a>'
    links += f'<a href="https://www.google.com/maps/search/?api=1&amp;query={quote_plus(w["q"])}" target="_blank" rel="noopener">{L["pin"]}</a>'
    return (f'<article class="walk" data-s="{w["s"]}" data-t="{t}" data-v="{w["v"]}" data-l="{lv}">\n'
            f'  <div class="top"><span class="chip {w["v"]}">{w["v"]}</span>{badge}</div>\n'
            f'  <h2>{L["ic"][t]} {e(title)}</h2>\n'
            f'  <p class="type">{L["ty"][t]} · {L["start"]}{" :" if lang == "fr" else ":"} {e(start)}</p>\n'
            + f'  <div class="facts">{facts}</div>\n'
            f'  <p>{e(desc)}</p>\n'
            f'  <div class="links">{links}</div>\n'
            f'</article>')


def render(lang):
    L = T[lang]
    nw = sum(w["s"] == "hiver" for w in W)
    ns = sum(w["s"] == "ete" for w in W)
    def pill(k, x, label, seasons):
        return f'<button class="pill" data-x="{x}" data-in="{seasons}" aria-pressed="{"true" if not x else "false"}">{label}</button>'
    types = "".join(pill("t", t, f'{L["ic"][t]} {L["ty"][t]}', "hiver") for t in ("raq", "skr", "pied"))
    vil = ""
    for v in VILLAGES:
        ss = " ".join(s for s in ("hiver", "ete") if any(w["v"] == v and w["s"] == s for w in W))
        vil += pill("v", v, v, ss)
    lev = "".join(pill("l", k, L["lv"][k], "hiver ete") for k in ("f", "m", "s"))
    allp = pill("", "", L["all"], "hiver ete")
    cards = "\n".join(card(w, lang) for w in W)
    li = lambda xs: "".join(f"<li>{x}</li>" for x in xs)
    return f"""<!--WALKS-->
  <div class="season" id="season" role="group" aria-label="{L['choose']}">
    <button class="sz hiver" data-s="hiver" aria-pressed="true"><span class="sz-i" aria-hidden="true">❄️</span><span><b>{L['winter']}</b><small>{L['winter_sub']} · {nw} {L['n']}</small></span></button>
    <button class="sz ete" data-s="ete" aria-pressed="false"><span class="sz-i" aria-hidden="true">☀️</span><span><b>{L['summer']}</b><small>{L['summer_sub']} · {ns} {L['n']}</small></span></button>
  </div>
  <div class="bar" id="bar">
    <span class="lab" data-in="hiver">{L['type']}</span><div class="pills" data-k="t" data-in="hiver">{allp}{types}</div>
    <span class="lab">{L['vil']}</span><div class="pills" data-k="v">{allp}{vil}</div>
    <span class="lab">{L['lev']}</span><div class="pills" data-k="l">{allp}{lev}</div>
    <span class="count" id="count" aria-live="polite"></span>
  </div>
  <div class="list" id="list">
{cards}
  </div>
  <p class="empty" id="empty" hidden>{L['none']}</p>
  <div class="safe" data-in="hiver">
    <h3>{L['before']}</h3>
    <ul>{li(L['safe_w'])}</ul>
  </div>
  <div class="safe ete" data-in="ete" hidden>
    <h3>{L['before']}</h3>
    <ul>{li(L['safe_s'])}</ul>
  </div>
  <p class="note" style="margin-top:16px">{L['note']}</p>
<script>
(function(){{
const N="{L['n']}";const st={{s:"hiver",t:"",v:"",l:""}};
const ws=[...document.querySelectorAll(".walk")];
function run(){{let n=0;ws.forEach(w=>{{const h=w.dataset.s!==st.s||(st.t&&w.dataset.t!==st.t)||(st.v&&w.dataset.v!==st.v)||(st.l&&w.dataset.l!==st.l);w.hidden=h;if(!h)n++;}});
  document.getElementById("count").textContent=n+" "+N;document.getElementById("empty").hidden=n>0;}}
function reset(g){{g.querySelectorAll(".pill").forEach(x=>x.setAttribute("aria-pressed",!x.dataset.x));st[g.dataset.k]="";}}
function season(s,push){{st.s=s;document.querySelectorAll("#season .sz").forEach(b=>b.setAttribute("aria-pressed",b.dataset.s===s));
  document.body.dataset.season=s;
  document.querySelectorAll("[data-in]").forEach(x=>{{if(x.classList.contains("pill")&&!x.dataset.x)return;x.hidden=!x.dataset.in.split(" ").includes(s);}});
  document.querySelectorAll("#bar .pills").forEach(g=>{{const on=g.querySelector('.pill[aria-pressed="true"]');if(on&&on.hidden)reset(g);if(g.hidden)reset(g);}});
  if(push)history.replaceState(null,"","#"+s);run();}}
document.getElementById("season").addEventListener("click",e=>{{const b=e.target.closest(".sz");if(b)season(b.dataset.s,true);}});
document.getElementById("bar").addEventListener("click",e=>{{const b=e.target.closest(".pill");if(!b)return;const g=b.parentElement;g.querySelectorAll(".pill").forEach(x=>x.setAttribute("aria-pressed",x===b));st[g.dataset.k]=b.dataset.x;run();}});
const h=location.hash.slice(1),m=new Date().getMonth()+1;
season(h==="ete"||h==="hiver"?h:(m>=5&&m<=10?"ete":"hiver"),false);
}})();
</script>
<!--/WALKS-->"""


def inject(page, lang):
    return re.sub(r"<!--WALKS-->.*?<!--/WALKS-->", lambda _: render(lang), page, flags=re.S)


if __name__ == "__main__":
    p = os.path.join(ROOT, "balades", "index.html")
    s = open(p, encoding="utf-8").read()
    if "<!--WALKS-->" not in s:
        sys_exit = "marqueurs <!--WALKS--> absents"
        raise SystemExit(sys_exit)
    open(p, "w", encoding="utf-8").write(inject(s, "fr"))
    print("ok balades/ :", sum(w["s"] == "hiver" for w in W), "hiver,", sum(w["s"] == "ete" for w in W), "été")
