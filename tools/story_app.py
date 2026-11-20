import pathlib
from playwright.sync_api import sync_playwright
R=pathlib.Path("/home/claude/mpc-repo"); u=lambda p:(R/p).as_uri()
CSS=f"""*{{box-sizing:border-box;margin:0}}body{{width:1080px;height:1920px;font-family:Poppins,Inter,sans-serif;color:#fff;overflow:hidden;
background:linear-gradient(180deg,rgba(14,28,60,.80),rgba(14,28,60,.93)),url('{u("videos/hero-poster.jpg")}') center/cover;position:relative}}
.serif{{font-family:Lora,"DejaVu Serif",serif}}.k{{font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:#ff8a97;font-size:30px}}
.top{{position:absolute;top:150px;left:80px;right:80px;display:flex;gap:28px;align-items:center}}.top img{{width:120px;height:120px}}
h1{{font-size:76px;line-height:1.05;margin-top:6px}}
.phone{{position:absolute;left:50%;transform:translateX(-50%);width:520px;border:14px solid #0b1430;border-radius:60px;overflow:hidden;box-shadow:0 30px 80px rgba(0,0,0,.5)}}
.phone img{{display:block;width:100%}}
.ben{{position:absolute;left:80px;right:80px;display:grid;gap:18px}}
.b{{background:rgba(255,255,255,.96);color:#16213a;border-radius:26px;padding:22px 28px;font-size:34px;font-weight:600;display:flex;gap:18px;align-items:center}}
.b span{{font-size:44px}}
.cta{{position:absolute;left:0;right:0;text-align:center;font-size:40px;font-weight:700}}.cta b{{color:#ff8a97}}
.card{{position:absolute;left:70px;right:70px;background:rgba(255,255,255,.96);color:#16213a;border-radius:32px;padding:30px 36px}}
.card h2{{font-size:40px;display:flex;gap:14px;align-items:center}}.card ol{{margin-top:14px;padding-left:0;list-style:none;display:grid;gap:14px}}
.card li{{font-size:33px;line-height:1.25;display:flex;gap:18px;align-items:flex-start}}
.n{{flex:none;width:52px;height:52px;border-radius:50%;background:#d6283c;color:#fff;font-weight:800;display:grid;place-items:center;font-size:30px}}
.note{{position:absolute;left:80px;right:80px;font-size:29px;line-height:1.3;opacity:.92;text-align:center}}
"""
TOP=lambda k,t:f'<div class="top"><img src="{u("img/logo-rond.png")}"><div><div class="k">{k}</div><h1 class="serif">{t}</h1></div></div>'
f1=f"""<style>{CSS}</style>{TOP("Nouveau 📲","Megève par cœur<br>a son appli")}
<div class="phone" style="top:470px;height:760px"><img src="{u("img/app/screen-agenda.png")}"></div>
<div class="ben" style="top:1290px">
<div class="b"><span>🔔</span>Le programme du week-end, chaque vendredi</div>
<div class="b"><span>❄️</span>Une alerte quand la neige arrive</div>
<div class="b"><span>⭐</span>Tes sorties enregistrées dans « Mes sorties »</div></div>
<div class="cta" style="bottom:110px">Gratuite · sans store · 10 secondes 👉</div>"""
f2=f"""<style>{CSS}</style>{TOP("Installe l'appli en 3 gestes","Mode d'emploi")}
<div class="card" style="top:430px"><h2>🍎 Sur iPhone</h2><ol>
<li><span class="n">1</span><span>Ouvre <b>megeveparcoeur.fr/app</b> dans <b>Safari</b></span></li>
<li><span class="n">2</span><span>Touche <b>Partager</b> ⬆️ en bas de l'écran</span></li>
<li><span class="n">3</span><span>Choisis <b>« Sur l'écran d'accueil »</b> ➕</span></li></ol></div>
<div class="card" style="top:860px"><h2>🤖 Sur Android</h2><ol>
<li><span class="n">1</span><span>Ouvre <b>megeveparcoeur.fr/app</b> dans <b>Chrome</b></span></li>
<li><span class="n">2</span><span>Touche <b>« Installer l'appli »</b></span></li>
<li><span class="n">3</span><span>Confirme : l'icône apparaît ✅</span></li></ol></div>
<div class="note" style="top:1310px">Depuis Instagram ? Touche <b>⋯</b> en haut à droite puis<br><b>« Ouvrir dans le navigateur »</b>, et active les notifications 🔔</div>
<div class="cta" style="bottom:420px">👇 Touche le lien</div>"""
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome"); pg=b.new_page(viewport={"width":1080,"height":1920})
    for i,h in ((1,f1),(2,f2)):
        t=R/f"instagram/app/_t{i}.html"; t.write_text("<!DOCTYPE html><meta charset=utf-8>"+h,encoding="utf-8")
        pg.goto(t.as_uri()); pg.wait_for_timeout(700); pg.screenshot(path=f"/tmp/s{i}.png"); t.unlink()
    b.close()
