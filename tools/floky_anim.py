#!/usr/bin/env python3
"""Floky qui parle, sans HeyGen : voix gratuite (Piper, hors ligne) + animation maison à partir des dessins de Floky.

    python3 tools/floky_anim.py preparer DOSSIER_IMAGES     (une fois : découpe les 29 dessins en calques → tools/floky/)
    python3 tools/floky_anim.py voix TEXTE.txt SORTIE.wav [--voix tom]
    python3 tools/floky_anim.py anim TEXTE.txt SORTIE.mp4 [--voix tom]   (vidéo 1080x1920 fond vert + voix, comme HeyGen)

La bouche suit les phonèmes réels de la voix (alignement Piper), les yeux clignent, et Floky change d'expression
et de geste selon les mots du texte (coucou → salut de la main, froid/brrr → grelotte, soleil → yeux qui brillent…).
Dépendances : pip install piper-tts onnx numpy pillow ; ffmpeg. Les voix sont téléchargées au premier lancement
dans ~/.cache/floky-voix (Hugging Face, rhasspy/piper-voices).
"""
import sys, json, math, random, re, pathlib, subprocess, unicodedata, urllib.request, wave
import numpy as np
from PIL import Image, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "tools/floky"
CACHE = pathlib.Path.home() / ".cache/floky-voix"
W, H, FPS = 1080, 1920, 25
VERT = (2, 171, 67)
VOIX = {"tom": "fr/fr_FR/tom/medium/fr_FR-tom-medium", "siwis": "fr/fr_FR/siwis/medium/fr_FR-siwis-medium",
        "upmc": "fr/fr_FR/upmc/medium/fr_FR-upmc-medium"}
HAUTEUR_VOIX = 1.18          # voix « ourson » : un peu plus aiguë, même débit

# Numéros des dessins (ordre d'envoi par Vincent, 27/11/2026)
POSES = {"repos": 1, "coucou": 26, "pouce": 27, "doigt": 28, "bras": 29}
BOUCHES = {"repos": 1, "ferme": 10, "neutre": 2, "dents": 3, "e": 4, "a": 5, "o": 6, "ou": 7, "f": 8, "ah": 9}
YEUX = {"normal": 1, "plisses": 12, "fermes_rose": 13, "grands": 14, "clin": 15, "emu": 16, "pensif": 17, "sourcil": 18,
        "malin": 19, "gene": 20, "brillants": 21, "fermes": 22, "miam": 23, "froid": 24}
VISAGES = {"rire": 25, "miam": 23, "brrr": 24}            # visage complet (bouche comprise), Floky ne parle pas
ZONE_TETE = (180, 250, 850, 610)                          # x0, y0, x1, y1 dans le dessin 1024x1536
BOUCHE_Y, BOUCHE_X = 440, (370, 660)

# ------------------------------------------------------------------ préparation des calques
def detourer(im):
    a = np.asarray(im.convert("RGB")).astype(np.float32)
    d = np.sqrt(((a - np.array(VERT, np.float32)) ** 2).sum(2))
    al = np.clip((d - 45) / 70, 0, 1)
    g = a[..., 1]; m = np.maximum(a[..., 0], a[..., 2])
    a[..., 1] = np.where(al < 1, np.minimum(g, m + (g - m) * al * 0.3), g)      # despill sur les bords
    return Image.fromarray(np.dstack([a, al * 255]).astype(np.uint8), "RGBA")

