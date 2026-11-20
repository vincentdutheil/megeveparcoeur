#!/usr/bin/env python3
"""Régénère sitemap.xml (pages FR + EN avec leurs alternates). Usage : python3 tools/sitemap.py"""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = "https://www.megeveparcoeur.fr"
P = [("/", "/en/", "weekly", 1.0), ("/meteo/", "/en/meteo/", "daily", .8), ("/webcams/", "/en/webcams/", "daily", .7),
     ("/que-faire/", "/en/things-to-do/", "weekly", .8)]
for fr, en in [("ce-week-end", "this-weekend"), ("aujourd-hui", "today"), ("avec-des-enfants", "with-kids"), ("quand-il-pleut", "rainy-day"), ("gratuit", "free")]:
    P.append((f"/que-faire/{fr}/", f"/en/things-to-do/{en}/", "daily", .8))
P += [("/balades/", "/en/balades/", "monthly", .7), ("/carte/", "/en/carte/", "monthly", .6), ("/venir/", "/en/getting-here/", "monthly", .6),
      ("/proposer/", "/en/submit-event/", "monthly", .4), ("/boutique/", "/en/boutique/", "monthly", .5), ("/enfants/", None, "monthly", .6)]
out = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
for fr, en, f, pr in P:
    alt = "" if not en else f'<xhtml:link rel="alternate" hreflang="fr" href="{S}{fr}"/><xhtml:link rel="alternate" hreflang="en" href="{S}{en}"/>'
    out.append(f'  <url><loc>{S}{fr}</loc>{alt}<changefreq>{f}</changefreq><priority>{pr:.1f}</priority></url>')
    if not en: continue
    out.append(f'  <url><loc>{S}{en}</loc>{alt}<changefreq>{f}</changefreq><priority>{max(.1, pr - .2):.1f}</priority></url>')
out.append('</urlset>')
open(os.path.join(ROOT, "sitemap.xml"), "w").write("\n".join(out) + "\n")
print(len(P) * 2, "URL")
