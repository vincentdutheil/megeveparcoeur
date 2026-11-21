#!/usr/bin/env python3
"""Reel Instagram à partir de quelques photos de Vincent (diaporama doux, 1080x1920).
Usage : python3 tools/reel_photos.py FICHIER.json [--audio musique.mp3]
FICHIER.json :
 {"date":"AAAA-MM-JJ",
  "kicker":"De l'automne à l'hiver",            (bandeau doré, constant)
  "items":[{"src":"chemin/photo.jpg", "label":"22 octobre · la première neige"}, ...],
  "fin":["Megève par cœur", "L'hiver arrive ❄"]   (carte de fin : 1 ou 2 lignes)}
Règles (identiques aux stories) : chaque photo est montrée ENTIÈRE, dans son format d'origine
(paysage reste paysage), sur un fond uni bleu nuit, JAMAIS de bandes floues.
Le bas de l'image (zone de la légende et du sticker musique d'Instagram) reste libre.
Sorties dans instagram/ : reel-DATE.mp4 (muet par défaut : la musique s'ajoute dans Buffer,
pour qu'elle soit identifiée sur Instagram) et reel-DATE-cover.jpg (couverture)."""
import json, sys, pathlib, subprocess
from PIL import Image, ImageOps, ImageDraw, ImageFont

R = pathlib.Path(__file__).resolve().parent.parent
W, H, FPS = 1080, 1920, 30
NAVY, GOLD, WHITE = (12, 26, 52), (242, 183, 27), (255, 255, 255)
SEG, FADE, END = 3.4, 0.6, 2.8          # durée par photo, fondu, carte de fin (s)
TOP, BOTTOM, MAXW = 390, 1590, 1010      # zone photo (sous 1590 : légende et sticker musique d’Instagram)


def font(size, w="Bold"):
    for f in (f"/usr/share/fonts/opentype/inter/Inter-{w}.otf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try: return ImageFont.truetype(f, size)
        except Exception: pass
    return ImageFont.load_default()


def centered(d, y, t, f, fill):
    d.text(((W - d.textlength(t, font=f)) / 2, y), t, fill=fill, font=f)


def prep(src):
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    r = im.width / im.height
    if r > 1.91: tw = int(im.height * 1.91); x = (im.width - tw) // 2; im = im.crop((x, 0, x + tw, im.height)); r = 1.91
    sc = min(MAXW / im.width, (BOTTOM - TOP) / im.height)
    fw, fh = round(im.width * sc), round(im.height * sc)
    big = im.resize((round(fw * 1.12), round(fh * 1.12)), Image.LANCZOS)   # marge pour le zoom lent
    mask = Image.new("L", (fw, fh), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, fw, fh), 30, fill=255)
    return big, (fw, fh), mask


def base(logo, kicker):
    bg = Image.new("RGB", (W, H), NAVY); bg.paste(logo, (W // 2 - logo.width // 2, 95), logo)
    d = ImageDraw.Draw(bg); centered(d, 262, kicker.upper(), font(34, "SemiBold"), GOLD)
    centered(d, 1650, "megeveparcoeur.fr", font(40, "SemiBold"), WHITE)
    return bg


def photo_frame(bg0, p, label, t):
    big, (fw, fh), mask = p
    z = 1.12 - 0.10 * t                                    # zoom avant très lent, photo toujours entière dans son cadre
    cw = round(fw * 1.12 / z); ch = round(fh * 1.12 / z)
    cw, ch = min(cw, big.width), min(ch, big.height)
    x = (big.width - cw) // 2; y = (big.height - ch) // 2
    ph = big.crop((x, y, x + cw, y + ch)).resize((fw, fh), Image.BILINEAR)
    im = bg0.copy(); im.paste(ph, ((W - fw) // 2, TOP + (BOTTOM - TOP - fh) // 2), mask)
    d = ImageDraw.Draw(im); centered(d, 318, label, font(44), WHITE)
    return im


def end_card(logo_big, lines):
    im = Image.new("RGB", (W, H), NAVY); im.paste(logo_big, (W // 2 - logo_big.width // 2, 600), logo_big)
    d = ImageDraw.Draw(im); y = 600 + logo_big.height + 70
    for i, t in enumerate(lines):
        centered(d, y, t, font(64 if i == 0 else 46, "Bold" if i == 0 else "Medium"), WHITE if i == 0 else GOLD); y += 95
    centered(d, 1650, "megeveparcoeur.fr", font(40, "SemiBold"), WHITE)
    return im


def main():
    c = json.load(open(sys.argv[1], encoding="utf-8")); day = c["date"]
    audio = sys.argv[sys.argv.index("--audio") + 1] if "--audio" in sys.argv else None
    logo_src = Image.open(R / "img/logo-rond.png").convert("RGBA")
    bg0 = base(logo_src.resize((150, 150), Image.LANCZOS), c.get("kicker", ""))
    endc = end_card(logo_src.resize((300, 300), Image.LANCZOS), c.get("fin", ["Megève par cœur"]))
    items = [(prep(R / it["src"] if not pathlib.Path(it["src"]).is_absolute() else it["src"]), it.get("label", "")) for it in c["items"]]
    out = R / "instagram"; out.mkdir(exist_ok=True); mp4 = out / f"reel-{day}.mp4"
    n = len(items); total = n * SEG + END; nf = round(total * FPS)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if audio: cmd += ["-i", audio, "-map", "0:v", "-map", "1:a", "-af", f"afade=t=out:st={total-1.5}:d=1.5", "-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(mp4)]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    seg_dur = SEG + FADE                                   # chaque photo reste FADE s de plus pour le fondu
    for k in range(nf):
        t = k / FPS; i = min(int(t // SEG), n)
        if i < n:
            fr = photo_frame(bg0, items[i][0], items[i][1], (t - i * SEG) / seg_dur)
        else:
            fr = endc
        # fondu avec le segment précédent pendant les FADE premières secondes
        if i >= 1 and t - i * SEG < FADE:
            prev = photo_frame(bg0, items[i - 1][0], items[i - 1][1], (t - (i - 1) * SEG) / seg_dur)
            fr = Image.blend(prev, fr, (t - i * SEG) / FADE)
        if k == 0: cover = fr
        if i == 0 and abs(t - 1.0) < 1 / FPS: cover = fr
        ff.stdin.write(fr.tobytes())
    ff.stdin.close(); ff.wait()
    cv = out / f"reel-{day}-cover.jpg"; cover.save(cv, quality=90)
    print(mp4, f"{total:.1f} s,", "avec musique" if audio else "muette (musique à ajouter dans Buffer)"); print(cv)


if __name__ == "__main__":
    main()
