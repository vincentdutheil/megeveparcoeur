#!/usr/bin/env python3
"""Dessine le salon de chalet (SVG) du Coin des enfants et l'insère dans enfants/index.html.
Usage : python3 tools/gen_chalet.py"""
import os, random, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
random.seed(7)
W, H = 960, 460
o = []
a = o.append

a(f'<svg viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Un salon de chalet à Megève, au coin du feu">')
a('''<defs>
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0d1b36"/><stop offset="1" stop-color="#2c4a7c"/></linearGradient>
<radialGradient id="fireglow" cx=".5" cy=".82" r=".75"><stop offset="0" stop-color="#ffb04a" stop-opacity=".55"/><stop offset=".45" stop-color="#ff8a2a" stop-opacity=".16"/><stop offset="1" stop-color="#ff8a2a" stop-opacity="0"/></radialGradient>
<radialGradient id="lampglow" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#ffd58a" stop-opacity=".55"/><stop offset="1" stop-color="#ffd58a" stop-opacity="0"/></radialGradient>
<radialGradient id="vign" cx=".5" cy=".55" r=".75"><stop offset=".55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".55"/></radialGradient>
<linearGradient id="fl1" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#ff5a1f"/><stop offset=".6" stop-color="#ffa42b"/><stop offset="1" stop-color="#ffe27a"/></linearGradient>
<linearGradient id="fl2" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#ffb23a"/><stop offset="1" stop-color="#fff3b0"/></linearGradient>
<linearGradient id="goldG" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffe08a"/><stop offset=".5" stop-color="#e7b53c"/><stop offset="1" stop-color="#a87414"/></linearGradient>
<linearGradient id="silverG" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset=".5" stop-color="#c3cbd4"/><stop offset="1" stop-color="#7d8792"/></linearGradient>
<linearGradient id="leather" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#b56a35"/><stop offset=".55" stop-color="#8c4a22"/><stop offset="1" stop-color="#5e2f14"/></linearGradient>
<linearGradient id="beam" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6e4628"/><stop offset="1" stop-color="#3a2212"/></linearGradient>
<linearGradient id="floor" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4a2c18"/><stop offset="1" stop-color="#2e1a0d"/></linearGradient>
<linearGradient id="shade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f6e2bd"/><stop offset="1" stop-color="#e2bf86"/></linearGradient>
<pattern id="tartan" width="24" height="24" patternUnits="userSpaceOnUse"><rect width="24" height="24" fill="#a8261f"/><rect y="9" width="24" height="6" fill="#5c1210" opacity=".7"/><rect x="9" width="6" height="24" fill="#5c1210" opacity=".55"/><rect y="11" width="24" height="1.5" fill="#e9c46a" opacity=".7"/><rect x="11" width="1.5" height="24" fill="#e9c46a" opacity=".6"/><rect y="2" width="24" height="1" fill="#1f2d4a" opacity=".5"/><rect x="2" width="1" height="24" fill="#1f2d4a" opacity=".45"/></pattern>
<pattern id="wool" width="8" height="8" patternUnits="userSpaceOnUse"><rect width="8" height="8" fill="#efe6d6"/><path d="M0 4q2 -2 4 0t4 0" stroke="#e2d6c2" stroke-width="1" fill="none"/></pattern>
<clipPath id="win"><rect x="58" y="92" width="190" height="198" rx="4"/></clipPath>
</defs>''')

# ---- mur en vieux bois (planches verticales)
x = 0
while x < W:
    w = random.choice([46, 52, 58, 64])
    base = random.choice(["#5d3b23", "#573620", "#62402a", "#523219", "#5a3a22"])
    a(f'<rect x="{x}" y="0" width="{w}" height="{H}" fill="{base}"/>')
    for _ in range(4):
        gx = x + random.uniform(6, w - 6)
        a(f'<path d="M{gx:.0f} 0 C{gx+random.uniform(-6,6):.0f} 120 {gx+random.uniform(-6,6):.0f} 260 {gx+random.uniform(-4,4):.0f} {H}" stroke="#3b2414" stroke-width="{random.uniform(.6,1.4):.1f}" opacity=".35" fill="none"/>')
    if random.random() < .5:
        ky = random.uniform(40, 380)
        a(f'<ellipse cx="{x + w/2:.0f}" cy="{ky:.0f}" rx="4" ry="7" fill="#3b2414" opacity=".45"/>')
    a(f'<rect x="{x + w - 2}" y="0" width="2" height="{H}" fill="#2e1b0e" opacity=".8"/>')
    x += w
