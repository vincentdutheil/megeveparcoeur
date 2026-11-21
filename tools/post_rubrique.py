#!/usr/bin/env python3
"""Visuels de la publication « rubrique » du samedi (Instagram megeveparcoeur).
Usage : python3 tools/post_rubrique.py FICHIER.json
FICHIER.json :
 {"date":"AAAA-MM-JJ", "kicker":"La balade du week-end", "emoji":"🥾", "title":"Les crêtes du Mont Joly",
  "lines":["⏱ 3h · ↗ 800 m", "Départ : …", "…"]  (3 à 5 lignes courtes),
  "photo":"chemin/vers/photo.jpg" (facultatif : photo en haut de la publication),
  "cta":"Tous les détails sur megeveparcoeur.fr", "theme":"nuit"|"neige"|"sapin"|"chalet" (facultatif)}
Sorties : instagram/rubrique-AAAA-MM-JJ.jpg (1080x1350) et instagram/rubrique-AAAA-MM-JJ-story.jpg (1080x1920)."""
import json, sys, pathlib, html, tempfile
from playwright.sync_api import sync_playwright
from PIL import Image

R = pathlib.Path(__file__).resolve().parent.parent
THEMES = {"nuit": ("#0a1424", "#16345a", "#ff8a97"), "neige": ("#1d3d63", "#5f86b5", "#ffd98a"),
          "sapin": ("#10241b", "#2f5444", "#f3c27a"), "chalet": ("#1d1511", "#4a3324", "#f3c27a")}

def page(c, H):
    bg1, bg2, acc = THEMES.get(c.get("theme"), THEMES["nuit"])
    e = lambda s: html.escape(str(s))
    photo = c.get("photo")
    ph = f'<div class="ph" style="background-image:url({pathlib.Path(photo).resolve().as_uri()})"></div>' if photo else ""
    lines = "".join(f"<li>{e(l)}</li>" for l in c.get("lines", [])[:5])
    story = H == 1920
    return f"""<!DOCTYPE html><meta charset=utf-8><style>
*{{box-sizing:border-box;margin:0}}body{{width:1080px;height:{H}px;overflow:hidden;font-family:Inter,"DejaVu Sans",sans-serif;color:#fff;
background:radial-gradient(70% 50% at 80% 10%,rgba(255,200,130,.18),transparent 60%),linear-gradient(170deg,{bg1},{bg2});position:relative;display:flex;flex-direction:column}}
.main{{flex:1;display:flex;flex-direction:column;justify-content:center;padding-bottom:{420 if story else 190}px}}
.mt{{position:absolute;left:0;right:0;bottom:0;width:100%;height:{330 if story else 230}px}}
.top{{display:flex;align-items:center;gap:26px;padding:{90 if story else 60}px 70px 0}}.top img{{width:{130 if story else 110}px;height:auto}}
.k{{font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:{acc};font-size:{30 if story else 26}px}}
.brand{{font-family:"DejaVu Serif",Georgia,serif;font-size:{34 if story else 30}px;opacity:.9;margin-top:4px}}
.ph{{margin:{40 if story else 34}px 70px 0;height:{620 if story else 470}px;border-radius:34px;background:center/cover no-repeat;box-shadow:0 20px 50px rgba(0,0,0,.45)}}
.em{{font-size:{170 if story else 130}px;line-height:1;margin:0 70px}}
h1{{font-family:"DejaVu Serif",Georgia,serif;font-weight:400;font-size:{88 if story else 72}px;line-height:1.05;margin:{24 if photo else 18}px 70px 0}}
ul{{list-style:none;padding:0;margin:{34 if story else 26}px 70px 0;display:grid;gap:{18 if story else 14}px}}
li{{font-size:{38 if story else 33}px;line-height:1.3;background:rgba(255,255,255,.09);border:1px solid rgba(255,255,255,.18);border-radius:22px;padding:{18 if story else 14}px 26px}}
.cta{{position:absolute;left:70px;right:70px;bottom:{260 if story else 60}px;text-align:center;font-weight:800;font-size:{38 if story else 32}px;color:#fff;
background:#c8323d;border-radius:999px;padding:{24 if story else 20}px 20px;box-shadow:0 14px 30px rgba(200,50,61,.4)}}
</style><div class="top"><img src="{(R/'img/logo-rond.png').as_uri()}"><div><div class="k">{e(c.get('kicker',''))}</div><div class="brand">Megève par cœur</div></div></div>
<div class="main">{ph or f'<div class="em">{e(c.get("emoji",""))}</div>'}<h1>{(e(c.get('emoji',''))+' ') if photo else ''}{e(c['title'])}</h1><ul>{lines}</ul></div>
<svg class="mt" viewBox="0 0 1080 300" preserveAspectRatio="none"><path fill="rgba(255,255,255,.08)" d="M0 300V170L140 90 250 150 400 40 520 130 650 70 800 160 930 80 1080 140V300z"/><path fill="rgba(0,0,0,.22)" d="M0 300V230L160 170 300 215 470 150 620 220 780 175 940 225 1080 190V300z"/></svg>
<div class="cta">{e(c.get('cta','Tous les détails sur megeveparcoeur.fr'))}</div>"""

def main():
    c = json.load(open(sys.argv[1], encoding="utf-8")); day = c["date"]
    out = R / "instagram"; out.mkdir(exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/usr/bin/google-chrome")
        for H, suf in ((1350, ""), (1920, "-story")):
            pg = b.new_page(viewport={"width": 1080, "height": H})
            t = pathlib.Path(tempfile.mkstemp(suffix=".html")[1]); t.write_text(page(c, H), encoding="utf-8")
            pg.goto(t.as_uri()); pg.wait_for_timeout(600)
            over = pg.evaluate("(()=>{const u=document.querySelector('ul').getBoundingClientRect(),c=document.querySelector('.cta').getBoundingClientRect();return u.bottom>c.top-20})()")
            png = out / f"_tmp{suf}.png"; pg.screenshot(path=str(png)); t.unlink()
            dst = out / f"rubrique-{day}{suf}.jpg"; Image.open(png).convert("RGB").save(dst, quality=88, optimize=True); png.unlink()
            print(dst, "ATTENTION : le texte touche le bouton, raccourcis les lignes" if over else "ok")
        b.close()

if __name__ == "__main__": main()
