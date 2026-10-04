def build_comic_layout(outline, story, images):
    result = []
    for i, panel in enumerate(outline[:5]):
        s = story[i] if i < len(story) else {}
        result.append({
            "panel": panel.get("panel", i + 1),
            "title": panel.get("title", f"Panel {i+1}"),
            "image": "/" + str(images[i]).replace("\\", "/").lstrip("/"),
            "narration": s.get("narration", panel.get("beat", "")),
            "dialogue": s.get("dialogue", ""),
        })
    return result
