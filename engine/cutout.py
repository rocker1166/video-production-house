#!/usr/bin/env python3
"""Cross-platform subject lift. Same contract as the Vision `cutout` tool:  cutout.py <in.png|jpg> <out.png>
Writes a transparent PNG cropped to the subject. Needs `pip install -r requirements-seg.txt`."""
import sys
from PIL import Image
from rembg import new_session, remove

src, dst = sys.argv[1:3]
img = remove(Image.open(src).convert("RGB"), session=new_session("u2net_human_seg"))
box = img.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
if not box:
    sys.exit("no subject detected")
img.crop(box).save(dst)
print(f"ok {box[2]-box[0]}x{box[3]-box[1]}")
