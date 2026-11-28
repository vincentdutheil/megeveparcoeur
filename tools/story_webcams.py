#!/usr/bin/env python3
"""Story Instagram quotidienne « Ce matin à Megève » : 3 webcams + météo du jour.
Usage : python3 tools/story_webcams.py AAAA-MM-JJ [--meteo FICHIER.json] [--cams DOSSIER] [--apres HH:MM] [--reel [--audio MP3]]
  --apres HH:MM : n'utiliser que des images prises à HH:MM ou après (attend jusqu'à 12 min si besoin).
  - Météo en haut, puis les webcams (dans cet ordre) : village de Megève, sommet de Rochebrune, sommet de Combloux,
    lues via https://www.megeveparcoeur.fr/api/webcam?c=… (dernière image Skaping + heure de prise de vue).
    --cams DOSSIER : utiliser DOSSIER/combloux.jpg, rochebrune.jpg, village.jpg (tests, ou images déjà téléchargées).
  - Météo : Open-Meteo, Megève uniquement. Village (1 113 m) : temps et température du moment, min/max du jour,
    prévisions des 3 jours suivants. Neige au sol : au sommet du domaine de Megève (~2 000 m), estimation du modèle.
    --meteo FICHIER.json : réponse brute d'Open-Meteo (tableau de 2 lieux) déjà téléchargée (ex. via WebFetch).
Sortie : instagram/webcams-AAAA-MM-JJ-story.jpg (1080x1920, fond bleu nuit uni), puis un résumé
et une ligne « TAGS {...} » : centre vertical (0-1) de chaque webcam, pour placer les identifications.
Option --reel [--audio MUSIQUE.mp3] : crée aussi instagram/reel-webcams-AAAA-MM-JJ.mp4 (1080x1920, 20 s, 30 i/s :
météo en haut, dessous les 3 webcams ensemble sur tout l'espace (village, Rochebrune, Combloux), chacune parcourue
 en entier par un panoramique régulier,
 et pour finir « Belle journée à tous ! »)
et instagram/reel-webcams-AAAA-MM-JJ-cover.jpg. Avec --audio, la musique est la bande-son (fondu à la fin).
Affiche « ATTENTION » si une webcam manque, est trop sombre (nuit) ou si l'image est trop ancienne."""
import json, sys, pathlib, html, tempfile, datetime as dt, urllib.request, subprocess
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
from PIL import Image, ImageStat, ImageDraw, ImageFont

R = pathlib.Path(__file__).resolve().parent.parent
CAMS = [("village", "Village de Megève", "Megève", "#1f3d7a"),
        ("rochebrune", "Sommet de Rochebrune", "Megève", "#1f3d7a"),
        ("combloux", "Sommet de Combloux", "Combloux", "#2f5a44")]
UA = {"User-Agent": "Mozilla/5.0 (compatible; megeveparcoeur.fr story)"}
METEO_URL = ("https://api.open-meteo.com/v1/forecast?latitude=45.857,45.826&longitude=6.617,6.618&elevation=1113,2000"
             "&current=temperature_2m,weather_code,snow_depth"
             "&daily=weather_code,temperature_2m_max,temperature_2m_min,snowfall_sum,precipitation_probability_max"
             "&forecast_days=4&timezone=Europe%2FParis")
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
JC = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
WMO = {0: ("☀️", "Grand soleil"), 1: ("🌤️", "Plutôt ensoleillé"), 2: ("⛅", "Éclaircies"), 3: ("☁️", "Couvert"),
       45: ("🌫️", "Brouillard"), 48: ("🌫️", "Brouillard givrant"), 51: ("🌦️", "Bruine légère"), 53: ("🌦️", "Bruine"),
       55: ("🌧️", "Bruine forte"), 56: ("🌧️", "Bruine verglaçante"), 57: ("🌧️", "Bruine verglaçante"),
       61: ("🌧️", "Pluie faible"), 63: ("🌧️", "Pluie"), 65: ("🌧️", "Forte pluie"), 66: ("🌧️", "Pluie verglaçante"),
       67: ("🌧️", "Pluie verglaçante"), 71: ("🌨️", "Neige faible"), 73: ("🌨️", "Neige"), 75: ("❄️", "Forte neige"),
       77: ("🌨️", "Grains de neige"), 80: ("🌦️", "Averses"), 81: ("🌧️", "Averses"), 82: ("⛈️", "Fortes averses"),
       85: ("🌨️", "Averses de neige"), 86: ("❄️", "Fortes averses de neige"), 95: ("⛈️", "Orages"),
       96: ("⛈️", "Orages et grêle"), 99: ("⛈️", "Orages et grêle")}


