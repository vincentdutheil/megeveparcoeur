#!/usr/bin/env python3
"""Visuel « prévisions de neige » pour Instagram (format des classements de stations).
Usage : python3 tools/post_neige.py FICHIER.json [--audio musique.mp3]
FICHIER.json :
 {"date":"AAAA-MM-JJ", "periode":"du 22 au 28 novembre",
  "items":[["Megève", 42, 4], ...]   ([station, cm prévus sur 7 jours, cm de neige au sol aujourd'hui]),
  "photo":"photos/xxx.jpg" (une photo de Vincent, jamais une photo d'abonné),
  "source":"Prévisions Open-Meteo · cumul sur 7 jours · vers 1 500 m",
  "apercu": true (facultatif : bandeau « aperçu, chiffres d'exemple »)}
Sorties dans instagram/ :
  neige-DATE.jpg (1080x1350, publication) · neige-DATE-story.jpg (1080x1920)
  neige-DATE-reel.mp4 (1080x1920, ~12 s : les stations apparaissent une à une ;
  avec --audio, la musique est ajoutée, sinon la vidéo est muette)."""
import json, sys, pathlib, html, tempfile, subprocess, shutil
from playwright.sync_api import sync_playwright
from PIL import Image

R = pathlib.Path(__file__).resolve().parent.parent
HOME = {"Megève", "Combloux", "Demi-Quartier", "Praz-sur-Arly"}


def page(c, H, shown=None):
    e = lambda s: html.escape(str(s))
    items = sorted(c["items"], key=lambda x: -x[1])[:12]
    n = len(items) if shown is None else shown
    story = H == 1920
    rows = ""
    for i, it in enumerate(items):
        name, cm, sol = it[0], it[1], (it[2] if len(it) > 2 else None)
        cls = "row home" if name in HOME else "row"
        vis = "" if i >= len(items) - n else " style=\"visibility:hidden\""
        sol_s = f'<i>{round(sol)} cm</i>' if sol is not None else '<i>—</i>'
        rows += f'<div class="{cls}"{vis}><span class="nm"><span class="n">{i+1}.</span> {e(name)}</span>{sol_s}<b>+{round(cm)} cm</b></div>'
    photo = (R / c["photo"]).resolve().as_uri()
    ap = '<div class="ap">APERÇU · chiffres d\'exemple</div>' if c.get("apercu") else ""
    top = 150 if story else 70
    return f"""<!DOCTYPE html><meta charset=utf-8><style>
*{{box-sizing:border-box;margin:0}}
body{{width:1080px;height:{H}px;overflow:hidden;font-family:Inter,"DejaVu Sans",sans-serif;position:relative;
background:linear-gradient(180deg,rgba(8,20,40,.55) 0%,rgba(8,20,40,.15) 35%,rgba(8,20,40,.15) 70%,rgba(8,20,40,.6) 100%),url({photo}) center/cover}}
.wrap{{position:absolute;inset:{top}px 0 0;display:flex;flex-direction:column;align-items:center}}
.brand{{display:flex;align-items:center;gap:16px;color:#fff;font-family:"DejaVu Serif",Georgia,serif;font-size:{34 if story else 30}px;text-shadow:0 2px 10px rgba(0,0,0,.5)}}
.brand img{{width:{84 if story else 72}px}}
h1{{margin-top:{30 if story else 22}px;background:#0c1a34;color:#fff;font-weight:800;text-align:center;line-height:1.12;
font-size:{58 if story else 50}px;padding:{22 if story else 18}px 40px;border-radius:22px;max-width:960px;box-shadow:0 14px 34px rgba(0,0,0,.35)}}
h1 small{{display:block;font-size:.5em;font-weight:700;color:#bcd3f2;margin-top:8px;letter-spacing:.02em}}
.list{{margin-top:{30 if story else 22}px;display:flex;flex-direction:column;gap:{14 if story else 9}px;width:960px}}
.row,.hd{{display:grid;grid-template-columns:1fr 190px 190px;align-items:center;gap:12px}}
.row{{background:#fff;color:#0c1a34;font-weight:800;font-size:{38 if story else 33}px;border-radius:16px;padding:{11 if story else 7}px 14px {11 if story else 7}px 24px;box-shadow:0 8px 20px rgba(0,0,0,.25)}}
.nm{{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}.row .n{{font-weight:700;opacity:.6}}
.row i,.row b{{text-align:center;border-radius:12px;padding:4px 0;font-style:normal}}
.row i{{background:#eef2f8;color:#55657e;font-weight:700}} .row b{{background:#1f4f9a;color:#fff}}
.row.home{{background:#c8323d;color:#fff}} .row.home i{{background:rgba(255,255,255,.2);color:#fff}} .row.home b{{background:#fff;color:#c8323d}}
.hd{{color:#fff;font-weight:800;font-size:{24 if story else 21}px;text-transform:uppercase;letter-spacing:.06em;text-shadow:0 2px 8px rgba(0,0,0,.6);padding:0 14px 0 24px}}
.hd span{{text-align:center}}
.foot{{position:absolute;left:40px;right:40px;bottom:{230 if story else 40}px;text-align:center;color:#fff;text-shadow:0 2px 8px rgba(0,0,0,.6)}}
.src{{font-size:{24 if story else 21}px;font-weight:600;opacity:.92}}
.url{{font-size:{34 if story else 30}px;font-weight:800;margin-top:8px}}
.ap{{position:absolute;top:{top-50 if story else 18}px;right:24px;background:#ffd84a;color:#000;font-weight:800;font-size:22px;padding:8px 16px;border-radius:999px}}
</style>{ap}<div class="wrap"><div class="brand"><img src="{(R/'img/logo-rond.png').as_uri()}">Megève par cœur</div>
<h1>❄️ La neige cette semaine<small>{e(c['periode'])} · Pays du Mont-Blanc &amp; Val d'Arly</small></h1>
<div class="list"><div class="hd"><span></span><span>Au sol</span><span>Prévu 7 j</span></div>{rows}</div></div>
<div class="foot"><div class="src">{e(c.get('source','Prévisions Open-Meteo · cumul sur 7 jours'))} · les prévisions évoluent</div><div class="url">megeveparcoeur.fr/meteo</div></div>"""


