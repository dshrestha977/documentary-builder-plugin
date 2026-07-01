"""Shared helpers. All phase scripts import this. Run everything from a SHORT working dir."""
import os, json, subprocess, sys

CWD = os.getcwd()
TOOLS = os.path.join(CWD, "tools")

def _paths():
    p = os.path.join(TOOLS, "paths.json")
    if not os.path.isfile(p):
        sys.exit("tools/paths.json missing -> run: python <skill>/scripts/setup.py")
    return json.load(open(p, encoding="utf-8-sig"))   # tolerate BOM

PATHS = _paths()
FF = PATHS["ffmpeg"]; FP = PATHS["ffprobe"]
FONT = "tools/font.ttf"; FONTB = "tools/fontb.ttf"   # relative to CWD (drawtext runs with cwd=CWD)

def load_cfg():
    if len(sys.argv) < 2:
        sys.exit("usage: <script> project.json [phase]")
    c = json.load(open(sys.argv[1], encoding="utf-8-sig"))   # tolerate BOM
    for k, v in {"width":1280,"height":720,"fps":30,"voice":"am_michael","speed":0.95,
                 "title_dur":6.0,"outro_dur":6.0,"card_dur":3.6,"feature_dur":5.5,
                 "output":"documentary.mp4"}.items():
        c.setdefault(k, v)
    return c

def enc(c):
    return ["-c:v","libx264","-preset","veryfast","-crf","21","-pix_fmt","yuv420p",
            "-r",str(c["fps"]),"-video_track_timescale","30000",
            "-c:a","aac","-b:a","160k","-ar","48000","-ac","2","-movflags","+faststart"]

def run(args, out=None):
    r = subprocess.run(args, capture_output=True, text=True, cwd=CWD)
    if r.returncode != 0:
        print("CMD FAILED:", " ".join(str(a) for a in args)[:280])
        print((r.stderr or "")[-1200:]); sys.exit(1)
    if out: print(f"  ok {os.path.basename(out):26s} {dur(out):7.2f}s")
    return r

def dur(p):
    r = subprocess.run([FP,"-v","error","-show_entries","format=duration","-of","csv=p=0",p],
                       capture_output=True, text=True)
    try: return float(r.stdout.strip())
    except: return 0.0

def mpath(c, rel): return os.path.join(c["media_dir"], rel)
def ppath(c, pid): return mpath(c, c["photos"][str(pid)])
