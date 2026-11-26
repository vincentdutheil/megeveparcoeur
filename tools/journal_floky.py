#!/usr/bin/env python3
"""« Le journal du weekend » présenté par Floky, l'ourson virtuel de Megève par cœur (Reel du jeudi, 1080x1920).

Étape 1 — texte :  python3 tools/journal_floky.py texte AAAA-MM-JJ        (AAAA-MM-JJ = le samedi du weekend)
    Récupère la météo (samedi, dimanche, lundi) et les sorties du weekend (data/agenda.json), écrit
    instagram/journal/AAAA-MM-JJ/donnees.json (météo + sorties, modifiable à la main) et
    instagram/journal/AAAA-MM-JJ/texte-heygen.txt : le texte à faire dire à Floky dans HeyGen (840 caractères max).
    Le texte est écrit « pour l'oreille » : « Pra-sur-Arly », heures et adresse du site en toutes lettres.

Étape 2 — HeyGen (à la main) : avatar Floky, voix de Floky, format vertical 9:16, FOND VERT UNI.
    Exporter la vidéo et la passer à l'étape 3.

Étape 3 — montage : python3 tools/journal_floky.py montage AAAA-MM-JJ VIDEO_HEYGEN.mp4 [--fond webcam|place-neige] [--neige|--sans-neige] [--relire]
    Détoure Floky (fond vert) et le pose « au balcon » devant la webcam du village prise au moment du montage
    (par défaut ; panoramique lent sur toute la place, à lancer vers 17h30), ou devant une photo (--fond place-neige).
    Neige qui tombe : seulement s'il neige au village à ce moment (Open-Meteo), ou forcée avec --neige / --sans-neige.
    Ajoute le titre,
    les cartes météo, les sous-titres (calés sur la voix par transcription automatique), le bandeau « SORTIES »
    et la chanson d'Akhilleus en fond très bas. Sorties : instagram/journal/AAAA-MM-JJ/journal-AAAA-MM-JJ.mp4
    et journal-AAAA-MM-JJ-cover.jpg. Les sous-titres sont écrits dans sous-titres.json : avec --relire, le script
    s'arrête après les avoir écrits (les corriger, puis relancer sans --relire : le fichier existant est réutilisé).

Dépendances : ffmpeg (avec libass), Pillow, faster-whisper (pip install faster-whisper ; modèle « small » téléchargé
au premier lancement), polices Poppins (/usr/share/fonts/truetype/google-fonts).
"""
import sys, json, math, random, re, datetime as dt, pathlib, subprocess, tempfile, urllib.request, difflib, unicodedata
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONTS = pathlib.Path("/usr/share/fonts/truetype/google-fonts")
SON = ROOT / "sons/megeve-c-est-le-reve.mp3"
LAT, LON, ALT = 45.857, 6.617, 1113          # village de Megève
W, H = 1080, 1920
NAVY, RED, WHITE = (14, 28, 70), (220, 30, 40), (255, 255, 255)
MAX_CHARS = 840
# Fonds : photo déjà mise à l'échelle ; y0 = ligne de la photo placée en haut de l'écran ; x0 = "droite" ou pixels
FONDS = {"place-neige": {"fichier": "tools/journal/fond-place-neige.jpg", "x0": "droite", "y0": 524}}
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]

def font(name, size): return ImageFont.truetype(str(FONTS / f"Poppins-{name}.ttf"), size)
def dossier(sam): d = ROOT / "instagram/journal" / sam; d.mkdir(parents=True, exist_ok=True); return d

# ---------------------------------------------------------------- nombres et oral
UNITES = "zéro un deux trois quatre cinq six sept huit neuf dix onze douze treize quatorze quinze seize".split()
DIZ = {20: "vingt", 30: "trente", 40: "quarante", 50: "cinquante"}
def en_lettres(n):
    if n < 0: return "moins " + en_lettres(-n)
    if n <= 16: return UNITES[n]
    if n < 20: return "dix-" + UNITES[n - 10]
    d, u = divmod(n, 10); base = DIZ[d * 10]
    return base if u == 0 else base + (" et un" if u == 1 else "-" + UNITES[u])