# poutres du plafond
a('<rect x="0" y="0" width="960" height="30" fill="url(#beam)"/><rect x="0" y="28" width="960" height="4" fill="#24140a" opacity=".6"/>')

# ---- fenêtre avec vue sur les montagnes enneigées
a('<g>')
a('<rect x="46" y="80" width="214" height="222" rx="6" fill="#3a2212"/>')
a('<g clip-path="url(#win)"><rect x="58" y="92" width="190" height="198" fill="url(#sky)"/>')
a('<circle cx="206" cy="124" r="13" fill="#fff6d8"/><circle cx="211" cy="120" r="12" fill="#13244a" opacity=".25"/>')
for i in range(18):
    a(f'<circle cx="{random.uniform(62,244):.0f}" cy="{random.uniform(96,170):.0f}" r="{random.uniform(.6,1.3):.1f}" fill="#fff" opacity="{random.uniform(.5,.9):.2f}"/>')
a('<path d="M58 238 L96 176 L120 204 L160 150 L196 196 L222 172 L248 210 L248 290 L58 290Z" fill="#dfe9f6"/>')
a('<path d="M160 150 L176 172 L166 170 L160 182 L152 168 L144 174Z M96 176 L106 192 L98 190 L92 198 L86 190Z" fill="#fff"/>')
a('<path d="M160 150 L196 196 L180 196 L170 178 Z M96 176 L120 204 L108 206Z" fill="#a9bfdc" opacity=".7"/>')
a('<path d="M58 256 Q150 236 248 252 L248 290 L58 290Z" fill="#f4f8fd"/>')
for tx in [70, 88, 104, 214, 232]:
    s = random.uniform(.8, 1.2)
    a(f'<path d="M{tx} {262 - 34*s:.0f} L{tx + 11*s:.0f} {268} L{tx - 11*s:.0f} {268}Z" fill="#1d3b33"/>')
a('<rect x="150" y="248" width="26" height="18" fill="#6e4628"/><path d="M146 250 L163 236 L180 250Z" fill="#fff"/><rect x="158" y="254" width="6" height="6" fill="#ffd27a"/>')
a('<g class="snowf">')
for i in range(26):
    a(f'<circle cx="{random.uniform(60,246):.0f}" cy="{random.uniform(90,290):.0f}" r="{random.uniform(1,2.2):.1f}" fill="#fff" style="animation-delay:-{random.uniform(0,6):.1f}s;animation-duration:{random.uniform(5,9):.1f}s"/>')
a('</g></g>')
a('<path d="M153 92 V290 M58 191 H248" stroke="#3a2212" stroke-width="8"/>')
a('<rect x="40" y="290" width="226" height="12" rx="3" fill="#6e4628"/>')
# rideaux en tartan, attachés
a('<path d="M30 74 H74 C74 150 60 200 82 236 C66 246 54 300 50 330 H30Z" fill="url(#tartan)"/><path d="M276 74 H232 C232 150 246 200 224 236 C240 246 252 300 256 330 H276Z" fill="url(#tartan)"/>')
a('<path d="M30 74 H74 C74 150 60 200 82 236 C66 246 54 300 50 330 H30Z M276 74 H232 C232 150 246 200 224 236 C240 246 252 300 256 330 H276Z" fill="#000" opacity=".12"/>')
a('<rect x="22" y="66" width="262" height="10" rx="5" fill="#3a2212"/><circle cx="22" cy="71" r="7" fill="#c9952a"/><circle cx="284" cy="71" r="7" fill="#c9952a"/>')
a('<path d="M72 232 q10 6 4 14 M234 232 q-10 6 -4 14" stroke="#e9c46a" stroke-width="4" fill="none"/>')
a('</g>')

# ---- conduit et cheminée en pierre
a('<g>')
a('<rect x="336" y="0" width="300" height="404" fill="#7d7268"/>')
y = 0
row = 0
while y < 404:
    h = random.choice([26, 30, 34])
    x = 336 - (row % 2) * 22
    while x < 636:
        w = random.choice([40, 48, 56, 64])
        x0, x1 = max(x, 338), min(x + w - 4, 634)
        if x1 - x0 > 8:
            c = random.choice(["#a59a8c", "#9b8f81", "#b0a596", "#8f8477", "#a89e93", "#b8ac9c"])
            a(f'<rect x="{x0}" y="{y + 2}" width="{x1 - x0}" height="{h - 4}" rx="7" fill="{c}"/>')
            a(f'<rect x="{x0 + 3}" y="{y + 4}" width="{(x1 - x0) * .6:.0f}" height="3" rx="1.5" fill="#fff" opacity=".12"/>')
        x += w
    y += h
    row += 1
