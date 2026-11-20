#!/usr/bin/env python3
"""Synthétise un feu de cheminée (boucle stéréo de 40 s) -> sons/feu.mp3"""
import numpy as np, subprocess, pathlib, scipy.signal as ss, scipy.io.wavfile as wf
SR=44100; L=40; X=3; N=(L+X)*SR
rng=np.random.default_rng(2026)
def env(rate, lo, hi, n=N):
    """enveloppe aléatoire lisse (rate ~ Hz)"""
    k=max(2,int(n*rate/SR)+3); pts=rng.random(k)
    e=np.interp(np.linspace(0,k-1,n),np.arange(k),pts)
    e=ss.sosfiltfilt(ss.butter(2,rate*1.5,fs=SR,output='sos'),e)
    return lo+(hi-lo)*np.clip((e-e.min())/(np.ptp(e)+1e-9),0,1)
def filt(x,kind,f,order=2): return ss.sosfilt(ss.butter(order,f,btype=kind,fs=SR,output='sos'),x)
def brown(n):
    b=np.cumsum(rng.standard_normal(n)); return filt(b,'high',20)
out=np.zeros((N,2))
# 1. grondement doux des flammes
for c in range(2):
    r=filt(brown(N),'low',320,2); r/=np.abs(r).max()
    out[:,c]+=.22*r*env(.35,.55,1)*env(1.8,.75,1)
# 2. flammes qui lèchent (souffle médium, scintillement)
for c in range(2):
    w=filt(rng.standard_normal(N),'band',[180,1100]); w/=np.abs(w).max()
    lick=env(5,0,1)**2*env(.4,.3,1)
    out[:,c]+=.16*w*lick
# 3. léger chuintement aigu
for c in range(2):
    h=filt(rng.standard_normal(N),'band',[2500,7000]); h/=np.abs(h).max()
    out[:,c]+=.012*h*env(2,.2,1)
# 4. crépitements : impulsions brèves dans des bancs de résonances
dens=env(.25,1.5,14)*env(1.2,.3,1)       # bouffées
p=dens/SR; ev=np.nonzero(rng.random(N)<p)[0]
bands=[(900,1600),(1600,2600),(2600,3800),(3800,5200),(5200,7000)]
banks=[np.zeros((N,2)) for _ in bands]
for t in ev:
    a=min(1,rng.pareto(2.2)*.12+.02)      # la plupart discrets, quelques forts
    ln=int(SR*rng.uniform(.0004,.0025)); g=np.exp(-np.arange(ln)/(ln/4))*rng.standard_normal(ln)*a
    pan=rng.uniform(.15,.85); b=rng.integers(len(bands)) if a<.35 else rng.integers(0,2)
    if t+ln<N: banks[b][t:t+ln,0]+=g*(1-pan); banks[b][t:t+ln,1]+=g*pan
for (lo,hi),bk in zip(bands,banks):
    out+=1.2*ss.sosfilt(ss.butter(2,[lo,hi],btype='band',fs=SR,output='sos'),bk,axis=0)
# 5. quelques « pops » de bois (plus graves, avec étincelles)
t=int(SR*rng.uniform(1,3))
while t<N-SR:
    f=rng.uniform(350,1100); ln=int(SR*rng.uniform(.03,.07)); k=np.arange(ln)
    pop=np.sin(2*np.pi*f*k/SR*(1-.25*k/ln))*np.exp(-k/(ln/5))+.5*rng.standard_normal(ln)*np.exp(-k/(ln/12))
    pop=filt(pop,'band',[200,3000])*rng.uniform(.10,.22); pan=rng.uniform(.25,.75)
    out[t:t+ln,0]+=pop*(1-pan); out[t:t+ln,1]+=pop*pan
    for j in range(rng.integers(2,6)):     # petites étincelles qui suivent
        u=t+int(SR*rng.uniform(.02,.35)); s=int(SR*.001); 
        if u+s<N: sp=rng.standard_normal(s)*np.exp(-np.arange(s)/(s/4))*rng.uniform(.03,.09); out[u:u+s]+=sp[:,None]*.5
    t+=int(SR*rng.uniform(2.5,7))
# adoucir le haut du spectre, compresser doucement
out=ss.sosfilt(ss.butter(2,8500,fs=SR,output='sos'),out,axis=0)
out=np.tanh(out*1.6)/1.6
# boucle sans couture : fondu enchaîné de X s
xf=X*SR; w=np.linspace(0,1,xf)[:,None]
loop=out[:L*SR].copy(); loop[:xf]=loop[:xf]*np.sqrt(w)+out[L*SR:L*SR+xf]*np.sqrt(1-w)
loop/=np.abs(loop).max(); loop*=.7
R=pathlib.Path(__file__).resolve().parent.parent; wav="/tmp/feu.wav"
wf.write(wav,SR,(loop*32767).astype(np.int16))
subprocess.run(["ffmpeg","-y","-loglevel","error","-i",wav,"-c:a","libmp3lame","-b:a","96k",str(R/"sons/feu.mp3")],check=True)
print("ok", (R/"sons/feu.mp3").stat().st_size)
