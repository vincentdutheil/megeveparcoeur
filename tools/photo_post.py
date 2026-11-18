#!/usr/bin/env python3
"""Prépare la photo Instagram de la semaine.
Usage : python3 tools/photo_post.py CHEMIN_PHOTO AAAA-MM-JJ [centre_vertical 0-1, défaut 0.5]
Sorties :
  instagram/photo-AAAA-MM-JJ.jpg        publication 1080x1350 (4:5, recadrage vertical, jamais paysage)
  instagram/photo-AAAA-MM-JJ-story.jpg  story 1080x1920 (la même photo 4:5 sur fond flouté)
Refuse une photo paysage dont le recadrage 4:5 garderait moins de 60 % de la largeur."""
import sys, pathlib
from PIL import Image, ImageOps, ImageFilter, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent

def crop45(im, cy=0.5):
    w, h = im.size
    tw = min(w, int(h * 4 / 5)); th = int(tw * 5 / 4)
    if th > h: th = h; tw = int(th * 4 / 5)
    x = (w - tw) // 2
    y = int(max(0, min(h - th, cy * h - th / 2)))
    return im.crop((x, y, x + tw, y + th)), tw / w

def main():
    src, day = sys.argv[1], sys.argv[2]
    cy = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    c, kept = crop45(im, cy)
    if kept < 0.6:
        print(f"REFUSÉ : photo paysage, le format 4:5 ne garderait que {kept:.0%} de la largeur. Choisis une photo verticale."); return 1
    post = c.resize((1080, 1350), Image.LANCZOS)
    out = ROOT / "instagram"; out.mkdir(exist_ok=True)
    p1 = out / f"photo-{day}.jpg"; post.save(p1, quality=88, optimize=True, progressive=True)
    # story : fond flouté + photo 4:5 + signature
    bg = ImageOps.fit(im, (1080, 1920), Image.LANCZOS).filter(ImageFilter.GaussianBlur(40))
    bg = Image.blend(bg, Image.new("RGB", bg.size, (14, 28, 60)), 0.45)
    ph = post.resize((960, 1200), Image.LANCZOS)
    mask = Image.new("L", ph.size, 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, *ph.size), 36, fill=255)
    bg.paste(ph, (60, 330), mask)
    logo = Image.open(ROOT / "img/logo-rond.png").convert("RGBA").resize((150, 150), Image.LANCZOS)
    bg.paste(logo, (465, 140), logo)
    d = ImageDraw.Draw(bg)
    try: f = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Bold.otf", 44)
    except Exception:
        try: f = ImageFont.truetype("DejaVuSans-Bold.ttf", 44)
        except Exception: f = ImageFont.load_default()
    t = "Nouvelle publication  ·  @megeveparcoeur"
    w = d.textlength(t, font=f); d.text(((1080 - w) / 2, 1590), t, fill=(255, 255, 255), font=f)
    p2 = out / f"photo-{day}-story.jpg"; bg.save(p2, quality=88, optimize=True, progressive=True)
    print(p1); print(p2); return 0

if __name__ == "__main__": sys.exit(main())