def calque(img, ref, zone):
    a, r = np.asarray(img).astype(int), np.asarray(ref).astype(int)
    d = np.abs(a - r).sum(2) > 45
    x0, y0, x1, y1 = ZONE_TETE; z = np.zeros_like(d); z[y0:y1, x0:x1] = True
    yy, xx = np.mgrid[:d.shape[0], :d.shape[1]]
    bouche = (yy >= BOUCHE_Y) & (xx >= BOUCHE_X[0]) & (xx <= BOUCHE_X[1])
    z &= bouche if zone == "bouche" else ~bouche
    m = Image.fromarray(((d & z) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(13)).filter(ImageFilter.GaussianBlur(3))
    m = Image.fromarray((np.asarray(m) * z).astype(np.uint8))
    bb = m.getbbox()
    if not bb: return None
    lay = img.convert("RGBA"); lay.putalpha(m)
    return lay.crop(bb), bb[:2]

def preparer(dossier):
    src = {int(re.sub(r"\D", "", p.stem)): p for p in pathlib.Path(dossier).glob("*.png")}
    load = lambda n: Image.open(src[n]).convert("RGB").resize((1024, 1536), Image.LANCZOS)
    ASSETS.mkdir(parents=True, exist_ok=True); ref = load(1); idx = {"poses": {}, "bouches": {}, "yeux": {}, "visages": {}}
    for nom, n in POSES.items():
        detourer(load(n)).save(ASSETS / f"pose-{nom}.png", optimize=True); idx["poses"][nom] = f"pose-{nom}.png"
    for cat, table, zones in (("bouches", BOUCHES, ["bouche"]), ("yeux", YEUX, ["yeux"]), ("visages", VISAGES, ["yeux", "bouche"])):
        for nom, n in table.items():
            parts = []
            for z in zones:
                r = calque(load(n), ref, z)
                if r:
                    f = f"{cat[:-1]}-{nom}-{z}.png"; r[0].save(ASSETS / f, optimize=True); parts.append([f, list(r[1])])
            idx[cat][nom] = parts
    (ASSETS / "calques.json").write_text(json.dumps(idx, indent=1))
    print("calques →", ASSETS)

# ------------------------------------------------------------------ voix
def modele(nom):
    CACHE.mkdir(parents=True, exist_ok=True); base = VOIX[nom]; f = CACHE / (base.split("/")[-1] + ".onnx")
    for ext in (".onnx", ".onnx.json"):
        g = CACHE / (base.split("/")[-1] + ext)
        if not g.exists():
            print("téléchargement de la voix", g.name)
            urllib.request.urlretrieve(f"https://huggingface.co/rhasspy/piper-voices/resolve/main/{base}{ext}", g)
    return f

# Le texte est écrit « pour l'oreille » de HeyGen ; quelques retouches pour la prononciation de Piper
ORAL = [(r"\bFloky\b", "Floki"), (r"\bMeugève\b", "Megève"), (r"\bmegeveparcoeur point fr\b", "Megève par cœur point f r"),
        (r"\bBr+\b", "Brrrou"), (r"\bArly\b", "Arli"), (r"\bPraz\b", "Pra")]
def pour_piper(t):
    for a, b in ORAL: t = re.sub(a, b, t, flags=re.I)
    return t

def voix(texte, sortie, nom="tom"):
    """Écrit la voix (wav 44,1 kHz) et renvoie [(début s, fin s, phonème)]."""
    from piper import PiperVoice, SynthesisConfig
    texte = pour_piper(texte.replace("\n", " "))
    v = PiperVoice.load(str(modele(nom)), include_alignments=True)
    morceaux, phon, t = [], [], 0.0
    for c in v.synthesize(texte, SynthesisConfig(length_scale=0.98), include_alignments=True):
        sr = c.sample_rate; a = c.audio_int16_array
        for al in c.phoneme_alignments or []:
            d = int(al.num_samples) / sr; phon.append((t, t + d, al.phoneme)); t += d
        t = sum(len(m) for m in morceaux) / sr + len(a) / sr      # recale sur l'audio réel
        morceaux.append(a)
        pause = np.zeros(int(sr * 0.12), np.int16); morceaux.append(pause); t += len(pause) / sr
    brut = pathlib.Path(sortie).with_suffix(".brut.wav")
    with wave.open(str(brut), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(np.concatenate(morceaux).tobytes())
    # plus aigu sans changer la durée (le calage des phonèmes reste exact)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(brut), "-af",
                    f"asetrate={int(sr * HAUTEUR_VOIX)},atempo={1 / HAUTEUR_VOIX:.5f},aresample=44100,loudnorm=I=-16:TP=-1.5",
                    "-ar", "44100", str(sortie)], check=True)
    brut.unlink()
    return phon