def heure_orale(h):  # "20h30" -> "vingt heures trente"
    m = re.match(r"(\d{1,2})h(\d{2})?", h or "")
    if not m: return None
    hh, mm = int(m.group(1)), int(m.group(2) or 0)
    s = ("midi" if hh == 12 else en_lettres(hh) + (" heure" if hh == 1 else " heures"))
    return s + (" " + en_lettres(mm) if mm else "")
ORAL = [("Praz-sur-Arly", "Pra-sur-Arly"), ("megeveparcoeur.fr", "megeveparcoeur point fr")]
def pour_oreille(t):
    for a, b in ORAL: t = t.replace(a, b)
    return t
def pour_ecran(t):
    for a, b in ORAL: t = t.replace(b, a)
    t = re.sub(r"\bPra-sur-Arly\b", "Praz-sur-Arly", t)
    nb = {en_lettres(n): n for n in range(60)}
    mots = "|".join(sorted(map(re.escape, nb), key=len, reverse=True))
    t = re.sub(rf"\b({mots}) heures?(?: ({mots}))?\b", lambda m: f"{nb[m.group(1)]}h" + (f"{nb[m.group(2)]:02d}" if m.group(2) else ""), t)
    t = re.sub(r"\bmidi\b(?! et)", "midi", t)
    return t

# ---------------------------------------------------------------- météo
def wmo(code, neige):
    if neige and neige >= 0.5: return "neige"
    if code in (0, 1): return "soleil"
    if code == 2: return "eclaircies"
    if code in (3, 45, 48): return "nuages"
    if 71 <= code <= 77 or code in (85, 86): return "neige"
    return "pluie"
DESC = {"soleil": "Grand soleil", "eclaircies": "Éclaircies", "nuages": "Nuageux", "pluie": "Pluie", "neige": "Neige"}

def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "megeveparcoeur.fr (github.com/vincentdutheil/megeveparcoeur)"})
    return json.load(urllib.request.urlopen(req, timeout=30))

