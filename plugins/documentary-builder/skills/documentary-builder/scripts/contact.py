"""Build contact sheets of every photo in media_dir so you can curate (view PNGs, note ids).
Writes contact/contact_*.png (each cell labelled with its id) + photo_index.json (id -> path)."""
import os, json
from PIL import Image, ImageDraw, ImageFont
import dvlib as D

c = D.load_cfg()
SRC = c["media_dir"]; OUT = "contact"; os.makedirs(OUT, exist_ok=True)
exts = (".jpg",".jpeg",".png")
skip = c.get("contact_skip", ["(1)","(2)","(3)"])   # WhatsApp duplicate copies

paths=[]
for root,_,files in os.walk(SRC):
    for f in files:
        if f.lower().endswith(exts) and not any(s in f for s in skip):
            paths.append(os.path.join(root,f))
paths.sort()
print("photos:", len(paths))

TW,TH=360,202; COLS,ROWS=6,5; PER=COLS*ROWS; PAD=4; LBL=22
cw,ch=TW+PAD,TH+PAD+LBL
try: font=ImageFont.truetype(D.PATHS["font"],20)
except Exception: font=ImageFont.load_default()
idx={}; page=None; draw=None; pages=0
for i,p in enumerate(paths):
    cell=i%PER
    if cell==0:
        if page: page.save(os.path.join(OUT,f"contact_{pages:02d}.png")); pages+=1
        page=Image.new("RGB",(cw*COLS,ch*ROWS),(20,20,20)); draw=ImageDraw.Draw(page)
    r,col=divmod(cell,COLS); x=col*cw; y=r*ch
    try:
        im=Image.open(p); im.thumbnail((TW,TH)); cv=Image.new("RGB",(TW,TH),(0,0,0))
        cv.paste(im,((TW-im.width)//2,(TH-im.height)//2)); page.paste(cv,(x+PAD//2,y+LBL))
    except Exception:
        draw.text((x+4,y+LBL+80),"ERR",fill=(255,80,80),font=font)
    draw.rectangle([x,y,x+40,y+LBL],fill=(0,0,0)); draw.text((x+3,y+1),str(i),fill=(255,220,120),font=font)
    idx[i]=p
if page: page.save(os.path.join(OUT,f"contact_{pages:02d}.png")); pages+=1
json.dump(idx,open("photo_index.json","w"),indent=1)
print(f"wrote {pages} sheets -> {OUT}/  and photo_index.json")
print("Curate: view the PNGs, then put chosen ids/paths into project.json 'photos' + segment feature/interlude.")