def minutage(texte, phon):
    """[(début, fin, " mot")] pour les sous-titres, avec les mots du texte d'origine. Piper découpe en phrases
    (« ^ … $ ») et sépare les mots par des espaces : si le nombre de mots colle, chaque mot a son temps exact,
    sinon les mots de la phrase sont répartis au prorata sur le temps réellement parlé."""
    phrases = [p for p in re.split(r"(?<=[.!?])\s+", texte.strip().replace("\n", " ")) if p.strip()]
    blocs, cur, mot = [], [], []
    for a, b, p in phon:
        if p == "^": cur, mot = [], []
        elif p in ("$", " ", ",", ".", "!", "?", ":", ";", "…", "-"):
            if mot: cur.append((mot[0][0], mot[-1][1])); mot = []
            if p == "$": blocs.append(cur)
        else: mot.append((a, b))
    if len(blocs) != len(phrases):
        phrases, blocs = [" ".join(phrases)], [[x for bl in blocs for x in bl]]
    out = []
    for ph, gr in zip(phrases, blocs):
        m2 = []
        for m in re.findall(r"\S+", ph):          # ponctuation isolée (« ! », « » ») collée au mot voisin
            if m2 and not re.search(r"\w", m) and m != "«": m2[-1] += " " + m
            elif m2 and m2[-1] == "«": m2[-1] += " " + m
            else: m2.append(m)
        if not gr: continue
        if len(gr) == len(m2):
            out += [(round(a, 2), round(b, 2), " " + m) for (a, b), m in zip(gr, m2)]; continue
        # sinon : chaque début de mot est accroché au début de groupe de la voix le plus proche (au prorata des lettres)
        poids = np.cumsum([0] + [b - a for a, b in gr]); poids = poids / poids[-1]
        L = sum(len(m) + 1 for m in m2); acc, deb = 0, []
        for m in m2:
            j = int(np.argmin(np.abs(poids[:-1] - acc / L))); deb.append(max(j, deb[-1] if deb else 0)); acc += len(m) + 1
        for i, m in enumerate(m2):
            j = deb[i]; k = deb[i + 1] if i + 1 < len(m2) else len(gr)
            out.append((gr[j][0], gr[max(j, k - 1)][1], " " + m))
    return [(float(a), float(b), m) for a, b, m in out]

# ------------------------------------------------------------------ choix des bouches
VOY = {"a": "a", "ɑ": "a", "ɛ": "e", "e": "e", "ə": "e", "ø": "e", "œ": "e", "i": "dents", "y": "ou", "o": "o", "ɔ": "o", "u": "ou"}
CONS = {"p": "ferme", "b": "ferme", "m": "ferme", "f": "f", "v": "f", "s": "dents", "z": "dents", "ʃ": "ou", "ʒ": "ou",
        "t": "e", "d": "e", "n": "e", "l": "ah", "k": "e", "g": "e", "ʁ": "e", "j": "e", "ɥ": "ou", "w": "ou", "ɲ": "e", "ŋ": "e"}

def bouches(phon, n_img, energie):
    """Une bouche par image vidéo."""
    seq = []                                   # (début, fin, forme)
    for i, (a, b, p) in enumerate(phon):
        if p in ("ˈ", "ˌ", "̃", "ː") and seq: seq[-1] = (seq[-1][0], b, seq[-1][2]); continue
        if p in VOY:
            f = VOY[p]
            nas = i + 1 < len(phon) and phon[i + 1][2] == "̃"
            if nas and f == "a": f = "o" if p == "ɑ" else "ah"
            seq.append((a, b, f))
        elif p in CONS:
            if b - a < 0.07 and CONS[p] not in ("ferme", "f") and seq and seq[-1][2] in set(VOY.values()) | {"ah"}:
                seq[-1] = (seq[-1][0], b, seq[-1][2])
            else: seq.append((a, b, CONS[p]))
        else: seq.append((a, b, "repos"))
    out = []
    for k in range(n_img):
        if k % 2: out.append(out[-1]); continue        # « en deux » : une forme pour 2 images
        t = (k + 1) / FPS
        f = next((s[2] for s in seq if s[0] <= t < s[1]), "repos")
        e = energie[k] if k < len(energie) else 0
        if f == "a" and e < 0.45: f = "ah"
        if f != "repos" and e < 0.06: f = "ferme" if f == "ferme" else "neutre"
        out.append(f)
    return out