a('<rect x="336" y="0" width="300" height="404" fill="#000" opacity=".08"/>')
# ouverture du foyer
a('<path d="M386 404 V300 Q486 236 586 300 V404Z" fill="#a39486"/><path d="M398 404 V306 Q486 252 574 306 V404Z" fill="#160c07"/>')
a('<path d="M398 404 V306 Q486 252 574 306 V404Z" fill="url(#fireglow)" class="glow"/>')
# chenets et bûches
a('<path d="M430 400 V380 M542 400 V380" stroke="#2a2a2a" stroke-width="6" stroke-linecap="round"/><circle cx="430" cy="376" r="6" fill="#3a3a3a"/><circle cx="542" cy="376" r="6" fill="#3a3a3a"/>')
a('<rect x="420" y="380" width="134" height="20" rx="10" fill="#6b4226" transform="rotate(-5 486 390)"/><rect x="424" y="384" width="128" height="18" rx="9" fill="#7d4f2e" transform="rotate(6 486 392)"/><circle cx="430" cy="394" r="8" fill="#c99a6b"/><circle cx="430" cy="394" r="3.5" fill="none" stroke="#8a5a33" stroke-width="2"/>')
a('<ellipse cx="486" cy="398" rx="62" ry="8" fill="#ff7a1a" opacity=".55" class="glow"/>')
# flammes
a('<path class="flame" d="M486 392C448 384 436 346 454 316C458 336 470 342 474 334C466 304 486 276 500 262C496 290 522 300 524 326C532 320 532 308 530 300C550 324 542 380 486 392Z" fill="url(#fl1)"/>')
a('<path class="flame b" d="M448 394C426 386 424 362 436 344C440 358 448 360 448 354C446 338 454 326 462 320C462 340 476 350 472 370C470 384 462 392 448 394Z" fill="url(#fl1)"/>')
a('<path class="flame c" d="M526 394C542 386 548 366 540 348C536 360 530 360 530 354C532 340 526 330 520 324C520 342 508 354 512 372C514 384 518 392 526 394Z" fill="url(#fl1)"/>')
a('<path class="flame b" d="M486 392C468 386 466 364 476 348C478 360 484 362 486 356C484 342 490 330 498 324C498 342 508 352 504 370C502 384 496 390 486 392Z" fill="url(#fl2)"/>')
a('<g fill="#ffcf6b"><circle class="ember-p" cx="476" cy="340" r="2" style="--dx:-14px"/><circle class="ember-p" cx="498" cy="336" r="1.6" style="--dx:12px;animation-delay:1.2s"/><circle class="ember-p" cx="486" cy="350" r="1.8" style="--dx:-6px;animation-delay:2.1s"/><circle class="ember-p" cx="508" cy="344" r="1.4" style="--dx:18px;animation-delay:2.9s"/></g>')
# âtre en pierre
a('<rect x="356" y="400" width="260" height="18" rx="4" fill="#9b8f81"/><rect x="356" y="400" width="260" height="4" fill="#fff" opacity=".12"/>')
# gants qui sèchent sur l'âtre
a('<g transform="translate(366 368)"><path d="M6 32C1 14 7 2 19 2C30 2 34 10 34 20L37 13C42 11 45 16 42 22L36 32Z" fill="#b8322a"/><rect x="4" y="29" width="34" height="8" rx="3" fill="#efe6d6"/></g>')
a('<g transform="translate(570 368) scale(-1 1) translate(-40 0)"><path d="M6 32C1 14 7 2 19 2C30 2 34 10 34 20L37 13C42 11 45 16 42 22L36 32Z" fill="#a52a22"/><rect x="4" y="29" width="34" height="8" rx="3" fill="#efe6d6"/></g>')
# skis anciens croisés au-dessus du manteau
for ang, col in [(-24, "#8a5530"), (24, "#9a6338")]:
    a(f'<g transform="rotate({ang} 486 150)"><rect x="480" y="38" width="12" height="214" rx="6" fill="{col}"/><path d="M480 44 C480 22 492 18 492 30" fill="none" stroke="{col}" stroke-width="12" stroke-linecap="round"/><rect x="478" y="140" width="16" height="14" rx="2" fill="#3a2212"/><path d="M478 147 h16" stroke="#c9952a" stroke-width="2"/></g>')
