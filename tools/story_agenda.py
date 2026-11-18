#!/usr/bin/env python3
"""Génère la story Instagram hebdo de l'agenda (1080x1920) à partir de data/agenda.json.
Usage : python3 tools/story_agenda.py AAAA-MM-JJ  (date du jeudi de publication)
Sortie : stories/agenda-AAAA-MM-JJ.png (+ affiche la liste retenue)."""
import json, sys, datetime as dt, pathlib, html
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
MC = ["janv.","févr.","mars","avr.","mai","juin","juil.","août","sept.","oct.","nov.","déc."]
JOURS = ["lun.","mar.","mer.","jeu.","ven.","sam.","dim."]

def pick(start):
    end = start + dt.timedelta(days=6)
    out = []
    for e in json.load(open(ROOT/"data/agenda.json", encoding="utf-8")):
        d = dt.date.fromisoformat(e["d"]); d2 = dt.date.fromisoformat(e.get("d2", e["d"]))
        if d2 < start or d > end: continue
        long_ = (d2 - d).days > 14
        if long_ and not (start <= d <= end): continue   # saisons, expos : seulement la semaine où elles commencent
        out.append((max(d, start), d, d2, e))
    out.sort(key=lambda x: (x[0], x[3]["t"]))
    return out[:6], end

def label(d, d2, start):
    if d == d2: return f"{JOURS[d.weekday()]} {d.day} {MC[d.month-1]}"
    if d < start: return f"jusqu'au {d2.day} {MC[d2.month-1]}"
    return f"{d.day}–{d2.day} {MC[d2.month-1]}" if d.month == d2.month else f"{d.day} {MC[d.month-1]} → {d2.day} {MC[d2.month-1]}"

def main():
    start = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.date.today()
    evs, end = pick(start)
    if not evs:
        print("AUCUN ÉVÉNEMENT"); return 1
    col = {"Megève":"#1f3d7a","Combloux":"#2f5d50","Praz-sur-Arly":"#8a5a14"}
    rows = "".join(
        f'<div class="ev"><div class="d">{html.escape(label(d,d2,start))}{(" · "+html.escape(e["h"])) if e.get("h") else ""}</div>'
        f'<div class="t">{html.escape(e["t"])}</div><span class="p" style="background:{col.get(e["lieu"],"#1f3d7a")}">{html.escape(e["lieu"])}</span></div>'
        for _, d, d2, e in evs)
    per = f"du {start.day} {MC[start.month-1]} au {end.day} {MC[end.month-1]}"
    page = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0}}body{{width:1080px;height:1920px;font-family:Inter,sans-serif;color:#fff;overflow:hidden;
background:linear-gradient(180deg,rgba(14,28,60,.78),rgba(14,28,60,.9)),url('{(ROOT/"videos/hero-poster.jpg").as_uri()}') center/cover}}
.serif{{font-family:"DejaVu Serif",Georgia,serif}}
.top{{position:absolute;top:150px;left:80px;right:80px;display:flex;gap:28px;align-items:center}}
.top img{{width:130px;height:130px}}.k{{font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:#ff8a97;font-size:28px}}
h1{{font-size:70px;line-height:1.05;margin-top:8px}}.per{{font-size:34px;opacity:.9;margin-top:10px}}
.list{{position:absolute;top:430px;left:70px;right:70px;display:grid;gap:22px}}
.ev{{background:rgba(255,255,255,.96);color:#16213a;border-radius:28px;padding:24px 30px;position:relative}}
.d{{font-weight:800;color:#d6283c;font-size:28px;text-transform:uppercase;letter-spacing:.03em}}
.t{{font-size:38px;font-weight:700;line-height:1.15;margin-top:6px;padding-right:200px}}
.p{{position:absolute;right:26px;top:24px;color:#fff;font-size:22px;font-weight:800;text-transform:uppercase;padding:6px 14px;border-radius:999px}}
.cta{{position:absolute;bottom:330px;left:0;right:0;text-align:center;font-size:40px;font-weight:700}}
.cta b{{color:#ff8a97}}
</style></head><body>
<div class="top"><img src="{(ROOT/"img/logo-rond.png").as_uri()}"><div><div class="k">L'agenda de la semaine</div>
<h1 class="serif">Megève &amp; alentours</h1><div class="per">{per}</div></div></div>
<div class="list">{rows}</div>
<div class="cta">👇 Tous les événements sur<br><b>megeveparcoeur.fr</b></div>
</body></html>"""
    out = ROOT/"stories"; out.mkdir(exist_ok=True)
    tmp = out/"_tmp.html"; tmp.write_text(page, encoding="utf-8")
    png = out/f"agenda-{start.isoformat()}.png"
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/usr/bin/google-chrome")
        pg = b.new_page(viewport={"width":1080,"height":1920}); pg.goto(tmp.as_uri()); pg.wait_for_timeout(600)
        h = pg.evaluate("document.querySelector('.list').getBoundingClientRect().bottom")
        pg.screenshot(path=str(png)); b.close()
    tmp.unlink()
    for _, d, d2, e in evs: print("-", label(d,d2,start), e["lieu"], e["t"])
    if h > 1560: print("ATTENTION : liste trop longue, retirer un événement")
    print(png)
    return 0

if __name__ == "__main__": sys.exit(main())