def tenir(seq, n):
    """Les états qui durent moins de n images rejoignent le plus long de leurs deux voisins (sans effet de cascade)."""
    runs = []
    for v in seq:
        if runs and runs[-1][0] == v: runs[-1][1] += 1
        else: runs.append([v, 1])
    for _ in range(3):
        i = 1
        while i < len(runs):
            if runs[i][1] < n and len(runs) > 1:
                g = runs[i - 1] if i == len(runs) - 1 or runs[i - 1][1] >= runs[i + 1][1] else runs[i + 1]
                g[1] += runs[i][1]; runs.pop(i)
                j = max(1, i - 1)          # refusionne les voisins devenus identiques
                k = 1
                while k < len(runs):
                    if runs[k][0] == runs[k - 1][0]: runs[k - 1][1] += runs[k][1]; runs.pop(k)
                    else: k += 1
                i = j
            else: i += 1
    return [v for v, c in runs for _ in range(c)]

def energie_audio(wav):
    w = wave.open(str(wav)); sr = w.getframerate(); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    hop = sr // FPS; n = len(a) // hop
    e = np.array([np.sqrt((a[i * hop:(i + 1) * hop] ** 2).mean()) for i in range(n)])
    return e / (np.percentile(e, 95) + 1e-6), n

# ------------------------------------------------------------------ mise en scène selon le texte
REGLES = [  # (motif, yeux pendant la phrase, geste, visage muet à la fin de la phrase)
    (r"\b(coucou|bonjour|salut|hello)\b", "brillants", "coucou", None),
    (r"\b(brrr+|glagla)\b", "froid", None, "brrr"),
    (r"\b(froid|gel|glacial|moins \w+ degrés?|frisquet|bonnets?)\b", "froid", None, None),
    (r"\b(miam|raclette|fondue|tartiflette|reblochon|chocolat|crêpes?|gourmand\w*|goûter|marché)\b", "plisses", None, "miam"),
    (r"\b(haha|hihi|rigol\w*)\b", "plisses", None, "rire"),
    (r"\b(neige|flocons?|poudreuse)\b", "grands", "bras", None),
    (r"\b(soleil|grand beau|magnifique|génial|super|top|parfait)\b", "brillants", "pouce", None),
    (r"\b(pluie|pleut|gris|nuages?|dommage|couvert)\b", "gene", None, None),
    (r"\?", "pensif", None, None),
    (r"\b(megeveparcoeur|site|agenda|rendez-vous|n'oubliez pas|pensez à)\b", "malin", "doigt", None),
    (r"\b(bon weekend|bon week-end|à jeudi|à la semaine prochaine|bisous)\b", "clin", "bras", None),
]

def scenario(texte, phon, n_img, energie):
    """Yeux, geste et visage muet pour chaque image, phrase par phrase (les phrases sont repérées par les pauses de la voix)."""
    phrases = [p.strip() for p in re.split(r"(?<=[.!?])\s+", texte.strip().replace("\n", " ")) if p.strip()]
    fins = [a for a, b, p in phon if p == "$"]
    debuts = [b for a, b, p in phon if p == "^"]
    if len(fins) != len(phrases):
        tot = n_img / FPS; L = sum(len(p) for p in phrases); acc = 0; fins = []
        for p in phrases: acc += len(p); fins.append(tot * acc / L)
    bornes, t0 = [], 0.0
    for p, f in zip(phrases, fins): bornes.append((t0, f, p)); t0 = f
    yeux, geste, muet = ["normal"] * n_img, ["repos"] * n_img, [None] * n_img
    rnd = random.Random(len(texte))
    for i, (a, b, p) in enumerate(bornes):
        ka, kb = int(a * FPS), min(n_img, int(b * FPS) + 1)
        y, g, v = ("plisses" if rnd.random() < 0.3 else "normal"), None, None
        for motif, yy, gg, vv in REGLES:
            if re.search(motif, p, re.I):
                y = yy or y; g = g or gg; v = v or vv
                if gg or vv: break
        for k in range(ka, kb): yeux[k] = y
        if g:   # le geste dure ~2,4 s depuis le début de la phrase
            for k in range(ka + 3, min(kb + 8, ka + 63, n_img)): geste[k] = g
        if v:   # petite mimique muette pendant le silence qui suit la phrase
            fin_muet = int(debuts[i + 1] * FPS) if len(debuts) == len(phrases) and i + 1 < len(debuts) else kb + 14
            for k in range(kb, min(n_img, max(kb + 8, fin_muet), kb + 18)): muet[k] = v
    yeux, geste = tenir(yeux, 12), tenir(geste, 20)
    # clignements naturels toutes les 2,5 à 5 s : mi-clos, fermé, fermé, mi-clos
    k = 20
    while k < n_img - 4:
        if all(yeux[j] in ("normal", "brillants", "grands", "malin", "pensif", "gene", "sourcil") for j in range(k - 2, k + 6)):
            for j, e in zip(range(k, k + 4), ("plisses", "fermes", "fermes", "plisses")): yeux[j] = e
        k += int(FPS * rnd.uniform(2.5, 5))
    return yeux, geste, muet