a('<g transform="rotate(-8 486 150)"><path d="M440 60 L532 246" stroke="#2b2b2b" stroke-width="3"/><circle cx="526" cy="234" r="7" fill="none" stroke="#2b2b2b" stroke-width="2.5"/></g>')
a('<g transform="rotate(8 486 150)"><path d="M532 60 L440 246" stroke="#2b2b2b" stroke-width="3"/><circle cx="446" cy="234" r="7" fill="none" stroke="#2b2b2b" stroke-width="2.5"/></g>')
# manteau : poutre ancienne
a('<rect x="318" y="252" width="336" height="28" rx="4" fill="url(#beam)"/><rect x="318" y="252" width="336" height="5" fill="#8a5a33"/>')
for i in range(5):
    gx = 330 + i * 64
    a(f'<path d="M{gx} 262 q20 6 40 0" stroke="#24140a" stroke-width="1.2" opacity=".5" fill="none"/>')
a('</g>')

# ---- objets sur le manteau : coupes, bougies, cadre
def trophy(x, y, s, grad, stroke):
    a(f'<g transform="translate({x} {y}) scale({s})"><path d="M14 6H62C62 52 52 70 38 72C24 70 14 52 14 6Z" fill="url(#{grad})"/><path d="M14 14C0 14 -2 40 18 44M62 14C76 14 78 40 58 44" fill="none" stroke="{stroke}" stroke-width="6"/><rect x="33" y="72" width="10" height="12" fill="{stroke}"/><rect x="20" y="82" width="36" height="10" rx="2" fill="#5b3a24"/><rect x="16" y="90" width="44" height="6" fill="#3a2212"/><path d="M28 16l10 -8 10 8 -10 18z" fill="#fff" opacity=".45"/></g>')
trophy(452, 152, 1.0, "goldG", "#c9952a")
trophy(392, 196, .58, "silverG", "#9aa3ad")
trophy(548, 192, .62, "goldG", "#c9952a")
# skieur gravé sur la grande coupe
a('<g transform="translate(478 176)" fill="#7a4b14"><circle cx="13" cy="4" r="3.5"/><path d="M8 9l7 2-2 9 6 5-2 2-7-6 1-6-5 3-1-3z"/><path d="M0 28l26-6" stroke="#7a4b14" stroke-width="2"/></g>')
# bougies en lanterne
for cx in [346, 626]:
    a(f'<g transform="translate({cx} 214)"><rect x="-10" y="0" width="20" height="38" rx="3" fill="#2a2a2a" opacity=".85"/><rect x="-7" y="4" width="14" height="30" rx="2" fill="#ffe7b0" opacity=".25"/><rect x="-4" y="18" width="8" height="16" rx="1.5" fill="#f6efe2"/><path class="flame c" d="M0 18 C-4 14 -2 9 0 6 C2 9 4 14 0 18Z" fill="#ffc24a"/><path d="M-12 0 L0 -8 L12 0Z" fill="#2a2a2a"/><circle cx="0" cy="-10" r="3" fill="none" stroke="#2a2a2a" stroke-width="2"/></g>')
# guirlande de sapin et lumières le long du manteau
pts = []
for i in range(23):
    gx = 322 + i * 15
    gy = 284 + 9 * abs(((i % 8) - 4) / 4) - 2
    pts.append((gx, gy))
for gx, gy in pts:
    a(f'<ellipse cx="{gx}" cy="{gy:.0f}" rx="11" ry="7" fill="{random.choice(["#1f4d36", "#245a3f", "#1a4430"])}"/>')
    a(f'<path d="M{gx-8} {gy:.0f} l-4 -3 M{gx+8} {gy:.0f} l4 -3 M{gx} {gy+5:.0f} l0 4" stroke="#2f6b4a" stroke-width="2"/>')
for k, (gx, gy) in enumerate(pts[::2]):
    col = ["#ffd27a", "#ffb04a", "#fff1c1"][k % 3]
    a(f'<circle class="tw" cx="{gx}" cy="{gy + 4:.0f}" r="3" fill="{col}" style="animation-delay:-{k * .37:.2f}s"/>')