def meteo_json():
    """Météo Open-Meteo, d'abord via le relais du site (/api/meteo, interrogé depuis Vercel),
    puis en direct. Le direct échoue souvent dans le cloud : quota quotidien de l'IP partagée épuisé (429)."""
    import time
    q = METEO_URL.split("?", 1)[1]
    erreurs = []
    for essai in range(3):
        for url in ("https://www.megeveparcoeur.fr/api/meteo?" + q, METEO_URL):
            try:
                m = json.loads(get(url)[0])
                if isinstance(m, list) and len(m) >= 2:
                    return m
                erreurs.append(f"{url[:40]}… : réponse inattendue {str(m)[:120]}")
            except Exception as e:
                erreurs.append(f"{url[:40]}… : {e}")
        time.sleep(15)
    sys.exit("ATTENTION : météo indisponible, pas de reel. " + " | ".join(erreurs[-2:]))


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
        return r.read(), r.headers


def deg(v):
    n = round(v)
    return ("−" if n < 0 else "") + f"{abs(n)}°"


def cams(folder, tmp, apres=None):
    """apres = "HH:MM" : attendre (jusqu'à 12 min) que chaque webcam ait une image prise à cette heure ou après."""
    import time
    out = []
    for cid, title, vil, col in CAMS:
        dst = tmp / f"{cid}.jpg"
        shot = None
        try:
            if folder:
                dst.write_bytes((pathlib.Path(folder) / f"{cid}.jpg").read_bytes())
            else:
                for essai in range(13):
                    data, hd = get(f"https://www.megeveparcoeur.fr/api/webcam?c={cid}&t={int(time.time())}")
                    shot = hd.get("X-Shot")
                    if not apres or not shot or shot[11:16] >= apres or essai == 12:
                        break
                    time.sleep(60)
                if apres and shot and shot[11:16] < apres:
                    print(f"ATTENTION : {title} : pas encore d'image de {apres} (dernière : {shot[11:16]})")
                dst.write_bytes(data)
            im = Image.open(dst).convert("L"); lum = ImageStat.Stat(im).mean[0]
        except Exception as e:
            print(f"ATTENTION : webcam {title} indisponible ({e})"); out.append(None); continue
        out.append({"id": cid, "t": title, "v": vil, "c": col, "src": dst.as_uri(), "shot": shot, "lum": lum})
    return out