# ------------------------------------------------------------------ rendu
CADRE = (15, 90, 1050)       # carré 1050 px en (15, 90) : la zone que journal_floky.py découpe dans une vidéo 1080x1920
SOURCE = (-20, 40, 1064)     # carré découpé dans le dessin : de la tête aux genoux
FONDU = {"bouche": 2, "yeux": 3, "pose": 1}   # geste : coupe franche + rebond (un fondu ferait un bras fantôme)   # durée des fondus, en images

class Floky:
    def __init__(self):
        idx = json.loads((ASSETS / "calques.json").read_text())
        L = lambda parts: [(Image.open(ASSETS / f).convert("RGBA"), tuple(xy)) for f, xy in parts]
        self.poses = {}
        for k, f in idx["poses"].items():      # prémultiplié : les fondus ne font pas ressortir le vert
            a = np.asarray(Image.open(ASSETS / f).convert("RGBA")).astype(np.float32) / 255; a[..., :3] *= a[..., 3:]; self.poses[k] = a
        self.calques = {("b", k): L(v) for k, v in idx["bouches"].items()}
        self.calques.update({("y", k): L(v) for k, v in idx["yeux"].items()})
        self.calques.update({("v", k): L(v) for k, v in idx["visages"].items()})
        self.cache = {}

    def visage(self, yeux, bouche):
        """Calques du visage seuls (prémultipliés, zone de la tête) : yeux + bouche, ou visage muet complet."""
        cle = (yeux, bouche)
        if cle not in self.cache:
            x0, y0, x1, y1 = ZONE_TETE
            c = Image.new("RGBA", (1024, 1536), (0, 0, 0, 0))
            parts = self.calques.get(("v", yeux[2:]), []) if yeux.startswith("v:") else \
                self.calques.get(("y", yeux), []) + self.calques.get(("b", bouche), [])
            for im, xy in parts: c.alpha_composite(im, xy)
            a = np.asarray(c.crop((x0, y0, x1, y1))).astype(np.float32) / 255
            a[..., :3] *= a[..., 3:]
            self.cache[cle] = a
        return self.cache[cle]

    def dessin(self, pose, yeux, bouche):
        """pose/yeux/bouche = (état précédent, état actuel, poids 0→1)."""
        pa, pb, wp = pose
        P = self.poses[pb] if wp >= 1 or pa == pb else self.poses[pa] * (1 - wp) + self.poses[pb] * wp
        ya, yb, wy = yeux; ba, bb, wb = bouche
        F = sum(w * self.visage(y, b) for y, b, w in
                ((ya, ba, (1 - wy) * (1 - wb)), (yb, ba, wy * (1 - wb)), (ya, bb, (1 - wy) * wb), (yb, bb, wy * wb)) if w > 0.001)
        x0, y0, x1, y1 = ZONE_TETE
        P = P.copy(); zone = P[y0:y1, x0:x1]
        zone[...] = F + zone * (1 - F[..., 3:])
        al = P[..., 3:]; P[..., :3] = np.where(al > 0, P[..., :3] / np.maximum(al, 1e-6), 0)
        return Image.fromarray((np.clip(P, 0, 1) * 255).astype(np.uint8), "RGBA")