# médailles accrochées sous la guirlande
a('<g transform="translate(372 290)"><path d="M0 0l10 26M20 0L10 26" stroke="#b8322a" stroke-width="5"/><circle cx="10" cy="34" r="10" fill="url(#goldG)" stroke="#a87414" stroke-width="2"/></g>')
a('<g transform="translate(582 290)"><path d="M0 0l10 26M20 0L10 26" stroke="#2b4c7e" stroke-width="5"/><circle cx="10" cy="34" r="10" fill="url(#silverG)" stroke="#7d8792" stroke-width="2"/></g>')

# ---- réserve de bûches à gauche du foyer
a('<g transform="translate(276 330)"><rect x="0" y="0" width="54" height="80" rx="3" fill="#2e1b0e"/>')
for r in range(4):
    for c in range(3):
        a(f'<circle cx="{9 + c * 18 + (r % 2) * 4}" cy="{12 + r * 18}" r="8.5" fill="#b07a48"/><circle cx="{9 + c * 18 + (r % 2) * 4}" cy="{12 + r * 18}" r="4" fill="none" stroke="#7d4f2e" stroke-width="1.5"/>')
a('</g>')

# ---- plancher et tapis en peau de mouton
a(f'<rect x="0" y="410" width="{W}" height="{H - 410}" fill="url(#floor)"/>')
for i in range(0, W, 80):
    a(f'<path d="M{i} 410 L{i - 40} {H}" stroke="#24140a" stroke-width="2" opacity=".6"/>')
fur = "M330 440 "
for i in range(0, 25):
    fx = 330 + i * 13
    fur += f"q6 {-10 if i % 2 else -6} 13 0 "
fur += "q10 10 0 20 H330 q-10 -10 0 -20Z"
a(f'<path d="{fur}" fill="#f3ebdd"/><path d="{fur}" fill="url(#wool)" opacity=".5"/>')
# casque de ski posé sur le tapis
a('<g transform="translate(250 392) scale(.62)"><path d="M6 64C6 26 36 8 64 8C92 8 114 28 116 62Z" fill="#1f3d7a"/><path d="M18 40C30 22 56 16 76 20" stroke="#4f78c4" stroke-width="7" fill="none" stroke-linecap="round"/><rect x="4" y="60" width="114" height="12" rx="6" fill="#16295a"/><rect x="22" y="42" width="78" height="26" rx="13" fill="#f4a62a" stroke="#111" stroke-width="4"/><path d="M34 50h22" stroke="#fff" stroke-width="4" stroke-linecap="round" opacity=".7"/></g>')

# ---- affiche ancienne encadrée (dessin original)
a('<g transform="translate(700 64)"><rect x="-8" y="-8" width="156" height="196" rx="3" fill="#2e1b0e"/><rect x="-3" y="-3" width="146" height="186" fill="#c9952a" opacity=".55"/>')
a('<rect x="0" y="0" width="140" height="180" fill="#f2e3c4"/><rect x="0" y="0" width="140" height="112" fill="#f0a65a"/><circle cx="104" cy="34" r="16" fill="#ffe9a8"/>')
a('<path d="M0 112 L36 60 L58 84 L86 40 L118 86 L140 70 V112Z" fill="#fbf6ec"/><path d="M86 40 L118 86 L104 86 L92 62Z M36 60 L58 84 L48 86Z" fill="#c9d6e6"/>')
a('<path d="M0 112 Q70 100 140 116 V128 H0Z" fill="#fbf6ec"/>')
a('<g transform="translate(46 70) rotate(-12)" fill="#1f3d7a"><circle cx="14" cy="4" r="4"/><path d="M9 10l9 2-2 10 7 6-2 3-9-7 1-6-6 4-2-3z"/><path d="M-2 34l34-8" stroke="#b8322a" stroke-width="2.5"/></g>')
a('<text x="70" y="152" text-anchor="middle" font-family="Georgia, serif" font-size="25" font-weight="700" letter-spacing="3" fill="#b8322a">MEGÈVE</text>')
a('<text x="70" y="170" text-anchor="middle" font-family="Georgia, serif" font-size="9" letter-spacing="2.5" fill="#3a2212">SPORTS D\'HIVER</text></g>')

