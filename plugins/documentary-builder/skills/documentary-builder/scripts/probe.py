"""Probe clips listed in project.json -> footage.json (resolution, orientation, audio, duration)."""
import os, json, subprocess
import dvlib as D
c = D.load_cfg()

def probe(path):
    r = subprocess.run([D.FP,"-v","error","-print_format","json",
        "-show_entries","stream=codec_type,width,height:format=duration",
        "-show_entries","stream_side_data=rotation", path], capture_output=True, text=True)
    d = json.loads(r.stdout or "{}")
    v = next((s for s in d.get("streams",[]) if s.get("codec_type")=="video"), {})
    a = any(s.get("codec_type")=="audio" for s in d.get("streams",[]))
    rot = 0
    for s in d.get("streams",[]):
        for sd in s.get("side_data_list",[]):
            if "rotation" in sd: rot = sd["rotation"]
    w,h = v.get("width"), v.get("height")
    dw,dh = (h,w) if rot in (90,-90,270,-270) else (w,h)
    return {"w":w,"h":h,"dur":round(float(d.get("format",{}).get("duration",0) or 0),2),
            "audio":a,"orient":("portrait" if (dw and dh and dh>dw) else "landscape")}

out = {"clips":{}}
for cid, fn in c["clips"].items():
    p = D.mpath(c, fn)
    if not os.path.isfile(p):
        print("MISSING", cid, p); continue
    info = probe(p); info["path"] = p; out["clips"][cid] = info
    print(f"{cid:14s} {info['orient']:9s} {info['dur']:7.1f}s audio={info['audio']}")
json.dump(out, open("footage.json","w"), indent=1)
print("-> footage.json  (%d clips)" % len(out["clips"]))
