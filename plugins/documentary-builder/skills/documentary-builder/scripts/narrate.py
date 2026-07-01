"""Kokoro TTS narration. Spoken text = sentence with phonetic respelling; captions keep proper text.
Outputs seg_<id>.wav per segment + timing.json (per-sentence start/end for captions)."""
import os, json, wave
import soundfile as sf
from kokoro_onnx import Kokoro
import dvlib as D

c = D.load_cfg()
k = Kokoro(D.PATHS["kokoro_model"], D.PATHS["kokoro_voices"])
PHON = c.get("phonetics", {})
def respell(t):
    for key in sorted(PHON, key=len, reverse=True):
        t = t.replace(key, PHON[key])
    return t

WAVS = "wavs"; os.makedirs(WAVS, exist_ok=True)
def synth(text, out):
    s, sr = k.create(text, voice=c["voice"], speed=c["speed"], lang="en-us")
    sf.write(out, s, sr, subtype="PCM_16")
def info(p):
    with wave.open(p,'rb') as w:
        return w.getframerate(), w.getsampwidth(), w.getnchannels(), w.getnframes(), w.readframes(w.getnframes())

items = []; i = 0
for seg in c["segments"]:
    for sent in seg["sentences"]:
        o = os.path.join(WAVS, f"s{i:03d}.wav"); synth(respell(sent), o)
        r,sw,ch,n,_ = info(o)
        items.append({"seg":seg["id"],"cap":sent,"path":o,"dur":n/r,"r":r,"sw":sw,"ch":ch}); i += 1
    print("  synth", seg["id"])

r=items[0]["r"]; sw=items[0]["sw"]; ch=items[0]["ch"]
def sil(sec): return b"\x00"*int(round(sec*r))*sw*ch
GAP = c.get("sentence_gap", 0.36)
order = [s["id"] for s in c["segments"]]; segments = {}
for sid in order:
    ss = [it for it in items if it["seg"]==sid]; buf=bytearray(); t=0.0; sents=[]
    for j,it in enumerate(ss):
        _,_,_,_,fr = info(it["path"]); st=t; buf.extend(fr); t+=it["dur"]
        sents.append({"text":it["cap"],"start":round(st,3),"end":round(t,3)})
        if j != len(ss)-1: buf.extend(sil(GAP)); t+=GAP
    o = f"seg_{sid}.wav"
    with wave.open(o,'wb') as w:
        w.setnchannels(ch); w.setsampwidth(sw); w.setframerate(r); w.writeframes(bytes(buf))
    segments[sid] = {"dur":round(t,3),"sentences":sents}
    print(f"  seg_{sid} {t:.1f}s")

json.dump({"order":order,"rate":r,"segments":segments}, open("timing.json","w"), indent=1)
print(f"total spoken {sum(segments[s]['dur'] for s in order):.1f}s  voice={c['voice']}")