def page(date, cs, m):
    e = lambda s: html.escape(str(s))
    vil, top = m[0], m[1]
    d = vil["daily"]
    code = vil["current"]["weather_code"]; emo, lab = WMO.get(code, ("🌡️", "—"))
    sol = round((top["current"].get("snow_depth") or 0) * 100)
    neige0 = d["snowfall_sum"][0] or 0
    blocks = ""
    for c in cs:
        if not c:
            continue
        hh = f'<span class="h">{e(c["shot"][11:16].replace(":", "h"))}</span>' if c.get("shot") else ""
        blocks += (f'<div class="cam"><img src="{c["src"]}"><span class="lb"><b style="background:{c["c"]}">{e(c["v"])}</b>'
                   f'{e(c["t"])}</span>{hh}</div>')
    prev = ""
    for k in range(1, 4):
        dd = dt.date.fromisoformat(d["time"][k]); pe, pl = WMO.get(d["weather_code"][k], ("🌡️", "—"))
        sn = d["snowfall_sum"][k] or 0
        sn_s = f'<i>❄️ +{round(sn)} cm</i>' if sn >= 0.5 else '<i class="z">pas de neige</i>'
        prev += (f'<div class="d"><span class="j">{JC[dd.weekday()]} {dd.day}</span><span class="pe">{pe}</span>'
                 f'<span class="t">{deg(d["temperature_2m_min"][k])} / {deg(d["temperature_2m_max"][k])}</span>{sn_s}</div>')
    jour = f"{JOURS[date.weekday()].capitalize()} {date.day} {MOIS[date.month-1]}"
    n0 = f' · ❄️ +{round(neige0)} cm' if neige0 >= 0.5 else ""
    html_s = f"""<!DOCTYPE html><meta charset=utf-8><style>
*{{box-sizing:border-box;margin:0}}
body{{width:1080px;height:1920px;overflow:hidden;background:#0a1424;color:#fff;font-family:Inter,"DejaVu Sans",sans-serif;position:relative}}
.brand{{position:absolute;top:120px;left:40px;right:40px;display:flex;align-items:center;gap:18px;font-family:"DejaVu Serif",Georgia,serif;font-size:34px}}
.brand img{{width:84px;height:84px}}.brand .dt{{margin-left:auto;font-family:Inter,"DejaVu Sans",sans-serif;font-weight:800;font-size:28px;color:#bcd3f2}}
h1{{position:absolute;top:228px;left:40px;right:40px;font-size:62px;font-weight:800;line-height:1}}
h1 small{{font-size:30px;font-weight:700;color:#ff8a97;margin-left:14px;letter-spacing:.02em}}
.cams{{position:absolute;top:var(--ct);left:40px;right:40px;display:grid;gap:16px}}
.cam{{position:relative;height:280px;border-radius:26px;overflow:hidden;background:#16243d;box-shadow:0 14px 30px rgba(0,0,0,.4)}}
.cam img{{width:100%;height:100%;object-fit:cover;display:block}}
.lb{{position:absolute;left:16px;bottom:16px;display:flex;align-items:center;gap:10px;background:rgba(10,20,36,.82);
padding:8px 18px 8px 8px;border-radius:999px;font-weight:800;font-size:28px}}
.lb b{{font-size:20px;text-transform:uppercase;letter-spacing:.05em;padding:6px 12px;border-radius:999px}}
.h{{position:absolute;right:16px;top:16px;background:rgba(10,20,36,.82);font-weight:800;font-size:24px;padding:6px 14px;border-radius:999px}}
.met{{position:absolute;top:318px;left:40px;right:40px;background:#fff;color:#0c1a34;border-radius:28px;padding:26px 30px;box-shadow:0 14px 30px rgba(0,0,0,.4)}}
.now{{display:grid;grid-template-columns:auto 1fr auto;gap:22px;align-items:center}}
.big{{font-size:96px;line-height:1}}.lab{{font-size:36px;font-weight:800;line-height:1.1}}
.lab small{{display:block;font-size:26px;font-weight:700;color:#55657e;margin-top:6px}}
.tp{{font-size:84px;font-weight:800;color:#1f4f9a;line-height:1}}
.sol{{margin-top:20px;display:flex;justify-content:space-between;align-items:center;background:#eef2f8;border-radius:18px;padding:14px 22px;font-size:27px;font-weight:700;color:#55657e}}
.sol b{{font-size:44px;color:#0c1a34}}
.prev{{margin-top:18px;display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}
.d{{background:#0c1a34;color:#fff;border-radius:18px;padding:12px 8px;text-align:center;display:grid;gap:4px}}
.j{{font-weight:800;font-size:24px;text-transform:uppercase;color:#bcd3f2}}.pe{{font-size:46px;line-height:1.1}}
.t{{font-weight:800;font-size:28px}}.d i{{font-style:normal;font-weight:800;font-size:22px;color:#bcd3f2}}.d i.z{{opacity:.6;font-weight:700}}
.ft{{position:absolute;top:1702px;left:40px;right:40px;text-align:center}}
.ft .s{{font-size:21px;font-weight:600;color:#bcd3f2}}.ft .u{{font-size:32px;font-weight:800;margin-top:6px}}
</style>
<div class="brand"><img src="{(R/'img/logo-rond.png').as_uri()}">Megève par cœur<span class="dt">{e(jour)}</span></div>
<h1>Ce matin à Megève<small>📍 en direct</small></h1>
<div class="cams">{blocks}</div>
<div class="met"><div class="now"><span class="big">{emo}</span>
<span class="lab">{e(lab)}<small>Au village · aujourd'hui {deg(d["temperature_2m_min"][0])} / {deg(d["temperature_2m_max"][0])}{n0}</small></span>
<span class="tp">{deg(vil["current"]["temperature_2m"])}</span></div>
<div class="sol"><span>❄️ Neige au sol au sommet<br><small>Domaine de Megève · ~2 000 m · estimation</small></span><b>{sol} cm</b></div>
<div class="prev">{prev}</div></div>
<div class="ft"><div class="s">Webcams Skaping · prévisions Open-Meteo pour Megève</div><div class="u">megeveparcoeur.fr</div></div>"""
    resume = {"temps": lab, "temperature": round(vil["current"]["temperature_2m"]),
              "min": round(d["temperature_2m_min"][0]), "max": round(d["temperature_2m_max"][0]),
              "neige_aujourdhui_cm": round(neige0), "neige_sol_sommet_cm": sol,
              "previsions": [{"date": d["time"][k], "temps": WMO.get(d["weather_code"][k], ("", "—"))[1],
                              "min": round(d["temperature_2m_min"][k]), "max": round(d["temperature_2m_max"][k]),
                              "neige_cm": round(d["snowfall_sum"][k] or 0)} for k in range(1, 4)]}
    return html_s, resume


