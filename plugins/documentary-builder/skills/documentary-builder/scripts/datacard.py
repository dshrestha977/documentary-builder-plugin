"""Lightweight animated data card (ffmpeg-only infographics — the OpenMontage strength, done locally).
Usage: python datacard.py project.json "54,330" "litres/day - Scheme A design demand" out.mp4 [seconds]
Produces an mp4 piece (big-number reveal + underline). Drop it into your timeline / concat list.
For richer motion-graphics (animated maps, charts), render segments with OpenMontage's Remotion
pipeline and concat them alongside build.py pieces."""
import os, sys
import dvlib as D

c = D.load_cfg()
big = sys.argv[2] if len(sys.argv) > 2 else "0"
sub = sys.argv[3] if len(sys.argv) > 3 else ""
out = sys.argv[4] if len(sys.argv) > 4 else "datacard.mp4"
d   = float(sys.argv[5]) if len(sys.argv) > 5 else 4.0
W,H,FPS = c["width"], c["height"], c["fps"]; ENC = D.enc(c); FF = D.FF
os.makedirs("pieces", exist_ok=True)
open("pieces/dc_big.txt","w",encoding="utf-8").write(big)
open("pieces/dc_sub.txt","w",encoding="utf-8").write(sub)
bg = c.get("datacard_bg", "0x0B1A2A")
vf = (f"format=yuv420p,"
      f"drawbox=x=(w-560)/2:y=(h/2)+70:w='min(560,(t/0.8)*560)':h=5:color=0xFFE08A:t=fill,"
      f"drawtext=fontfile='{D.FONTB}':textfile='pieces/dc_big.txt':fontcolor=white:fontsize=120:"
      f"x=(w-text_w)/2:y=(h/2)-130:alpha='if(lt(t,0.5),t/0.5,1)',"
      f"drawtext=fontfile='{D.FONT}':textfile='pieces/dc_sub.txt':fontcolor=0xCFE0F0:fontsize=30:"
      f"x=(w-text_w)/2:y=(h/2)+95:alpha='if(lt(t,0.9),0,min((t-0.9)/0.6,1))'")
D.run([FF,"-y","-f","lavfi","-i",f"color=c={bg}:s={W}x{H}:r={FPS}",
       "-f","lavfi","-i","anullsrc=r=48000:cl=stereo",
       "-vf",vf,"-map","0:v","-map","1:a","-t",str(d)]+ENC+[out], out)
print("->", out)
