"""Build a narrated animated DATA SEGMENT from a config (standalone infographics explainer).
Usage: python datasegment.py <config.json>
Config has a `data_segment` block (or top-level) with { voice?, output?, cards: [ ... ] }.
Each card: { "type": section|number|compare|checklist|stats, ...fields, "narration": "...", "pad": 0.7 }
No footage required. Renders cards, narrates with Kokoro (+ phonetics), burns captions."""
import os, json, wave
import soundfile as sf
from kokoro_onnx import Kokoro
import dvlib as D, datacards as DC

c = D.load_cfg()
seg = c.get("data_segment", c)
voice = seg.get("voice", c.get("voice", "am_michael"))
speed = seg.get("speed", c.get("speed", 0.95))
phon  = c.get("phonetics", {})
out   = seg.get("output", c.get("output", "data_segment.mp4"))
cards = seg["cards"]
os.makedirs("pieces", exist_ok=True)

k = Kokoro(D.PATHS["kokoro_model"], D.PATHS["kokoro_voices"])
def respell(t):
    for kk in sorted(phon, key=len, reverse=True): t = t.replace(kk, phon[kk])
    return t

RENDER = {"section":  lambda o,d,cd: DC.section_card(c,o,d,cd["title"],cd.get("subtitle","")),
          "number":   lambda o,d,cd: DC.number_card(c,o,d,cd["big"],cd.get("sub","")),
          "compare":  lambda o,d,cd: DC.compare_card(c,o,d,cd["title"],cd["items"]),
          "checklist":lambda o,d,cd: DC.checklist_card(c,o,d,cd["title"],cd["items"]),
          "stats":    lambda o,d,cd: DC.stats_card(c,o,d,cd["title"],cd["pairs"])}

# 1) narrate each card, measure durations
rate=sw=ch=None; narr=[]  # (wav_or_None, speech_dur)
durs=[]
for i,cd in enumerate(cards):
    txt = cd.get("narration","")
    if txt:
        s,srr = k.create(respell(txt), voice=voice, speed=speed, lang="en-us")
        o = f"pieces/dseg_a{i}.wav"; sf.write(o, s, srr, subtype="PCM_16")
        with wave.open(o,'rb') as w:
            rate,sw,ch = w.getframerate(),w.getsampwidth(),w.getnchannels(); sd = w.getnframes()/rate
        narr.append((o,sd))
    else:
        narr.append((None, cd.get("dur",3.0)))
    durs.append(round(narr[i][1] + cd.get("pad",0.8), 3))
    print(f"  card {i} {cd['type']:9s} {durs[i]:5.2f}s")
if rate is None: rate,sw,ch = 24000,2,1

# 2) render each card visual to its duration
pieces=[]
for i,cd in enumerate(cards):
    o=f"pieces/dseg_v{i}.mp4"; RENDER[cd["type"]](o,durs[i],cd); pieces.append(o)

# 3) concat visuals
with open("pieces/dseg_cat.txt","w",encoding="utf-8") as fp:
    for f in pieces: fp.write(f"file '{os.path.abspath(f)}'\n")
D.run([D.FF,"-y","-f","concat","-safe","0","-i","pieces/dseg_cat.txt","-c","copy","dseg_video.mp4"],"dseg_video.mp4")
total = D.dur("dseg_video.mp4")

# 4) narration track (each card's speech at that card's start) + captions
buf = bytearray(int(total*rate)*sw*ch); t=0.0; caps=[]
def ts(x):
    h=int(x//3600);m=int((x%3600)//60);s=x%60; return f"{h:02d}:{m:02d}:{s:06.3f}".replace('.',',')
for (wav,sd),dur,cd in zip(narr,durs,cards):
    if wav:
        with wave.open(wav,'rb') as w: fr=w.readframes(w.getnframes())
        pos=int(t*rate)*sw*ch; buf[pos:pos+len(fr)]=fr
        caps.append((t, t+sd, cd.get("narration","")))
    t += dur
with wave.open("dseg_narr.wav",'wb') as w:
    w.setnchannels(ch); w.setsampwidth(sw); w.setframerate(rate); w.writeframes(bytes(buf))
with open("dseg.srt","w",encoding="utf-8") as f:
    for n,(a,b,txt) in enumerate(caps,1): f.write(f"{n}\n{ts(a)} --> {ts(b)}\n{txt}\n\n")

# 5) mux narration + burn captions
style=("FontName=Arial,Fontsize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
       "BorderStyle=1,Outline=2,Shadow=1,MarginV=28,Alignment=2")
D.run([D.FF,"-y","-i","dseg_video.mp4","-i","dseg_narr.wav",
       "-vf",f"subtitles='dseg.srt':force_style='{style}'","-map","0:v","-map","1:a"]+D.enc(c)+[out], out)
print(f"\nOUTPUT: {out}  ({D.dur(out):.1f}s, {len(cards)} cards)")