# ---- lampe sur pied et halo
a('<circle cx="912" cy="150" r="120" fill="url(#lampglow)"/>')
a('<path d="M912 178 V420 M890 420 H934" stroke="#2b2b2b" stroke-width="5" stroke-linecap="round"/><path d="M884 130 H940 L952 178 H872Z" fill="url(#shade)"/><path d="M872 178 H952" stroke="#c9a46a" stroke-width="3"/>')

# ---- fauteuil club en cuir avec plaid
a('<g transform="translate(676 236)">')
a('<path d="M20 60 C20 18 40 6 100 6 C160 6 180 18 180 60 V150 H20Z" fill="url(#leather)"/>')
a('<path d="M44 40 C60 30 140 30 156 40" stroke="#5e2f14" stroke-width="3" fill="none" opacity=".6"/>')
for i in range(5):
    for j in range(2):
        a(f'<circle cx="{52 + i * 24}" cy="{56 + j * 22}" r="2.5" fill="#4a2410"/>')
a('<rect x="38" y="120" width="124" height="34" rx="12" fill="#9a5528"/>')
a('<path d="M0 98 C0 80 30 80 34 98 V180 H0Z" fill="url(#leather)"/><path d="M166 98 C170 80 200 80 200 98 V180 H166Z" fill="url(#leather)"/>')
a('<rect x="0" y="150" width="200" height="34" rx="6" fill="#6b3518"/>')
a('<path d="M14 184 v12 M186 184 v12" stroke="#2e1608" stroke-width="7" stroke-linecap="round"/>')
# coussin en laine et plaid tartan
a('<rect x="58" y="72" width="64" height="50" rx="14" fill="url(#wool)" transform="rotate(-8 90 97)"/>')
a('<path d="M150 50 C176 46 190 64 192 96 L198 170 C180 178 164 172 160 160 L150 120 Z" fill="url(#tartan)"/><path d="M150 50 C176 46 190 64 192 96 L198 170 C180 178 164 172 160 160 L150 120 Z" fill="#000" opacity=".12"/>')
a('<path d="M160 160 l-3 8 M168 166 l-2 8 M178 170 l-1 8 M188 170 l0 8" stroke="#e9c46a" stroke-width="2"/>')
a('</g>')

# ---- table d'appoint : chocolat chaud et livres
a('<g transform="translate(616 352)"><rect x="0" y="0" width="56" height="8" rx="3" fill="#6e4628"/><path d="M8 8 V58 M48 8 V58" stroke="#4a2c18" stroke-width="5"/>')
a('<rect x="4" y="-12" width="44" height="7" rx="1" fill="#2b4c7e"/><rect x="7" y="-19" width="40" height="7" rx="1" fill="#b8322a"/>')
a('<g transform="translate(14 -50)"><path class="steam" d="M8 0C2 -8 14 -12 8 -20" stroke="#fff" stroke-width="2.5" fill="none" stroke-linecap="round"/><path class="steam s2" d="M20 2C14 -6 26 -10 20 -18" stroke="#fff" stroke-width="2.5" fill="none" stroke-linecap="round"/>')
a('<path d="M0 6H28L26 32H2Z" fill="#efe6d6"/><path d="M28 12C38 12 38 26 27 26" fill="none" stroke="#e4d7c2" stroke-width="4"/><ellipse cx="14" cy="7" rx="14" ry="3.5" fill="#6b3a1c"/><rect x="6" y="2" width="7" height="5" rx="1.5" fill="#fff"/><rect x="15" y="1" width="7" height="5" rx="1.5" fill="#fde7ef"/><path d="M6 18h16" stroke="#b8322a" stroke-width="3"/></g>')
a('</g>')

# ---- lumière chaude du feu et vignettage
a(f'<rect width="{W}" height="{H}" fill="url(#fireglow)" class="glow" opacity=".7"/>')
a(f'<rect width="{W}" height="{H}" fill="url(#vign)"/>')
a('</svg>')
SVG = "\n".join(o)

p = os.path.join(ROOT, "enfants/index.html")
s = open(p, encoding="utf-8").read()
s2 = re.sub(r'(<div class="scene"[^>]*>)\s*<svg.*?</svg>', lambda m: m.group(1) + "\n" + SVG, s, count=1, flags=re.S)
assert s2 != s or SVG in s
open(p, "w", encoding="utf-8").write(s2)
print("ok", len(SVG) // 1024, "Ko")