# ------------------------------------------------------------------ reel
FPS, DUREE, END = 30, 20.0, 2.6                 # i/s, durée totale du reel, durée de la carte de fin (s)
ZONE = (40, 796, 1040, 1880)                    # zone des 3 webcams : tout l'espace sous la météo
GAP = 18
BH = (ZONE[3] - ZONE[1] - 2 * GAP) // 3         # hauteur d'une bande de webcam


def fnt(size, w="ExtraBold"):
    for f in (f"/usr/share/fonts/opentype/inter/Inter-{w}.otf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except Exception:
            pass
    return ImageFont.load_default()


def chip(d, x, y, txt, f, bg=(10, 20, 36, 210), pad=(16, 8), anchor="lt"):
    l, t, r, b = d.textbbox((0, 0), txt, font=f)
    w, h = r - l + 2 * pad[0], b - t + 2 * pad[1]
    if anchor == "rt":
        x -= w
    if anchor == "lb":
        y -= h
    d.rounded_rectangle((x, y, x + w, y + h), radius=h // 2, fill=bg)
    d.text((x + pad[0] - l, y + pad[1] - t), txt, font=f, fill=(255, 255, 255))
    return x + w


def cam_layer(c, bw, bh):
    """Webcam agrandie pour remplir sa bande, avec de la marge pour le panoramique."""
    im = Image.open(c["src"].replace("file://", "")).convert("RGB")
    sc = max(bh / im.height, bw * 1.6 / im.width)      # panorama entier en hauteur ; zoom si l'image est trop étroite
    im = im.resize((round(im.width * sc), round(im.height * sc)), Image.LANCZOS)
    return im, im.width - bw, im.height - bh


def overlay(c, bw, bh):
    ov = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    col = tuple(int(c["c"][i:i + 2], 16) for i in (1, 3, 5)) + (255,)
    y = bh - 14
    x = chip(d, 14, y, c["v"].upper(), fnt(19), bg=col, pad=(14, 11), anchor="lb")
    chip(d, x + 8, y, c["t"], fnt(28), anchor="lb")
    if c.get("shot"):
        chip(d, bw - 14, 14, c["shot"][11:16].replace(":", "h"), fnt(24), anchor="rt")
    return ov


def end_card(bw, bh):
    """Carte de fin posée sur les webcams : « Belle journée à tous ! »."""
    ov = Image.new("RGBA", (bw, bh), (10, 20, 36, 215))
    d = ImageDraw.Draw(ov)
    for txt, f, dy in (("Belle journée", fnt(96), -105), ("à tous !", fnt(96), 5), ("megeveparcoeur.fr", fnt(42, "Bold"), 125)):
        l, t, r, b = d.textbbox((0, 0), txt, font=f)
        d.text(((bw - (r - l)) / 2 - l, bh / 2 + dy - t), txt, font=f, fill=(255, 255, 255))
    return ov


def rmask(w, h, r=24):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), radius=r, fill=255)
    return m


def reel(date, ok, m, base_png, audio, tmp):
    """Les webcams ensemble, l'une sous l'autre, chacune avec un lent panoramique ; puis « Belle journée à tous ! »."""
    base = Image.open(base_png).convert("RGB")
    bw, zh = ZONE[2] - ZONE[0], ZONE[3] - ZONE[1]
    n = len(ok)
    bh = (zh - (n - 1) * GAP) // n
    layers = [(cam_layer(c, bw, bh), overlay(c, bw, bh)) for c in ok]
    bmask, zmask = rmask(bw, bh), rmask(bw, zh, 28)
    fin = end_card(bw, zh)
    total = DUREE
    mp4 = R / "instagram" / f"reel-webcams-{date}.mp4"
    cover = R / "instagram" / f"reel-webcams-{date}-cover.jpg"
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", str(FPS), "-i", "-"]
    if audio:
        cmd += ["-i", str(audio), "-map", "0:v", "-map", "1:a", "-af", f"afade=t=in:d=0.4,afade=t=out:st={total - 1.6:.2f}:d=1.6",
                "-c:a", "aac", "-b:a", "192k"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            "-t", f"{total:.2f}", str(mp4)]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    nf = round(total * FPS)
    for fi in range(nf):
        t = fi / FPS
        k = min(t / total, 1)                                  # défilement régulier sur toute la durée
        fr = base.copy()
        for j, ((im, mx, my), ov) in enumerate(layers):
            x, y = round(mx * k), round(my * 0.5)
            band = im.crop((x, y, x + bw, y + bh)).convert("RGBA")
            band.alpha_composite(ov)
            fr.paste(band.convert("RGB"), (ZONE[0], ZONE[1] + j * (bh + GAP)), bmask)
        if t > total - END:                                    # « Belle journée à tous ! »
            a_ = min((t - (total - END)) / 0.5, 1)
            z = fr.crop((ZONE[0], ZONE[1], ZONE[0] + bw, ZONE[1] + zh)).convert("RGBA")
            z2 = z.copy(); z2.alpha_composite(fin)
            fr.paste(Image.blend(z, z2, a_).convert("RGB"), (ZONE[0], ZONE[1]), zmask)
        if t < 0.4:
            fr = Image.blend(Image.new("RGB", fr.size, (10, 20, 36)), fr, t / 0.4)
        if fi == round(1.0 * FPS):
            fr.save(cover, quality=90)
        pr.stdin.write(fr.tobytes())
    pr.stdin.close()
    if pr.wait() != 0:
        sys.exit("ATTENTION : ffmpeg a échoué")
    return mp4, cover, total