def shot(b, html_s, H, dst):
    pg = b.new_page(viewport={"width": 1080, "height": H})
    t = pathlib.Path(tempfile.mkstemp(suffix=".html")[1]); t.write_text(html_s, encoding="utf-8")
    pg.goto(t.as_uri()); pg.wait_for_timeout(400)
    over = pg.evaluate("(()=>{const l=document.querySelector('.list').getBoundingClientRect(),f=document.querySelector('.foot').getBoundingClientRect();return l.bottom>f.top-10})()")
    pg.screenshot(path=str(dst)); pg.close(); t.unlink()
    return over


def main():
    c = json.load(open(sys.argv[1], encoding="utf-8")); day = c["date"]
    audio = sys.argv[sys.argv.index("--audio") + 1] if "--audio" in sys.argv else None
    out = R / "instagram"; out.mkdir(exist_ok=True)
    n = min(12, len(c["items"]))
    tmp = pathlib.Path(tempfile.mkdtemp())
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/usr/bin/google-chrome")
        for H, suf in ((1350, ""), (1920, "-story")):
            png = tmp / f"x{suf}.png"
            over = shot(b, page(c, H), H, png)
            dst = out / f"neige-{day}{suf}.jpg"; Image.open(png).convert("RGB").save(dst, quality=90, optimize=True)
            print(dst, "ATTENTION : la liste touche le bas" if over else "ok")
        # Reel : 0 à n stations, de la dernière à la première (suspense), puis pause
        frames = []
        for k in range(n + 1):
            f = tmp / f"f{k:02d}.png"; shot(b, page(c, 1920, shown=k), 1920, f); frames.append(f)
        b.close()
    lst = tmp / "l.txt"
    lst.write_text("".join(f"file '{f}'\nduration {1.4 if k == 0 else (0.7 if k < n else 5)}\n" for k, f in enumerate(frames)) + f"file '{frames[-1]}'\n")
    mp4 = out / f"neige-{day}-reel.mp4"
    total = 1.4 + 0.7 * (n - 1) + 5
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst)]
    if audio:
        cmd += ["-i", audio, "-map", "0:v", "-map", "1:a", "-af", f"afade=t=out:st={total-1.5}:d=1.5", "-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += ["-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-movflags", "+faststart", "-t", f"{total:.1f}", str(mp4)]
    subprocess.run(cmd, check=True)
    shutil.rmtree(tmp)
    print(mp4, "avec musique" if audio else "muette (ajoute --audio pour la musique)")


if __name__ == "__main__":
    main()
