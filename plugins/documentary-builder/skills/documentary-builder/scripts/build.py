"""Assemble the documentary. Phases: norm | assemble | final | all.
Reads project.json + footage.json + timing.json. Run from a SHORT working dir."""
import os, sys, json, wave
import dvlib as D

c = D.load_cfg(); phase = sys.argv[2] if len(sys.argv) > 2 else "all"
W, H, FPS = c["width"], c["height"], c["fps"]; ENC = D.enc(c); FF = D.FF
NORM, PIECES = "norm", "pieces"; os.makedirs(NORM, exist_ok=True); os.makedirs(PIECES, exist_ok=True)
footage = json.load(open("footage.json")); timing = json.load(open("timing.json"))
ORDER = timing["order"]; SEG = timing["segments"]; SEGCFG = {s["id"]: s for s in c["segments"]}
FONT, FONTB = D.FONT, D.FONTB

def tf(name, text):
    open(os.path.join(PIECES, name), "w", encoding="utf-8").write(text); return "pieces/" + name

# ---------- normalize ----------
def norm_clip(cid):
    info = footage["clips"][cid]; out = os.path.join(NORM, f"{cid}.mp4")
    if os.path.isfile(out): return out
    ins = ["-i", info["path"]]
    if not info["audio"]: ins += ["-f","lavfi","-i","anullsrc=r=48000:cl=stereo"]
    if info["orient"] == "portrait":
        vf = (f"[0:v]fps={FPS},format=yuv420p,split=2[a][b];"
              f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},gblur=sigma=18,eq=brightness=-0.06[bg];"
              f"[b]scale=-2:{H}[fg];[bg][fg]overlay=(W-w)/2:0,setsar=1[v]")
    else:
        vf = (f"[0:v]fps={FPS},format=yuv420p,scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1[v]")
    amap = "0:a" if info["audio"] else "1:a"
    D.run([FF,"-y"]+ins+["-filter_complex",vf,"-map","[v]","-map",amap,"-af","aresample=48000","-shortest"]+ENC+[out], out)
    return out

def normalize():
    for cid in footage["clips"]: norm_clip(cid)

# ---------- cards ----------
def _dt(fontfile, txt_rel, size, color, y, fade=None):
    a = f":alpha='{fade}'" if fade else ""
    return (f"drawtext=fontfile='{fontfile}':textfile='{txt_rel}':fontcolor={color}:fontsize={size}:"
            f"x=(w-text_w)/2:y={y}{a}")

def _card(out, d, bg, draws, dim=0.35, blur=8):
    vf = (f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},gblur=sigma={blur},"
          f"setsar=1,format=yuv420p,drawbox=x=0:y=0:w={W}:h={H}:color=black@{dim}:t=fill," + ",".join(draws) + "[v]")
    D.run([FF,"-y","-loop","1","-t",str(d),"-i",bg,"-f","lavfi","-t",str(d),"-i","anullsrc=r=48000:cl=stereo",
           "-filter_complex",vf,"-map","[v]","-map","1:a"]+ENC+[out], out)

def _bg(key, default_first=True):
    keys = list(c["photos"].keys())
    return D.ppath(c, c.get(key, keys[0] if default_first else keys[-1]))

def title_card(out, d):
    t1=tf("t1.txt",c["title"]); t2=tf("t2.txt",c.get("subtitle","")); t3=tf("t3.txt",c.get("location_line",""))
    draws=[_dt(FONTB,t1,58,"white","h/2-90","if(lt(t,0.6),t/0.6,1)"),
           _dt(FONT,t2,26,"white","h/2+0","if(lt(t,1.0),0,min((t-1.0)/0.6,1))"),
           _dt(FONT,t3,20,"0xDDDDDD","h/2+44","if(lt(t,1.4),0,min((t-1.4)/0.6,1))")]
    _card(out,d,_bg("title_bg"),draws,0.30,6)

def outro_card(out, d):
    lines=c.get("outro",[c["title"]]); draws=[]
    for i,ln in enumerate(lines):
        t=tf(f"o{i}.txt",ln)
        col = "0xFFE08A" if i==len(lines)-2 else ("white" if i<len(lines)-1 else "0xDDDDDD")
        sz = 26 if i==0 else (24 if i==len(lines)-2 else 18)
        y = f"h/2{-110+i*40:+d}"
        draws.append(_dt(FONTB if i<=len(lines)-2 else FONT, t, sz, col, y))
    _card(out,d,_bg("outro_bg",False),draws,0.40,8)

