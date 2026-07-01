"""Animated data-card renderers (ffmpeg-only infographics). Imported by datasegment.py.
Each renderer writes an mp4 of exact `dur` seconds (dark card, gold accents, staggered reveals).
All drawtext uses expansion=none so literal text (%, :, etc.) renders safely."""
import os
import dvlib as D

GOLD="0xFFE08A"; GREEN="0x86E0A6"; FG="white"; SUB="0xCFE0F0"; BLUE="0x5AA9E6"

def _tf(name, text):
    os.makedirs("pieces", exist_ok=True)
    open(os.path.join("pieces", name), "w", encoding="utf-8").write(text)
    return "pieces/" + name

def _dt(tf, size, color, x, y, bold=True, alpha=None, font=None):
    f = font or (D.FONTB if bold else D.FONT)
    a = f":alpha='{alpha}'" if alpha else ""
    return (f"drawtext=fontfile='{f}':textfile='{tf}':expansion=none:"
            f"fontcolor={color}:fontsize={size}:x={x}:y={y}{a}")

def _fade(delay, dur=0.6): return f"if(lt(t,{delay}),0,min((t-{delay})/{dur},1))"

def _render(c, out, dur, vf):
    W,H,FPS = c["width"], c["height"], c["fps"]; bg = c.get("datacard_bg", "0x0B1A2A")
    D.run([D.FF,"-y","-f","lavfi","-i",f"color=c={bg}:s={W}x{H}:r={FPS}",
           "-f","lavfi","-i","anullsrc=r=48000:cl=stereo",
           "-vf", vf + ",format=yuv420p", "-map","0:v","-map","1:a","-t",str(dur)] + D.enc(c) + [out], out)

def section_card(c, out, dur, title, subtitle=""):
    parts=[_dt(_tf("dc_sec.txt",title),68,FG,"(w-text_w)/2","(h/2)-40",True,_fade(0.3,0.5)),
           f"drawbox=x=(w-360)/2:y=(h/2)+38:w='min(360,max(0,(t-0.3)/0.7)*360)':h=4:color={GOLD}:t=fill"]
    if subtitle: parts.append(_dt(_tf("dc_secsub.txt",subtitle),28,SUB,"(w-text_w)/2","(h/2)+58",False,_fade(0.9)))
    _render(c, out, dur, ",".join(parts))

def number_card(c, out, dur, big, sub=""):
    mw=560
    parts=[f"drawbox=x=(w-{mw})/2:y=(h/2)+70:w='min({mw},max(0,t/0.8)*{mw})':h=5:color={GOLD}:t=fill",
           _dt(_tf("dc_big.txt",big),120,FG,"(w-text_w)/2","(h/2)-135",True,_fade(0.0,0.5))]
    if sub: parts.append(_dt(_tf("dc_nsub.txt",sub),30,SUB,"(w-text_w)/2","(h/2)+95",False,_fade(0.9)))
    _render(c, out, dur, ",".join(parts))

def compare_card(c, out, dur, title, items):
    W=c["width"]; BARX=360; MAXBAR=W-BARX-200
    parts=[_dt(_tf("dc_cmpt.txt",title),36,GOLD,"(w-text_w)/2","70",True,_fade(0.1,0.5))]
    for i,it in enumerate(items):
        y0=210+i*170; delay=0.5+i*0.6; fw=int(MAXBAR*float(it["frac"])); col=GOLD if i==0 else BLUE
        parts.append(_dt(_tf(f"dc_cl{i}.txt",it["label"]),27,FG,str(BARX),str(y0-38),False,_fade(delay-0.1)))
        parts.append(f"drawbox=x={BARX}:y={y0}:w='min({fw},max(0,(t-{delay})/0.8)*{fw})':h=48:color={col}:t=fill")
        parts.append(_dt(_tf(f"dc_cv{i}.txt",it["value"]),40,FG,str(BARX+fw+20),str(y0+4),True,_fade(delay+0.7)))
    _render(c, out, dur, ",".join(parts))

def checklist_card(c, out, dur, title, items):
    parts=[_dt(_tf("dc_ckt.txt",title),36,GOLD,"(w-text_w)/2","70",True,_fade(0.1,0.5))]
    for i,it in enumerate(items):
        y0=200+i*82; delay=0.5+i*0.5
        parts.append(_dt(_tf(f"dc_chk{i}.txt","✓"),40,GREEN,"260",str(y0+2),True,_fade(delay,0.4),font=D.SYMBOL))
        parts.append(_dt(_tf(f"dc_ct{i}.txt",it),36,FG,"330",str(y0+4),False,_fade(delay,0.4)))
    _render(c, out, dur, ",".join(parts))

def stats_card(c, out, dur, title, pairs):
    W=c["width"]; n=len(pairs)
    parts=[_dt(_tf("dc_stt.txt",title),36,GOLD,"(w-text_w)/2","90",True,_fade(0.1,0.5))]
    for i,(val,lab) in enumerate(pairs):
        cx=int((i+0.5)/n*W); delay=0.5+i*0.45
        parts.append(_dt(_tf(f"dc_sv{i}.txt",val),86,FG,f"{cx}-text_w/2","(h/2)-40",True,_fade(delay,0.5)))
        parts.append(_dt(_tf(f"dc_sl{i}.txt",lab),28,SUB,f"{cx}-text_w/2","(h/2)+60",False,_fade(delay+0.2,0.5)))
    _render(c, out, dur, ",".join(parts))
