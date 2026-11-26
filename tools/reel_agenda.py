#!/usr/bin/env python3
"""Reel Instagram « L'agenda de la semaine » (20 s, 1080x1920) à partir des images de tools/story_agenda.py.
Usage : python3 tools/reel_agenda.py AAAA-MM-JJ   (lancer d'abord tools/story_agenda.py AAAA-MM-JJ)
Entrées : stories/agenda-AAAA-MM-JJ.png (agenda) et stories/agenda-AAAA-MM-JJ-fin.png (logo + « Bonne fin de semaine ! »)
Sortie  : stories/agenda-AAAA-MM-JJ-reel.mp4 — 15,5 s d'agenda (léger zoom) puis fondu vers la carte de fin (logo),
          musique « Megève c'est le rêve » (sons/megeve-c-est-le-reve.mp3, à partir de 1 min 03 s), muet si le fichier manque."""
import sys, subprocess, pathlib, tempfile, json
ROOT = pathlib.Path(__file__).resolve().parent.parent
D = sys.argv[1]
A, F = ROOT/f"stories/agenda-{D}.png", ROOT/f"stories/agenda-{D}-fin.png"
OUT = ROOT/f"stories/agenda-{D}-reel.mp4"
SON = ROOT/"sons/megeve-c-est-le-reve.mp3"
for f in (A, F):
    if not f.exists(): sys.exit(f"manque {f} : lance d'abord tools/story_agenda.py {D}")
T1, X, T = 16.0, 0.8, 20.0   # agenda 16 s (dont 0,8 s de fondu), fin = 4,8 s → 20 s
n1, n2 = int(T1*30), int((T-T1+X)*30)
v = (f"[0:v]scale=2160:3840,zoompan=z='1+0.06*on/{n1}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n1}:s=1080x1920:fps=30,"
     f"fade=t=in:st=0:d=0.6,format=yuv420p,setsar=1[a];"
     f"[1:v]scale=2160:3840,zoompan=z='1.12-0.12*on/{n2}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n2}:s=1080x1920:fps=30,"
     f"format=yuv420p,setsar=1[b];"
     f"[a][b]xfade=transition=fade:duration={X}:offset={T1-X},fade=t=out:st={T-0.6}:d=0.6[v]")
cmd = ["ffmpeg", "-loglevel", "error", "-y", "-loop", "1", "-framerate", "30", "-t", str(T1), "-i", str(A),
       "-loop", "1", "-framerate", "30", "-t", str(T-T1+X), "-i", str(F)]
if SON.exists():
    cmd += ["-ss", "63", "-t", str(T+1), "-i", str(SON)]
    flt = v + f";[2:a]afade=t=in:st=0:d=0.5,afade=t=out:st={T-2.5}:d=2.5[s]"
    cmd += ["-filter_complex", flt, "-map", "[v]", "-map", "[s]", "-c:a", "aac", "-b:a", "160k"]
else:
    print("ATTENTION : sons/megeve-c-est-le-reve.mp3 introuvable, reel muet")
    cmd += ["-filter_complex", v, "-map", "[v]"]
cmd += ["-t", str(T), "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-r", "30", "-movflags", "+faststart", str(OUT)]
subprocess.run(cmd, check=True)
info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,width,height:format=duration",
                                  "-of", "json", str(OUT)], capture_output=True, text=True).stdout)
print(OUT, "|", info["format"]["duration"], "s |", ", ".join(f'{s["codec_name"]}{" "+str(s["width"])+"x"+str(s["height"]) if "width" in s else ""}' for s in info["streams"]),
      "|", round(OUT.stat().st_size/1e6, 1), "Mo")
