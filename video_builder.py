from pathlib import Path
import uuid
import textwrap
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio.v2 as imageio

FPS = 12
PANEL_SECONDS = 3.4
CROSSFADE_SECONDS = 0.50
SIZE = (1280, 720)

FONT = "/usr/share/fonts/truetype/lato/Lato-Medium.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/lato/Lato-Heavy.ttf"


def _font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _load_panel(path):
    p = Path(path)
    if not p.exists():
        return Image.new("RGB", SIZE, "#111827")
    return Image.open(p).convert("RGB").resize(SIZE, Image.Resampling.LANCZOS)


def _motion(frame, t, panel_index):
    # Gentle movie-like camera movement rather than realistic video motion.
    zoom = 1.0 + 0.055 * t
    w, h = SIZE
    cw, ch = int(w / zoom), int(h / zoom)
    cx = int((w - cw) * (0.35 + 0.12 * np.sin(t * np.pi + panel_index)))
    cy = int((h - ch) * (0.45 + 0.05 * np.sin(t * np.pi)))
    cx = max(0, min(cx, w - cw))
    cy = max(0, min(cy, h - ch))
    return frame.crop((cx, cy, cx + cw, cy + ch)).resize(SIZE, Image.Resampling.LANCZOS)


def _draw_words(base, text, t, panel_index):
    """Bottom movie-style narration: soft glass panel + fade/slide/type-on feel."""
    if not text:
        return base
    text = " ".join(str(text).split())
    if not text:
        return base

    # Type-on effect, then keep the full sentence visible.
    reveal = min(1.0, max(0.0, (t - 0.10) / 0.75))
    chars = max(1, int(len(text) * reveal))
    visible = text[:chars]

    # Split long text into two cinematic lines.
    lines = textwrap.wrap(visible, width=62)[:2]
    if not lines:
        return base

    overlay = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = _font(FONT_BOLD, 32)
    small = _font(FONT, 18)

    # Fade/slide in from slightly below.
    alpha = int(235 * min(1.0, max(0.0, (t - 0.02) / 0.35)))
    slide = int(22 * (1.0 - min(1.0, max(0.0, t / 0.35))))
    box_h = 92 if len(lines) == 1 else 122
    y2 = SIZE[1] - 28 + slide
    y1 = y2 - box_h

    # Subtle cinematic vignette behind words.
    panel = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    pd.rounded_rectangle((70, y1, SIZE[0] - 70, y2), radius=24,
                         fill=(8, 10, 18, int(alpha * 0.72)),
                         outline=(255, 255, 255, int(alpha * 0.20)), width=1)
    panel = panel.filter(ImageFilter.GaussianBlur(0.2))
    overlay.alpha_composite(panel)

    # Tiny scene marker.
    draw = ImageDraw.Draw(overlay)
    draw.text((95, y1 + 13), f"SCENE {panel_index + 1:02d}", font=small,
              fill=(255, 255, 255, int(alpha * 0.55)))

    text_y = y1 + 34
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (SIZE[0] - tw) // 2
        # Soft shadow makes the words feel like a film subtitle.
        draw.text((x + 2, text_y + 2), line, font=font, fill=(0, 0, 0, int(alpha * 0.9)))
        draw.text((x, text_y), line, font=font, fill=(255, 255, 255, alpha))
        text_y += 38

    return Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")


def _wind_motion(base, t, panel_index):
    """Adds subtle drifting leaves/dust to sell a living, breezy background."""
    overlay = Image.new("RGBA", SIZE, (0,0,0,0))
    d = ImageDraw.Draw(overlay)
    for k in range(22):
        phase = k * 0.71 + panel_index * 0.43
        x = int((k * 71 + 90 * t * (1 + (k % 3) * 0.25) + 50*np.sin(t*2+phase)) % SIZE[0])
        y = int(125 + ((k * 43 + 260 * t + 35*np.sin(t*2.5+phase)) % 420))
        r = 2 + (k % 3)
        d.ellipse((x, y, x+r*3, y+r*2), fill=(190, 220, 150, 95))
    return Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")


def build_motion_video(layout):
    out_dir = Path("static/videos")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"comic_motion_{uuid.uuid4().hex}.mp4"

    panels = []
    captions = []
    for item in layout:
        raw = item.get("image_path") or item.get("image") or ""
        raw = str(raw).lstrip("/")
        panels.append(_load_panel(raw))
        narration = item.get("narration", "") or ""
        dialogue = item.get("dialogue", "") or ""
        caption = narration.strip() if narration.strip() else dialogue.strip()
        captions.append(caption)

    if not panels:
        panels = [Image.new("RGB", SIZE, "#111827")]
        captions = [""]

    panel_frames = max(1, int(PANEL_SECONDS * FPS))
    fade_frames = max(1, int(CROSSFADE_SECONDS * FPS))

    writer = imageio.get_writer(
        str(out_path), fps=FPS, codec="libx264", pixelformat="yuv420p", quality=7
    )
    try:
        for i, panel in enumerate(panels):
            for n in range(panel_frames):
                t = n / max(1, panel_frames - 1)
                frame = _motion(panel, t, i)
                frame = _wind_motion(frame, t, i)
                frame = _draw_words(frame, captions[i] if i < len(captions) else "", t, i)
                writer.append_data(np.asarray(frame))

            if i < len(panels) - 1:
                nxt = panels[i + 1]
                for n in range(1, fade_frames + 1):
                    a = n / fade_frames
                    cur = np.asarray(_motion(panel, 1.0, i), dtype=np.float32)
                    new = np.asarray(_motion(nxt, 0.0, i + 1), dtype=np.float32)
                    mixed = Image.fromarray(np.asarray(cur * (1 - a) + new * a, dtype=np.uint8))
                    mixed = _wind_motion(mixed, a, i + 1)
                    # During the transition, keep the next scene's words beginning softly.
                    mixed = _draw_words(mixed, captions[i + 1] if i + 1 < len(captions) else "", a, i + 1)
                    writer.append_data(np.asarray(mixed))
    finally:
        writer.close()

    return out_path