def meteo(jours):
    try:
        d = get_json("https://api.open-meteo.com/v1/forecast?latitude=%s&longitude=%s&elevation=%s&timezone=Europe%%2FParis"
                     "&daily=weather_code,temperature_2m_max,temperature_2m_min,snowfall_sum,precipitation_sum"
                     "&start_date=%s&end_date=%s" % (LAT, LON, ALT, jours[0], jours[-1]))["daily"]
        if "error" in d: raise ValueError(d)
        return [{"date": j, "type": wmo(d["weather_code"][i], d["snowfall_sum"][i]), "min": round(d["temperature_2m_min"][i]),
                 "max": round(d["temperature_2m_max"][i]), "neige_cm": round(d["snowfall_sum"][i] or 0),
                 "source": "Open-Meteo"} for i, j in enumerate(jours)]
    except Exception as e:
        print("Open-Meteo indisponible (%s), repli sur MET Norway" % e)
    d = get_json(f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={LAT}&lon={LON}&altitude={ALT}")
    out = []
    for j in jours:
        temps, syms, pr = [], [], 0.0
        for t in d["properties"]["timeseries"]:
            loc = dt.datetime.fromisoformat(t["time"].replace("Z", "+00:00")) + dt.timedelta(hours=1)
            if loc.date().isoformat() != j: continue
            temps.append(t["data"]["instant"]["details"]["air_temperature"])
            n = t["data"].get("next_1_hours") or t["data"].get("next_6_hours") or {}
            if 8 <= loc.hour <= 17 and n: syms.append(n["summary"]["symbol_code"])
            if t["data"].get("next_1_hours"): pr += t["data"]["next_1_hours"]["details"].get("precipitation_amount", 0)
        s = " ".join(syms)
        ty = ("neige" if "snow" in s else "pluie" if ("rain" in s or "sleet" in s) else
              "soleil" if s.count("clearsky") + s.count("fair") > len(syms) / 2 else
              "eclaircies" if "partlycloudy" in s or "fair" in s else "nuages")
        out.append({"date": j, "type": ty, "min": round(min(temps)) if temps else None, "max": round(max(temps)) if temps else None,
                    "neige_cm": round(pr) if ty == "neige" else 0, "source": "MET Norway"})
    return out

# ---------------------------------------------------------------- sorties
def sorties(sam, dim):
    ev = json.load(open(ROOT / "data/agenda.json"))
    res = []
    for e in ev:
        d1, d2 = e.get("d"), e.get("d2") or e.get("d")
        jours = [j for j in (sam, dim) if d1 <= j <= d2]
        if not jours: continue
        span = (dt.date.fromisoformat(d2) - dt.date.fromisoformat(d1)).days
        score = (3 if span == 0 else 2 if span <= 3 else 0) + (2 if e.get("lieu") == "Megève" else 0) \
            + (1 if e.get("free") else 0) + (1 if e.get("kids") else 0) - (3 if "(" in e["t"] else 0) - (2 if span > 20 else 0)
        res.append({"titre": e["t"], "lieu": e.get("lieu", ""), "heure": e.get("h", ""), "jours": jours,
                    "gratuit": bool(e.get("free")), "score": score, "x": e.get("x", "")})
    res.sort(key=lambda s: -s["score"])
    vus, out = set(), []
    for s in res:
        if s["titre"] in vus: continue
        vus.add(s["titre"]); out.append(s)
    return out[:6]

def jour_court(jours, sam):
    if len(jours) == 2: return "sam. et dim."
    return "sam." if jours[0] == sam else "dim."

# ---------------------------------------------------------------- texte de Floky
BLAGUES_FROID = ["Brrr, même moi, j'ai froid aux pattes !", "Brrr, sortez les bonnets… et les pots de miel !",
                 "Brrr, j'ai la truffe toute gelée !"]
BLAGUES_SORTIES = ["Miam !", "Je garde la plus grosse part, hein !", "Moi, j'y vais en pyjama de fourrure !"]

def phrase_jour(nom, m):
    t = m["type"]
    debut = {"soleil": f"{nom}, grand soleil", "eclaircies": f"{nom}, de belles éclaircies", "nuages": f"{nom}, un ciel plutôt gris",
             "pluie": f"{nom}, sortez les parapluies", "neige": f"{nom}, il va neiger"}[t]
    if m["min"] is not None and m["min"] <= -5:
        return f"{debut}… mais {en_lettres(m['min'])} au réveil !"
    if m["max"] is not None:
        return f"{debut}, jusqu'à {en_lettres(m['max'])} degrés."
    return debut + "."

def texte(sam):
    s = dt.date.fromisoformat(sam)
    if s.weekday() != 5: sys.exit("donne la date du SAMEDI du weekend")
    jours = [(s + dt.timedelta(days=i)).isoformat() for i in range(3)]
    met = meteo(jours)
    so = sorties(jours[0], jours[1])
    sem = s.isocalendar()[1]
    intro = "Coucou, c'est Floky, l'ourson de Megève par cœur, en direct du balcon sur la place du village ! Voici votre journal du weekend !"
    p_meteo = [phrase_jour("Samedi", met[0])]
    if met[0]["min"] is not None and met[0]["min"] <= -5: p_meteo.append(BLAGUES_FROID[sem % len(BLAGUES_FROID)])
    if met[1]["type"] == met[0]["type"] and met[1]["min"] is not None and abs(met[1]["min"] - met[0]["min"]) <= 2:
        p_meteo.append("Dimanche, rebelote, même ciel et même fraîcheur !" if met[1]["min"] <= 0 else "Dimanche, rebelote, même temps !")
    else:
        p_meteo.append(phrase_jour("Dimanche", met[1]))
    if met[2]["type"] == "neige" and met[0]["type"] != "neige" and met[1]["type"] != "neige":
        p_meteo.append("Et la neige revient lundi, youpi !")
    outro = "Tout le programme sur megeveparcoeur point fr. À jeudi prochain, gros câlins d'ours !"
    def phr(x):
        quand = {"sam. et dim.": "Samedi et dimanche", "sam.": "Samedi", "dim.": "Dimanche"}[jour_court(x["jours"], jours[0])]
        h = heure_orale(x["heure"]) if x["heure"] and "–" not in x["heure"] and "-" not in x["heure"] and " et " not in x["heure"] else None
        return f"{quand}{' à ' + h if h else ''}, {x['titre'].split(' (')[0][0].lower() + x['titre'].split(' (')[0][1:]}, à {x['lieu']}" + (", c'est gratuit !" if x["gratuit"] else ".")
    choix = so[:4]
    while True:
        corps = " ".join(phr(x) for x in sorted(choix, key=lambda x: (x["jours"][0], x["heure"])))
        if choix: corps = "Côté sorties ! " + corps + " " + BLAGUES_SORTIES[sem % len(BLAGUES_SORTIES)]
        t = "\n\n".join([intro, " ".join(p_meteo), corps, outro])
        t = pour_oreille(t)
        if len(t) <= MAX_CHARS or not choix: break
        choix = choix[:-1]
    d = dossier(sam)
    donnees = {"samedi": sam, "meteo": met, "sorties": [{k: v for k, v in x.items() if k != "score"} for x in so]}
    (d / "donnees.json").write_text(json.dumps(donnees, ensure_ascii=False, indent=1))
    (d / "texte-heygen.txt").write_text(t + "\n")
    print(t, f"\n\n[{len(t)} caractères] → {d/'texte-heygen.txt'}")

# ---------------------------------------------------------------- visuels fixes
def icone(d, ty, cx, cy):
    def soleil(x, y, r):
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 200, 40))
        for k in range(8):
            a = k * math.pi / 4
            d.line([(x + math.cos(a) * r * 1.35, y + math.sin(a) * r * 1.35), (x + math.cos(a) * r * 1.8, y + math.sin(a) * r * 1.8)], fill=(255, 200, 40), width=6)
    def nuage(x, y, s, col=(235, 240, 250)):
        for dx, dy, rr in [(-s * .6, 0, s * .55), (0, -s * .3, s * .7), (s * .6, 0, s * .55)]:
            d.ellipse([x + dx - rr, y + dy - rr, x + dx + rr, y + dy + rr], fill=col)
        d.rectangle([x - s * .6, y, x + s * .6, y + s * .55], fill=col)
    def flocon(x, y, s):
        for k in range(3):
            a = k * math.pi / 3
            d.line([(x - math.cos(a) * s, y - math.sin(a) * s), (x + math.cos(a) * s, y + math.sin(a) * s)], fill=WHITE, width=6)
    if ty == "soleil": soleil(cx, cy, 38)
    elif ty == "eclaircies": soleil(cx + 30, cy - 15, 30); nuage(cx - 15, cy + 10, 48)
    elif ty == "nuages": nuage(cx - 25, cy + 5, 40, (190, 200, 220)); nuage(cx + 15, cy + 15, 48)
    elif ty == "pluie":
        nuage(cx, cy - 20, 50, (200, 210, 230))
        for dx in (-35, 0, 35): d.line([(cx + dx, cy + 40), (cx + dx - 10, cy + 65)], fill=(120, 180, 255), width=6)
    else:
        nuage(cx, cy - 20, 50, (210, 220, 240))
        for dx, dy in ((-40, 43), (0, 53), (40, 43)): flocon(cx + dx, cy + dy, 14)

