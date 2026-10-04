from pathlib import Path
import uuid
import requests
from PIL import Image, ImageDraw, ImageFont
import io
import os
import math


def _font(size):
    for name in ["arial.ttf", "DejaVuSans.ttf"]:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    return ImageFont.load_default()


def _illustrated_scene(prompt: str, out_path: Path, scene_index: int = 0):
    """Offline fallback: creates a real illustrated comic scene instead of a text placeholder."""
    W, H = 1280, 720
    img = Image.new("RGB", (W, H), (24, 30, 55))
    d = ImageDraw.Draw(img)
    p = (prompt or "").lower()

    # Different cinematic environments for each panel.
    palettes = [
        ((18, 38, 65), (54, 111, 83), (242, 196, 115)),
        ((30, 27, 67), (74, 55, 113), (247, 187, 103)),
        ((19, 55, 52), (41, 113, 83), (238, 205, 116)),
        ((54, 30, 58), (105, 58, 91), (255, 180, 112)),
        ((21, 40, 63), (39, 86, 117), (245, 211, 126)),
    ]
    sky, ground, light = palettes[scene_index % len(palettes)]

    # Sky gradient bands.
    for y in range(H):
        t = y / H
        c = tuple(int(sky[i] * (1-t) + ground[i] * t) for i in range(3))
        d.line((0, y, W, y), fill=c)

    # Moon/sun glow.
    cx, cy = 1010, 125
    for r in range(105, 20, -8):
        alpha = int(12 + (105-r) * 0.35)
        col = tuple(min(255, int(light[i] * (0.72 + alpha/255))) for i in range(3))
        d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=col)
    d.ellipse((970, 85, 1050, 165), fill=light)

    # Distant mountains / castle.
    d.polygon([(0,430),(180,260),(350,420),(520,245),(760,430),(930,270),(1280,430),(1280,720),(0,720)], fill=(24,45,58))
    if "castle" in p or scene_index in (1, 4):
        bx, by = 770, 290
        d.rectangle((bx, by, bx+230, 475), fill=(64,55,83))
        for tx in [bx-35, bx+80, bx+195]:
            d.rectangle((tx, by-95, tx+65, by+35), fill=(76,64,96))
            d.polygon([(tx-10,by-95),(tx+32,by-145),(tx+75,by-95)], fill=(42,35,63))
            d.rectangle((tx+22, by-45, tx+43, by-5), fill=light)
        d.ellipse((bx+95, by+70, bx+135, by+110), fill=light)

    # Forest trees.
    for x in range(-40, W+80, 110):
        h = 180 + ((x*7 + scene_index*53) % 100)
        base = 620
        trunk = (47, 36, 32)
        d.rectangle((x+38, base-h//2, x+58, base), fill=trunk)
        green = (24 + (x%25), 78 + ((x//10)%25), 62 + ((x//7)%20))
        for yy in range(base-h, base, 55):
            d.polygon([(x+48,yy-70),(x-15,yy+35),(x+111,yy+35)], fill=green)

    # Ground path.
    d.polygon([(470,720),(590,470),(700,470),(900,720)], fill=(116, 83, 62))
    d.line([(520,720),(620,490),(675,490),(830,720)], fill=(161,118,78), width=8)

    # Consistent main character: stylized young adventurer.
    bobx = 610 + int(18*math.sin(scene_index*1.2))
    body_y = 500
    skin = (235, 180, 145)
    hair = (46, 29, 36)
    coat = (92, 74, 170)
    shirt = (242, 218, 181)
    # legs
    d.rounded_rectangle((bobx-43, body_y+95, bobx-5, body_y+190), 14, fill=(31,42,70))
    d.rounded_rectangle((bobx+5, body_y+95, bobx+43, body_y+190), 14, fill=(31,42,70))
    # body + arms
    d.rounded_rectangle((bobx-62, body_y-5, bobx+62, body_y+120), 28, fill=coat)
    d.line((bobx-50,body_y+20,bobx-105,body_y+78), fill=skin, width=24)
    d.line((bobx+50,body_y+20,bobx+105,body_y-15), fill=skin, width=24)
    # head/hair
    d.ellipse((bobx-52, body_y-92, bobx+52, body_y+10), fill=skin)
    d.pieslice((bobx-57,body_y-105,bobx+57,body_y+12),180,355,fill=hair)
    d.polygon([(bobx-50,body_y-55),(bobx-82,body_y-5),(bobx-45,body_y-18)], fill=hair)
    d.polygon([(bobx+45,body_y-60),(bobx+80,body_y-8),(bobx+42,body_y-20)], fill=hair)
    # eyes
    d.ellipse((bobx-24,body_y-45,bobx-10,body_y-31), fill=(20,25,35))
    d.ellipse((bobx+10,body_y-45,bobx+24,body_y-31), fill=(20,25,35))
    d.arc((bobx-17,body_y-20,bobx+17,body_y+3), 10, 170, fill=(90,45,55), width=3)

    # Scene-specific prop/action.
    if scene_index == 0:
        d.ellipse((bobx+80, body_y-70, bobx+160, body_y+10), outline=light, width=6)
        d.ellipse((bobx+97, body_y-53, bobx+143, body_y-7), fill=light)
    elif scene_index == 1:
        d.line((bobx+95,body_y-10,bobx+175,body_y-110), fill=light, width=9)
        d.ellipse((bobx+158,body_y-128,bobx+190,body_y-96), fill=light)
    elif scene_index == 2:
        for k in range(5):
            x=430+k*55; y=350+int(18*math.sin(k))
            d.ellipse((x,y,x+26,y+26), fill=(238,210,121))
    elif scene_index == 3:
        d.rectangle((bobx+95, body_y-80, bobx+190, body_y+10), outline=light, width=6)
        d.line((bobx+105,body_y-60,bobx+180,body_y-10), fill=light, width=4)
    else:
        d.ellipse((bobx+105, body_y-55, bobx+170, body_y+10), fill=(236,190,94), outline=light, width=5)

    # Cinematic vignette and tiny panel label.
    overlay = Image.new("RGBA", (W,H), (0,0,0,0))
    od = ImageDraw.Draw(overlay)
    for r in range(160, 0, -20):
        alpha = int(30 * (1-r/160))
        od.rectangle((0,0,W,H), outline=(0,0,0,alpha), width=20)
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    # Soft atmospheric grain/highlights so the fallback feels like an animated-film frame
    # rather than a flat diagram.
    pix = img.load()
    for yy in range(0, H, 6):
        for xx in range(0, W, 6):
            r, g, b = pix[xx, yy]
            delta = int(5 * math.sin(xx * 0.017 + yy * 0.013 + scene_index))
            pix[xx, yy] = (max(0,min(255,r+delta)), max(0,min(255,g+delta)), max(0,min(255,b+delta)))

    # Wind-blown leaf accents (also echoed by the video motion layer).
    leaf = ImageDraw.Draw(img, "RGBA")
    for k in range(24):
        x = (k * 83 + scene_index * 47) % W
        y = 120 + ((k * 47 + scene_index * 71) % 420)
        leaf.ellipse((x, y, x+9, y+5), fill=(125, 170, 105, 115))

    img.save(out_path, format="PNG", optimize=True)


def generate_image(prompt: str, filename: str | None = None, scene_index: int = 0):
    out_dir = Path("static/panels")
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = filename or f"panel_{uuid.uuid4().hex}.png"
    out_path = out_dir / filename

    token = os.getenv("HF_TOKEN")
    model = os.getenv("HF_MODEL", "stabilityai/stable-diffusion-xl-base-1.0")
    if token:
        try:
            url = f"https://api-inference.huggingface.co/models/{model}"
            response = requests.post(
                url,
                headers={"Authorization": f"Bearer {token}"},
                json={"inputs": (
                    "cinematic semi-realistic 2D animated film frame, stylized human character, "
                    "natural facial proportions, expressive eyes, detailed hair and clothing, "
                    "soft skin shading, painterly background, realistic lighting but clearly animated, "
                    "subtle depth of field, wind-blown leaves and trees, polished feature-film animation, "
                    "consistent character design, no text, no watermark. Scene: " + str(prompt)
                )},
                timeout=120,
            )
            response.raise_for_status()
            Image.open(io.BytesIO(response.content)).convert("RGB").resize((1280, 720), Image.Resampling.LANCZOS).save(out_path, "PNG")
            return str(out_path).replace("\\", "/")
        except Exception:
            pass

    # No API key? Still create a proper illustrated scene, never a text placeholder.
    _illustrated_scene(prompt, out_path, scene_index)
    return str(out_path).replace("\\", "/")
