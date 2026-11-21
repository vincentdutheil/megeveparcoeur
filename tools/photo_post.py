#!/usr/bin/env python3
"""Prépare la photo Instagram de la semaine.
Usage : python3 tools/photo_post.py CHEMIN_PHOTO AAAA-MM-JJ [centre_vertical 0-1, défaut 0.5]
Sorties :
  instagram/photo-AAAA-MM-JJ.jpg        publication, dans le format d'origine de la photo :
                                        portrait → 1080x1350 (4:5) · carrée → 1080x1080 ·
                                        paysage → reste en paysage (1080x720 pour du 3:2, au plus 1,91:1 soit 1080x566)
                                        JAMAIS de bandes floues ni de flou ajouté.
  instagram/photo-AAAA-MM-JJ-story.jpg  story 1080x1920 : la photo entière au centre sur un fond uni bleu nuit,
                                        logo en haut, « megeveparcoeur.fr » en bas (pas de flou)."""
import sys, pathlib
from PIL import Image, ImageOps, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
NAVY = (12, 26, 52)

def font(size):
    for f in ("/usr/share/fonts/opentype/inter/Inter-Bold.otf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "DejaVuSans-Bold.ttf"):
        try: return ImageFont.truetype(f, size)
        except Exception: pass
    return ImageFont.load_default()

def post_image(im, cy):
    w, h = im.size; r = w / h
    if r < 0.9:                      # portrait → 4:5
        tw = min(w, int(h * 4 / 5)); th = int(tw * 5 / 4)
        if th > h: th = h; tw = int(th * 4 / 5)
        x = (w - tw) // 2; y = int(max(0, min(h - th, cy * h - th / 2)))
        return im.crop((x, y, x + tw, y + th)).resize((1080, 1350), Image.LANCZOS), "portrait 4:5"
    if r <= 1.1:                     # presque carrée → 1:1
        s = min(w, h); x = (w - s) // 2; y = int(max(0, min(h - s, cy * h - s / 2)))
        return im.crop((x, y, x + s, y + s)).resize((1080, 1080), Image.LANCZOS), "carré 1:1"
    if r > 1.91:                     # panorama très large → on rogne les côtés jusqu'à 1,91:1 (limite Instagram)
        tw = int(h * 1.91); x = (w - tw) // 2; im = im.crop((x, 0, x + tw, h)); r = 1.91
    return im.resize((1080, round(1080 / r)), Image.LANCZOS), f"paysage {r:.2f}:1"

def main():
    src, day = sys.argv[1], sys.argv[2]
    cy = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    post, kind = post_image(im, cy)
    out = ROOT / "instagram"; out.mkdir(exist_ok=True)
    p1 = out / f"photo-{day}.jpg"; post.save(p1, quality=88, optimize=True, progressive=True)
    # story : fond uni bleu nuit, photo entière au centre
    bg = Image.new("RGB", (1080, 1920), NAVY)
    top, bottom = 330, 1560
    sc = min(960 / post.width, (bottom - top) / post.height)
    ph = post.resize((round(post.width * sc), round(post.height * sc)), Image.LANCZOS)
    mask = Image.new("L", ph.size, 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, *ph.size), 32, fill=255)
    bg.paste(ph, ((1080 - ph.width) // 2, top + (bottom - top - ph.height) // 2), mask)
    logo = Image.open(ROOT / "img/logo-rond.png").convert("RGBA").resize((170, 170), Image.LANCZOS)
    bg.paste(logo, (455, 120), logo)
    d = ImageDraw.Draw(bg); f = font(46); t = "megeveparcoeur.fr"
    d.text(((1080 - d.textlength(t, font=f)) / 2, 1640), t, fill=(255, 255, 255), font=f)
    p2 = out / f"photo-{day}-story.jpg"; bg.save(p2, quality=88, optimize=True, progressive=True)
    print(f"{p1}  ({kind}, {post.width}x{post.height})"); print(p2); return 0

if __name__ == "__main__": sys.exit(main())