def calque_ui(sam, met, credit=None):
    s = dt.date.fromisoformat(sam); dim = s + dt.timedelta(days=1)
    dates = f"{s.day}-{dim.day} {MOIS[dim.month - 1]}" if s.month == dim.month else f"{s.day} {MOIS[s.month - 1]} - {dim.day} {MOIS[dim.month - 1]}"
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    logo = Image.open(ROOT / "img/logo-rond.png").convert("RGBA").resize((200, 200), Image.LANCZOS)
    d.ellipse([36, 36, 244, 244], fill=WHITE); im.alpha_composite(logo, (40, 40))
    d.text((270, 70), "LE JOURNAL", font=font("Bold", 64), fill=WHITE)
    d.text((270, 140), "DU WEEKEND", font=font("Bold", 64), fill=(255, 90, 95))
    d.text((272, 218), f"avec Floky  ·  {dates}", font=font("Medium", 34), fill=(200, 215, 245))
    cw, ch, y0 = 320, 300, 290
    for i, (nom, m) in enumerate(zip(("SAMEDI", "DIMANCHE", "LUNDI"), met)):
        x0 = 30 + i * (cw + 25)
        carte = Image.new("RGBA", (cw, ch)); ImageDraw.Draw(carte).rounded_rectangle([0, 0, cw - 1, ch - 1], 36, fill=(14, 28, 70, 190), outline=(255, 255, 255, 140), width=3)
        im.alpha_composite(carte, (x0, y0)); cx = x0 + cw // 2
        f = font("Bold", 36); d.text((cx - d.textlength(nom, font=f) / 2, y0 + 16), nom, font=f, fill=WHITE)
        icone(d, m["type"], cx, y0 + 125)
        if i == 2 and m["type"] == "neige": l1, l2 = "Neige !", (f"~{m['neige_cm']} cm prévus" if m["neige_cm"] else "Flocons prévus")
        else:
            l1 = f"{m['min']}° / {m['max']}°" if m["min"] is not None else "—"
            l2 = DESC[m["type"]]
        for txt, fs, yy, col in [(l1, 44, y0 + 190, WHITE), (l2, 28, y0 + 248, (200, 215, 245))]:
            f = font("Bold" if fs > 30 else "Medium", fs); d.text((cx - d.textlength(txt, font=f) / 2, yy), txt, font=f, fill=col)
    # pupitre + bandeau + mention « virtuel »
    d.rectangle([0, 1440, W, 1600], fill=NAVY + (255,)); d.rectangle([0, 1440, W, 1450], fill=WHITE)
    d.rectangle([0, 1470, W, 1550], fill=RED + (255,))
    d.rectangle([0, 1600, W, H], fill=NAVY + (200,))
    f = font("Medium", 32)
    for txt, yy in [("Floky, l'ourson virtuel de Megève par cœur", 1612), ("Rendez-vous chaque jeudi !", 1657)]:
        d.text(((W - d.textlength(txt, font=f)) / 2, yy), txt, font=f, fill=(200, 215, 245))
    if credit:
        f = font("Medium", 24); d.text(((W - d.textlength(credit, font=f)) / 2, 1715), credit, font=f, fill=(150, 170, 210))
    return im