def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    date = dt.date.fromisoformat(a[0])
    opt = lambda k: a[a.index(k) + 1] if k in a else None
    mf = opt("--meteo")
    m = json.loads(pathlib.Path(mf).read_text()) if mf else meteo_json()
    if not isinstance(m, list) or len(m) < 2:
        sys.exit("ATTENTION : réponse Open-Meteo inattendue (il faut les 2 lieux : village puis sommet)")
    tmp = pathlib.Path(tempfile.mkdtemp())
    cs = cams(opt("--cams"), tmp, opt("--apres"))
    ok = [c for c in cs if c]
    if len(ok) < 2:
        sys.exit("ATTENTION : moins de 2 webcams disponibles, pas de story")
    now = dt.datetime.now(ZoneInfo("Europe/Paris")).replace(tzinfo=None)
    for c in ok:
        if c["lum"] < 45:
            print(f"ATTENTION : webcam {c['t']} très sombre (luminosité {c['lum']:.0f}/255, nuit ?)")
        if c.get("shot"):
            age = now - dt.datetime.fromisoformat(c["shot"])
            if age > dt.timedelta(hours=3):
                print(f"ATTENTION : image {c['t']} ancienne ({c['shot']})")
    page_s, resume = page(date, cs, m)
    dst = R / "instagram" / f"webcams-{date}-story.jpg"
    f = tmp / "p.html"; f.write_text(page_s, encoding="utf-8")
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": 1080, "height": 1920})
        pg.goto(f.as_uri()); pg.wait_for_timeout(600)
        ct = round(pg.evaluate("document.querySelector('.met').getBoundingClientRect().bottom")) + 22
        pg.evaluate(f"document.body.style.setProperty('--ct', '{ct}px')"); pg.wait_for_timeout(200)
        bottom = pg.evaluate("document.querySelector('.cams').getBoundingClientRect().bottom")
        png = tmp / "p.png"; pg.screenshot(path=str(png)); b.close()
    Image.open(png).convert("RGB").save(dst, quality=90)
    if bottom > 1690:  # bas de la dernière webcam
        print("ATTENTION : les webcams débordent sur le bas")
    # centre vertical de chaque webcam affichée (pour les identifications)
    tags, y = {}, ct
    for c in ok:
        tags[c["id"]] = round((y + 140) / 1920, 3); y += 296
    print(dst)
    if "--reel" in a:
        page_r, _ = page(date, [], m)
        fr = tmp / "r.html"; fr.write_text(page_r, encoding="utf-8")
        with sync_playwright() as p:
            b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
            pg = b.new_page(viewport={"width": 1080, "height": 1920})
            pg.goto(fr.as_uri()); pg.wait_for_timeout(600)
            pg.evaluate("document.querySelector('.ft').style.display='none'")
            rp = tmp / "r.png"; pg.screenshot(path=str(rp)); b.close()
        mp4, cover, total = reel(date, ok, m, rp, opt("--audio"), tmp)
        print(mp4, f"{total:.1f} s", "avec musique" if opt("--audio") else "muette")
        print(cover)
    print("RESUME", json.dumps(resume, ensure_ascii=False))
    print("WEBCAMS", json.dumps({c["id"]: {"heure": c.get("shot"), "luminosite": round(c["lum"])} for c in ok}, ensure_ascii=False))
    print("TAGS", json.dumps(tags))


if __name__ == "__main__":
    main()