def chapter_card(out, d, roman, title):
    r=tf(f"c{roman}.txt",roman); t=tf(f"ct{roman}.txt",title)
    draws=[_dt(FONTB,r,30,"0xFFE08A","h/2-44"),_dt(FONTB,t,46,"white","h/2+6")]
    _card(out,d,_bg("chapter_bg"),draws,0.42,10)

def kenburns(out, photo, d, zdir):
    frames=int(d*FPS); z="min(zoom+0.0006,1.18)" if zdir=="in" else "if(eq(on,1),1.18,max(zoom-0.0006,1.0))"
    vf=(f"[0:v]scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},setsar=1,"
        f"zoompan=z='{z}':d={frames}:s={W}x{H}:fps={FPS}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)',format=yuv420p[v]")
    D.run([FF,"-y","-i",photo,"-f","lavfi","-t",str(d),"-i","anullsrc=r=48000:cl=stereo",
           "-filter_complex",vf,"-map","[v]","-map","1:a","-t",str(d)]+ENC+[out], out)

# ---------- footage pool + pieces ----------
POOL=c["clip_pool"]; _cur={"i":0,"off":0.0}
def take_slices(Dd):
    out=[]; need=Dd
    while need>1e-3:
        cid=POOL[_cur["i"]%len(POOL)]; clen=footage["clips"][cid]["dur"]-0.15; avail=clen-_cur["off"]
        if avail<=0.4: _cur["i"]+=1; _cur["off"]=0.0; continue
        t=min(avail,need); out.append((cid,round(_cur["off"],2),round(t,2))); _cur["off"]+=t; need-=t
        if _cur["off"]>=clen-0.4: _cur["i"]+=1; _cur["off"]=0.0
    return out

_pc={"i":0}
def npiece(tag): _pc["i"]+=1; return os.path.join(PIECES,f"p{_pc['i']:03d}_{tag}.mp4")

def concat_pieces(parts,out):
    lst=out+".txt"
    with open(lst,"w",encoding="utf-8") as fp:
        for f,_ in parts: fp.write(f"file '{os.path.abspath(f)}'\n")   # abs: concat resolves relative to the list's dir
    D.run([FF,"-y","-f","concat","-safe","0","-i",lst,"-c","copy",out],out)

def build_footage(out,Dd):
    sl=take_slices(Dd); ins=[]; fc=""; n=len(sl)
    for k,(cid,ip,t) in enumerate(sl): ins+=["-ss",str(ip),"-t",str(round(t,3)),"-i",os.path.join(NORM,f"{cid}.mp4")]
    for k in range(n): fc+=f"[{k}:v][{k}:a]"
    fc+=f"concat=n={n}:v=1:a=1[v][a]"
    D.run([FF,"-y"]+ins+["-filter_complex",fc,"-map","[v]","-map","[a]","-t",str(round(Dd,3))]+ENC+[out],out)

def build_montage(out,Dd,ids):
    n=len(ids); each=round(Dd/n,3); parts=[]
    for j,pid in enumerate(ids):
        pf=npiece(f"ph{pid}"); kenburns(pf,D.ppath(c,pid),each,"in" if j%2==0 else "out"); parts.append((pf,each))
    concat_pieces(parts,out)

def build_nar_visual(out,seg,Dd):
    feats=SEGCFG[seg].get("feature",[]); parts=[]; used=0.0; fd=SEGCFG[seg].get("feature_dur",c["feature_dur"])
    for j,pid in enumerate(feats):
        if used+fd>Dd-5: break
        pf=npiece(f"ft{pid}"); kenburns(pf,D.ppath(c,pid),fd,"in" if j%2==0 else "out"); parts.append((pf,fd)); used+=fd
    ff=npiece(f"foot_{seg}"); build_footage(ff,round(Dd-used,3)); parts.append((ff,round(Dd-used,3)))
    concat_pieces(parts,out)