def ease(x): x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)

def transitions(seq, d):
    """[(précédent, actuel, poids)] : chaque changement d'état se fait en fondu sur d images."""
    out, prec, k0 = [], seq[0], -999
    for k, v in enumerate(seq):
        if k and v != seq[k - 1]: prec, k0 = seq[k - 1], k
        w = 1.0 if d <= 1 else ease((k - k0 + 1) / d)
        out.append((prec, v, w))
    return out

def composer(fl, pose, yeux, bouche, t, parle, rebond):
    im = fl.dessin(pose, yeux, bouche)
    # balancement lent + respiration + léger hochement quand il parle + petit rebond quand il change de geste
    ang = 1.2 * math.sin(t * 1.1) + 0.9 * parle * math.sin(t * 3.4)
    dy = -10 * parle * abs(math.sin(t * 3.4)) - 14 * rebond
    sc = 1 + 0.008 * math.sin(t * 2.2) + 0.025 * rebond
    im = im.rotate(ang, Image.BICUBIC, center=(512, 1480))
    x0, y0, s = SOURCE
    cad = Image.new("RGBA", (s, s), (0, 0, 0, 0)); cad.alpha_composite(im, (-x0, -y0))
    taille = int(CADRE[2] * sc)
    cad = cad.resize((taille, taille), Image.BICUBIC)
    out = Image.new("RGB", (W, H), VERT)
    cx, cy = CADRE[0] + CADRE[2] // 2, CADRE[1] + CADRE[2]
    out.paste(cad, (cx - taille // 2, int(cy - taille + dy)), cad)
    return out

def anim(texte_f, sortie, nom_voix="tom"):
    texte = pathlib.Path(texte_f).read_text().strip(); sortie = pathlib.Path(sortie)
    wav = sortie.with_suffix(".wav")
    phon = voix(texte, wav, nom_voix)
    energie, n = energie_audio(wav)
    n += FPS // 2                                      # petite marge après la dernière syllabe
    bo = bouches(phon, n, energie); yeux_, geste, muet = scenario(texte, phon, n, energie)
    # un visage muet (rire, miam, brrr) remplace yeux et bouche
    yeux_ = [f"v:{m}" if m else y for y, m in zip(yeux_, muet)]
    bo = ["repos" if m else b for b, m in zip(bo, muet)]
    Tb, Ty, Tp = transitions(bo, FONDU["bouche"]), transitions(yeux_, FONDU["yeux"]), transitions(geste, FONDU["pose"])
    # le clignement se fait sans fondu (déjà progressif)
    Ty = [(a, b, 1.0) if "fermes" in (a, b) or b == "plisses" and a == "fermes" else (a, b, w) for a, b, w in Ty]
    fl = Floky()
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-i", str(wav), "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p",
                          "-af", "apad", "-c:a", "aac", "-b:a", "192k", "-shortest", str(sortie)], stdin=subprocess.PIPE)
    parle, rebond = 0.0, 0.0
    for k in range(n):
        e = energie[k] if k < len(energie) else 0
        parle += (min(1.0, e) - parle) * 0.08          # enveloppe très lissée : pas de tremblote
        rebond = 1.0 if k and geste[k] != geste[k - 1] else rebond * 0.82
        im = composer(fl, Tp[k], Ty[k], Tb[k], k / FPS, parle, math.sin(rebond * math.pi / 2) * rebond)
        p.stdin.write(im.tobytes())
    p.stdin.close(); p.wait(); wav.unlink()
    print("→", sortie, f"({n / FPS:.1f} s)")
    return minutage(texte, phon)

if __name__ == "__main__":
    a = sys.argv[1:]
    nv = a[a.index("--voix") + 1] if "--voix" in a else "tom"
    if len(a) >= 2 and a[0] == "preparer": preparer(a[1])
    elif len(a) >= 3 and a[0] == "voix": print(len(voix(pathlib.Path(a[1]).read_text(), a[2], nv)), "phonèmes")
    elif len(a) >= 3 and a[0] == "anim": anim(a[1], a[2], nv)
    else: sys.exit(__doc__)
