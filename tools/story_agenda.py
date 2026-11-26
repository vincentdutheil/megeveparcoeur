#!/usr/bin/env python3
"""Génère les visuels Instagram hebdo de l'agenda à partir de data/agenda.json.
Usage : python3 tools/story_agenda.py AAAA-MM-JJ  (date du jeudi de publication)
Sorties :
  stories/agenda-AAAA-MM-JJ.png       story 1080x1920 (6 événements max)
  stories/agenda-AAAA-MM-JJ-post.png  publication 1080x1350 (5 événements max)
puis la liste des événements retenus (date | lieu | titre | horaire | lien)."""
import json, sys, datetime as dt, pathlib, html
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
MC = ["janv.","févr.","mars","avr.","mai","juin","juil.","août","sept.","oct.","nov.","déc."]
JOURS = ["lun.","mar.","mer.","jeu.","ven.","sam.","dim."]
COL = {"Megève":"#1f3d7a","Demi-Quartier":"#5b4a86","Combloux":"#2f5d50","Praz-sur-Arly":"#8a5a14"}

def pick(start):
    end = start + dt.timedelta(days=6)
    out = []
    for e in json.load(open(ROOT/"data/agenda.json", encoding="utf-8")):
        d = dt.date.fromisoformat(e["d"]); d2 = dt.date.fromisoformat(e.get("d2", e["d"]))
        if d2 < start or d > end: continue
        if (d2 - d).days > 14 and not (start <= d <= end): continue  # saisons, expos : seulement la semaine où elles commencent
        out.append((max(d, start), d, d2, e))
    out.sort(key=lambda x: (x[0], x[3]["t"]))
    return out[:6], end

def label(d, d2, start):
    if d == d2: return f"{JOURS[d.weekday()]} {d.day} {MC[d.month-1]}"
    if d < start: return f"jusqu'au {d2.day} {MC[d2.month-1]}"
    if d.month == d2.month: return f"{d.day}–{d2.day} {MC[d2.month-1]}"
    return f"{d.day} {MC[d.month-1]} → {d2.day} {MC[d2.month-1]}"