# ---------- assemble ----------
def assemble():
    layout=[]; t=0.0; narr=[]; caps=[]
    f=os.path.join(PIECES,"00_title.mp4"); title_card(f,c["title_dur"]); layout.append((f,c["title_dur"])); t+=c["title_dur"]
    idx=1
    for seg in ORDER:
        sc=SEGCFG[seg]
        if sc.get("chapter"):
            roman,title=sc["chapter"]; f=os.path.join(PIECES,f"{idx:02d}_card_{seg}.mp4"); idx+=1
            chapter_card(f,c["card_dur"],roman,title); layout.append((f,c["card_dur"])); t+=c["card_dur"]
        segd=SEG[seg]["dur"]; f=os.path.join(PIECES,f"{idx:02d}_nar_{seg}.mp4"); idx+=1
        build_nar_visual(f,seg,segd); narr.append((seg,t))
        for s in SEG[seg]["sentences"]: caps.append((t+s["start"],t+s["end"],s["text"]))
        layout.append((f,segd)); t+=segd
        il=sc.get("interlude",[]); ild=sc.get("interlude_dur",0)
        if il and ild>0:
            f=os.path.join(PIECES,f"{idx:02d}_int_{seg}.mp4"); idx+=1
            build_montage(f,ild,il); layout.append((f,ild)); t+=ild
    f=os.path.join(PIECES,"99_outro.mp4"); outro_card(f,c["outro_dur"]); layout.append((f,c["outro_dur"])); t+=c["outro_dur"]
    TOTAL=t; print(f"TOTAL {TOTAL:.1f}s = {TOTAL/60:.2f} min")
    with open("concat.txt","w",encoding="utf-8") as fp:
        for f,_ in layout: fp.write(f"file '{os.path.abspath(f)}'\n")
    D.run([FF,"-y","-f","concat","-safe","0","-i","concat.txt","-c","copy","video_only.mp4"],"video_only.mp4")
    build_narration(narr,TOTAL); write_srt(caps)
    print("assemble done -> build.py project.json final")

def build_narration(narr,total):
    with wave.open("seg_"+ORDER[0]+".wav",'rb') as w: rate,sw,ch=w.getframerate(),w.getsampwidth(),w.getnchannels()
    buf=bytearray(int(total*rate)*sw*ch)
    for seg,ab in narr:
        with wave.open(f"seg_{seg}.wav",'rb') as w: fr=w.readframes(w.getnframes())
        pos=int(ab*rate)*sw*ch; buf[pos:pos+len(fr)]=fr
    with wave.open("narr.wav",'wb') as w: w.setnchannels(ch);w.setsampwidth(sw);w.setframerate(rate);w.writeframes(bytes(buf))
    print("  narr.wav")

def ts(x):
    h=int(x//3600);m=int((x%3600)//60);s=x%60; return f"{h:02d}:{m:02d}:{s:06.3f}".replace('.',',')
def write_srt(caps):
    with open("captions.srt","w",encoding="utf-8") as f:
        for n,(a,b,txt) in enumerate(caps,1): f.write(f"{n}\n{ts(a)} --> {ts(b)}\n{txt}\n\n")
    print(f"  captions.srt ({len(caps)})")

# ---------- final ----------
def final():
    total=D.dur("video_only.mp4")
    amb=c.get("ambient_clips",POOL[:3])
    with open("amb.txt","w",encoding="utf-8") as fp:
        for cid in amb: fp.write(f"file '{os.path.abspath(os.path.join(NORM,cid+'.mp4'))}'\n")
    D.run([FF,"-y","-stream_loop","-1","-f","concat","-safe","0","-i","amb.txt","-t",f"{total:.3f}",
           "-vn","-af","highpass=f=80,dynaudnorm=f=200:g=14:p=0.9:m=18,aresample=48000","-ac","2","ambient.wav"],"ambient.wav")
    lvl=c.get("ambient_level",0.4)
    afc=(f"[0:a]volume={lvl}[amb];[1:a]aresample=48000,aformat=channel_layouts=stereo[nar];"
         "[nar]asplit=2[nk][nm];[amb][nk]sidechaincompress=threshold=0.02:ratio=16:attack=12:release=320[ambd];"
         "[ambd][nm]amix=inputs=2:duration=longest:normalize=0[mix];"
         f"[mix]alimiter=limit=0.95,atrim=0:{total:.3f}[aout]")
    D.run([FF,"-y","-i","ambient.wav","-i","narr.wav","-filter_complex",afc,"-map","[aout]","mix.wav"],"mix.wav")
    style=("FontName=%s,Fontsize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
           "BorderStyle=1,Outline=2,Shadow=1,MarginV=34,Alignment=2")%(c.get("caption_font","Arial"))
    D.run([FF,"-y","-i","video_only.mp4","-i","mix.wav","-vf",f"subtitles='captions.srt':force_style='{style}'",
           "-map","0:v","-map","1:a"]+ENC+[c["output"]],c["output"])
    print(f"\nOUTPUT: {c['output']}  ({D.dur(c['output'])/60:.2f} min)")

if __name__=="__main__":
    if phase in ("norm","all"): print("== normalize =="); normalize()
    if phase in ("assemble","all"): print("== assemble =="); assemble()
    if phase in ("final","all"): print("== final =="); final()