def fond_webcam(tmp):
    """Dernière image de la webcam du village (Skaping, via le site), agrandie à 1440 px de haut pour le panoramique,
    + calque : dégradé sous le titre et badge « EN DIRECT DU BALCON »."""
    req = urllib.request.Request(f"https://www.megeveparcoeur.fr/api/webcam?c=village&t={int(dt.datetime.now().timestamp())}",
                                 headers={"User-Agent": "megeveparcoeur.fr"})
    r = urllib.request.urlopen(req, timeout=60); (tmp / "cam.jpg").write_bytes(r.read())
    print("webcam du village, prise de vue :", r.headers.get("x-shot"))
    im = Image.open(tmp / "cam.jpg").convert("RGB")
    h = 1440; im = im.resize((max(W, round(im.width * h / im.height)), h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(2.5))
    im.save(tmp / "cam_big.jpg", quality=92)
    ov = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(ov)
    for y in range(460): d.line([(0, y), (W, y)], fill=NAVY + (int(200 * (1 - y / 460)),))
    d.rounded_rectangle([30, 612, 520, 662], 25, fill=RED + (235,)); d.ellipse([48, 627, 68, 647], fill=WHITE)
    d.text((82, 615), "EN DIRECT DU BALCON", font=font("Bold", 30), fill=WHITE)
    ov.save(tmp / "cam_ov.png")
    return tmp / "cam_big.jpg", tmp / "cam_ov.png"

def neige_maintenant():
    try:
        c = get_json(f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&elevation={ALT}&current=weather_code,snowfall")["current"]
        return c.get("snowfall", 0) > 0 or 71 <= c["weather_code"] <= 77 or c["weather_code"] in (85, 86)
    except Exception as e:
        print("Open-Meteo indisponible (%s), repli sur MET Norway" % e)
    try:
        d = get_json(f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={LAT}&lon={LON}&altitude={ALT}")
        n = d["properties"]["timeseries"][0]["data"].get("next_1_hours", {})
        return "snow" in n.get("summary", {}).get("symbol_code", "")
    except Exception as e:
        print("météo actuelle indisponible :", e); return False

def etiquette():
    im = Image.new("RGBA", (210, 80), WHITE); ImageDraw.Draw(im).text((22, 12), "SORTIES", font=font("Bold", 40), fill=RED); return im

def fond(nom):
    c = FONDS[nom]; ph = Image.open(ROOT / c["fichier"]).convert("RGB")
    x0 = ph.width - W if c["x0"] == "droite" else int(c["x0"])
    ph = ph.crop((x0, c["y0"], x0 + W, c["y0"] + H)).filter(ImageFilter.GaussianBlur(4))
    ph = ImageEnhance.Brightness(ph).enhance(0.9).convert("RGBA")
    ov = Image.new("RGBA", (W, H)); od = ImageDraw.Draw(ov)
    for y in range(420): od.line([(0, y), (W, y)], fill=NAVY + (int(180 * (1 - y / 420)),))
    return Image.alpha_composite(ph, ov).convert("RGB")

def neige(tmp, T=8, fps=25):
    """Boucle de 8 s de neige qui tombe (sans raccord visible), avec transparence."""
    out = tmp / "neige.mov"
    rnd = random.Random(7); fl = []
    for _ in range(170): fl.append((rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(1.5, 3), 1, rnd.uniform(0, 6.28), rnd.uniform(8, 20), rnd.randint(120, 200)))
    for _ in range(70): fl.append((rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(3.5, 6), 2, rnd.uniform(0, 6.28), rnd.uniform(15, 35), rnd.randint(190, 240)))
    (tmp / "n").mkdir(exist_ok=True)
    for f in range(T * fps):
        t = f / (T * fps); im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        for x, y, r, k, ph, amp, a in fl:
            yy = (y + k * H * t) % H; xx = (x + amp * math.sin(2 * math.pi * t * k + ph)) % W
            d.ellipse([xx - r, yy - r, xx + r, yy + r], fill=(255, 255, 255, a))
        im.filter(ImageFilter.GaussianBlur(0.8)).save(tmp / f"n/{f:03d}.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(fps), "-i", str(tmp / "n/%03d.png"), "-c:v", "qtrle", str(out)], check=True)
    return out

# ---------------------------------------------------------------- sous-titres
CORR = [(r"\bFlo(c)?k(y|i)\b", "Floky"), (r"\bme ?Jeff( Parker)?\b", "Megève par cœur"), (r"\bmegeve\b", "Megève"),
        (r"\bmegeveparcoeur\b(?!\s*\.\s*fr)", "Megève par cœur"), (r"\bMegève ?par ?c(œ|oe)ur\s*\.\s*fr\b", "megeveparcoeur.fr"), (r"\bMegève ?par ?c(œ|oe)ur ?\.fr\b", "megeveparcoeur.fr"), (r"\bmegeve\b", "Megève"), (r"\bpalais\b", "Palais"),
        (r"\bau pâtes?\b", "aux pattes"), (r"\bbalisées\b", "balisés"), (r"\bbourse au jouet\b", "bourse aux jouets"), (r"^A ", "À "),
        (r"\bComblou\b", "Combloux"), (r"\bappra sur Arl(ie|y)\b|\bPra(z)?[- ]sur[- ]Arl(ie|y)\b", "Praz-sur-Arly"),
        (r"\bmoindis\b", "moins dix"), (r"\bcorales\b", "chorales"), (r"\bYoupie\b", "Youpi"), (r"\bweek -end\b", "weekend"), (r"\bBreur\b|\bBrrrr\b", "Brrr")]
def norm(w): return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFD", w.lower()).encode("ascii", "ignore").decode())

def transcrire(video, tmp):
    from faster_whisper import WhisperModel
    import numpy as np, wave
    wav = tmp / "voix.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-ac", "1", "-ar", "16000", str(wav)], check=True)
    w = wave.open(str(wav)); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    m = WhisperModel("small", device="cpu", compute_type="int8")
    segs, _ = m.transcribe(a, language="fr", word_timestamps=True,
                           initial_prompt="Floky, Megève par cœur, Praz-sur-Arly, Combloux, Saint-Gervais, reblochon, raquettes, ski de rando, megeveparcoeur.fr")
    return [(x.start, x.end, x.word) for s in segs for x in s.words]

def decouper(mots, maxc=40):
    """mots = [(debut, fin, morceau brut avec son espace)] → [(debut, fin, ligne)] : coupe aux fins de phrase,
    aux virgules et aux pauses, puis partage en parts égales les morceaux trop longs."""
    blocs, cur = [], []
    for i, m in enumerate(mots):
        cur.append(m)
        nxt = mots[i + 1] if i + 1 < len(mots) else None
        t = "".join(x[2] for x in cur).strip()
        if not nxt or re.search(r"[.!?…]$", t) or (re.search(r"[,:;]$", t) and len(t) > 16) or (nxt[0] - m[1] > 0.35 and len(t) > 10):
            blocs.append(cur); cur = []
    if cur: blocs.append(cur)
    out = []
    for bl in blocs:
        t = "".join(x[2] for x in bl).strip(); n = math.ceil(len(t) / maxc)
        if n <= 1: out.append((bl[0][0], bl[-1][1], t)); continue
        cible, parts, cur, acc = len(t) / n, [], [], 0
        for m in bl:
            if cur and acc + len(m[2]) / 2 > cible * (len(parts) + 1) and len(parts) < n - 1 and not m[2].startswith("'"):
                parts.append(cur); cur = []
            cur.append(m); acc += len(m[2])
        parts.append(cur)
        out += [(p[0][0], p[-1][1], "".join(x[2] for x in p).strip()) for p in parts]
    return out

def corriger(t):
    t = pour_ecran(t)
    for a, b in CORR: t = re.sub(a, b, t)
    t = re.sub(r"\s+([,.…])", r"\1", t)
    t = re.sub(r"(\w)([!?:;])", r"\1 \2", t)
    return pour_ecran(t)

def sous_titres(sam, video, tmp):
    d = dossier(sam); f = d / "sous-titres.json"
    if f.exists():
        print("sous-titres existants réutilisés :", f); return json.loads(f.read_text())
    mots = transcrire(video, tmp)
    script = (d / "texte-heygen.txt").read_text() if (d / "texte-heygen.txt").exists() else ""
    sw = script.split()
    a_, b_ = [norm(x) for x in sw], [norm(m[2]) for m in mots]
    ratio = difflib.SequenceMatcher(None, a_, b_, autojunk=False).ratio() if sw else 0
    if ratio > 0.85:   # la voix suit le texte : orthographe du texte, temps de la transcription
        sm = difflib.SequenceMatcher(None, a_, b_, autojunk=False)
        tps = [None] * len(sw)
        for a, b, n in sm.get_matching_blocks():
            for k in range(n): tps[a + k] = (mots[b + k][0], mots[b + k][1])
        for i in range(len(tps)):
            if tps[i] is None:
                p = next((tps[j][1] for j in range(i - 1, -1, -1) if tps[j]), mots[0][0])
                tps[i] = (p, p + 0.25)
        brut = [(t[0], t[1], " " + w) for t, w in zip(tps, sw)]
    else:              # la voix a été changée dans HeyGen : transcription corrigée, À RELIRE
        brut = mots
        print(f"⚠ la voix ne suit pas texte-heygen.txt (ressemblance {ratio:.0%}) : sous-titres tirés de la transcription — À RELIRE")
    lignes = []
    for i, (a, b, t) in enumerate(decouper(brut)):
        t = corriger(t)
        lignes.append({"debut": round(a, 2), "fin": round(b, 2), "texte": t[:1].upper() + t[1:] if i == 0 else t})
    f.write_text(json.dumps(lignes, ensure_ascii=False, indent=1))
    return lignes

def ass(lignes, dst):
    ts = lambda t: f"0:{int(t // 60):02d}:{t % 60:05.2f}"
    h = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 0\n[V4+ Styles]\n"
         "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
         "Style: S,Poppins,60,&H00FFFFFF,&H00FFFFFF,&H00501E0A,&H64000000,1,0,0,0,100,100,0,0,3,14,0,2,120,120,500,1\n"
         "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    dst.write_text(h + "".join(f"Dialogue: 0,{ts(l['debut'])},{ts(max(l['fin'], l['debut'] + 0.6))},S,,0,0,0,,{l['texte']}\n" for l in lignes))

# ---------------------------------------------------------------- montage
def montage(sam, video, nom_fond="webcam", relire=False, neige_force=None):
    d = dossier(sam); video = pathlib.Path(video).resolve()
    donnees = json.loads((d / "donnees.json").read_text())
    tmp = pathlib.Path(tempfile.mkdtemp())
    lignes = sous_titres(sam, video, tmp)
    if relire:
        print("Relis/corrige", d / "sous-titres.json", "puis relance sans --relire."); return
    ass(lignes, tmp / "st.ass")
    webcam = nom_fond == "webcam"
    calque_ui(sam, donnees["meteo"], "Image en direct : webcam Skaping de la place du village" if webcam else None).save(tmp / "ui.png")
    etiquette().save(tmp / "etiq.png")
    bandeau = "     •     ".join(f"{s['titre'].split(' (')[0]}, {s['lieu']} · {jour_court(s['jours'], sam)}" + (f" {s['heure']}" if s["heure"] else "")
                                  + (", gratuit" if s["gratuit"] else "") for s in donnees["sorties"]) + "     •     Tout l'agenda sur megeveparcoeur.fr     •     "
    (tmp / "bandeau.txt").write_text(bandeau * 3)
    larg = ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(bandeau, font=font("Bold", 38))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1", "-i", str(video), "-frames:v", "1", str(tmp / "f.png")], check=True)
    vi = Image.open(tmp / "f.png").convert("RGB"); vw, vh = vi.size; vert = "0x%02X%02X%02X" % vi.getpixel((5, 5))
    c = round(vw * 0.972); cx, cy = round(vw * 0.014), round(vh * 0.047)
    duree = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
                                 capture_output=True, text=True, check=True).stdout)
    avec_neige = neige_force if neige_force is not None else (neige_maintenant() if webcam else True)
    print("neige qui tombe :", "oui" if avec_neige else "non")
    out, cover = d / f"journal-{sam}.mp4", d / f"journal-{sam}-cover.jpg"
    if webcam:
        cam, cam_ov = fond_webcam(tmp)
        ins = ["-loop", "1", "-i", str(cam), "-f", "lavfi", "-i", f"color=c=0x0E1C46:s={W}x{H}:r=25", "-loop", "1", "-i", str(cam_ov)]
        fc = (f"[0:v]crop={W}:1440:x='(iw-{W})*t/{duree:.2f}':y=0[cam];[1:v][cam]overlay=0:0[f0];[f0][2:v]overlay=0:0[f1];")
    else:
        fond(nom_fond).save(tmp / "fond.png")
        ins = ["-loop", "1", "-i", str(tmp / "fond.png"), "-f", "lavfi", "-i", f"color=c=black@0:s=16x16:r=25", "-loop", "1", "-i", str(tmp / "etiq.png")]
        fc = "[0:v]null[f1];"
    if avec_neige:
        ins += ["-stream_loop", "-1", "-i", str(neige(tmp))]; fc += "[f1][3:v]overlay=0:0[p];"
    else:
        ins += ["-f", "lavfi", "-i", "color=c=black:s=16x16:r=25"]; fc += "[f1]null[p];"
    ins += ["-i", str(video), "-loop", "1", "-i", str(tmp / "ui.png"), "-i", str(tmp / "etiq.png")]   # 4, 5, 6
    fc += (f"[4:v]crop={c}:{c}:{cx}:{cy},chromakey={vert}:0.16:0.06,despill=type=green,scale=860:860[fl];"
           f"[p][fl]overlay=110:600:shortest=1[a];[a][5:v]overlay=0:0:shortest=1[b];"
           f"[b]drawtext=fontfile={FONTS/'Poppins-Bold.ttf'}:textfile={tmp/'bandeau.txt'}:fontsize=38:fontcolor=white:y=1488:x=210-mod(t*170\\,{larg:.0f})[t];"
           f"[t][6:v]overlay=0:1470[s];[s]subtitles={tmp/'st.ass'}:fontsdir={FONTS},format=yuv420p[v]")
    if SON.exists():
        ins += ["-i", str(SON)]
        fc += ";[7:a]atrim=start=63,asetpts=PTS-STARTPTS,volume=0.10,afade=t=in:d=1[m];[4:a][m]amix=inputs=2:duration=first:normalize=0[au]"; amap = "[au]"
    else: amap = "4:a"
    cmd = ["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex", fc, "-map", "[v]", "-map", amap, "-c:v", "libx264", "-preset", "veryfast",
           "-crf", "20", "-r", "25", "-c:a", "aac", "-b:a", "160k", "-t", f"{duree:.2f}", "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "3", "-i", str(out), "-frames:v", "1", "-q:v", "3", str(cover)], check=True)
    print("→", out, "\n→", cover)

if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == "texte": texte(a[1])
    elif len(a) >= 3 and a[0] == "montage":
        f = a[a.index("--fond") + 1] if "--fond" in a else "webcam"
        montage(a[1], a[2], f, "--relire" in a, True if "--neige" in a else False if "--sans-neige" in a else None)
    else: sys.exit(__doc__)