def render(start, end, evs, total, kind):
    H = 1920 if kind == "story" else 1350
    top, lst, bottom = (150, 470, 330) if kind == "story" else (70, 390, 60)
    rows = "".join(
        f'<div class="ev"><div class="d">{html.escape(label(d,d2,start))}{(" · "+html.escape(e["h"])) if e.get("h") else ""}</div>'
        f'<div class="t">{html.escape(e["t"])}</div><span class="p" style="background:{COL.get(e["lieu"],"#1f3d7a")}">{html.escape(e["lieu"])}</span></div>'
        for _, d, d2, e in evs)
    per = f"du {start.day} {MC[start.month-1]} au {end.day} {MC[end.month-1]}"
    if kind == "story":
        cta = "👇 L'agenda complet sur<br><b>www.megeveparcoeur.fr</b>"
    else:
        more = f"+ {total-len(evs)} autre{'s' if total-len(evs)>1 else ''} cette semaine · " if total > len(evs) else ""
        cta = f"{more}Tout l'agenda sur<br><b>megeveparcoeur.fr</b> · lien en bio"
    page = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0}}body{{width:1080px;height:{H}px;font-family:Inter,sans-serif;color:#fff;overflow:hidden;
background:linear-gradient(180deg,rgba(14,28,60,.78),rgba(14,28,60,.9)),url('{(ROOT/"videos/hero-poster.jpg").as_uri()}') center/cover}}
.serif{{font-family:"DejaVu Serif",Georgia,serif}}
.top{{position:absolute;top:{top}px;left:80px;right:80px;display:flex;gap:28px;align-items:center}}
.top img{{width:130px;height:130px}}.k{{font-weight:800;letter-spacing:{".05em" if kind=="story" else ".14em"};white-space:nowrap;text-transform:uppercase;color:#ff8a97;font-size:{46 if kind=="story" else 28}px}}
h1{{font-size:70px;line-height:1.05;margin-top:8px}}.loc{{font-size:26px;font-weight:700;color:#ff8a97;margin-top:6px}}
.per{{font-size:34px;opacity:.9;margin-top:8px}}
.list{{position:absolute;top:{lst}px;left:70px;right:70px;display:grid;gap:22px}}
.ev{{background:rgba(255,255,255,.96);color:#16213a;border-radius:28px;padding:24px 30px;position:relative}}
.d{{font-weight:800;color:#d6283c;font-size:28px;text-transform:uppercase;letter-spacing:.03em}}
.t{{font-size:38px;font-weight:700;line-height:1.15;margin-top:6px;padding-right:200px}}
.p{{position:absolute;right:26px;top:24px;color:#fff;font-size:22px;font-weight:800;text-transform:uppercase;padding:6px 14px;border-radius:999px}}
.cta{{position:absolute;bottom:{bottom}px;left:0;right:0;text-align:center;font-size:{56 if kind=="story" else 34}px;font-weight:800;line-height:1.25}}
.cta b{{color:#ff8a97}}
</style></head><body>
<div class="top"><img src="{(ROOT/"img/logo-rond.png").as_uri()}"><div><div class="k">L'agenda de la semaine</div>
<h1 class="serif">Megève &amp; alentours</h1><div class="loc">📍 Megève · Combloux · Demi-Quartier · Praz</div><div class="per">{per}</div></div></div>
<div class="list">{rows}</div>
<div class="cta">{cta}</div>
</body></html>"""
    out = ROOT/"stories"; out.mkdir(exist_ok=True)
    tmp = out/f"_tmp_{kind}.html"; tmp.write_text(page, encoding="utf-8")
    png = out/(f"agenda-{start.isoformat()}.png" if kind == "story" else f"agenda-{start.isoformat()}-post.png")
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/usr/bin/google-chrome")
        pg = b.new_page(viewport={"width":1080,"height":H}); pg.goto(tmp.as_uri()); pg.wait_for_timeout(600)
        lb = pg.evaluate("document.querySelector('.list').getBoundingClientRect().bottom")
        ct = pg.evaluate("document.querySelector('.cta').getBoundingClientRect().top")
        tb = pg.evaluate("document.querySelector('.top').getBoundingClientRect().bottom")
        lt = pg.evaluate("document.querySelector('.list').getBoundingClientRect().top")
        kw = pg.evaluate("document.querySelector('.k').scrollWidth - document.querySelector('.k').parentElement.clientWidth")
        pg.screenshot(path=str(png)); b.close()
    tmp.unlink()
    if lb > ct - 20: print(f"ATTENTION ({kind}) : la liste chevauche le bas de l'image")
    if tb > lt - 10: print(f"ATTENTION ({kind}) : l'en-tête chevauche la liste")
    if kw > 0: print(f"ATTENTION ({kind}) : « L'agenda de la semaine » déborde")
    print(png)

def render_fin(start):
    """Carte de fin du reel (1080x1920) : logo + « Bonne fin de semaine ! »."""
    page = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0}}body{{width:1080px;height:1920px;font-family:Inter,sans-serif;color:#fff;overflow:hidden;
background:linear-gradient(180deg,rgba(14,28,60,.78),rgba(14,28,60,.9)),url('{(ROOT/"videos/hero-poster.jpg").as_uri()}') center/cover;
display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center}}
img{{width:520px;height:520px}}h1{{font-family:"DejaVu Serif",Georgia,serif;font-size:96px;line-height:1.1;margin-top:70px}}
p{{font-size:52px;font-weight:800;color:#ff8a97;margin-top:50px}}
</style></head><body><img src="{(ROOT/"img/logo-rond.png").as_uri()}"><h1>Bonne fin<br>de semaine !</h1><p>www.megeveparcoeur.fr</p></body></html>"""
    out = ROOT/"stories"; tmp = out/"_tmp_fin.html"; tmp.write_text(page, encoding="utf-8")
    png = out/f"agenda-{start.isoformat()}-fin.png"
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/usr/bin/google-chrome")
        pg = b.new_page(viewport={"width":1080,"height":1920}); pg.goto(tmp.as_uri()); pg.wait_for_timeout(600)
        pg.screenshot(path=str(png)); b.close()
    tmp.unlink(); print(png)

def main():
    start = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.date.today()
    evs, end = pick(start)
    if not evs:
        print("AUCUN ÉVÉNEMENT"); return 1
    render(start, end, evs, len(evs), "story")
    render(start, end, evs[:5], len(evs), "post")
    render_fin(start)
    for _, d, d2, e in evs:
        print("-", label(d, d2, start), "|", e["lieu"], "|", e["t"], "|", e.get("h", ""), "|", e["u"])
    return 0

if __name__ == "__main__": sys.exit(main())
