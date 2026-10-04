import json
import os
from google import genai

MODEL = os.getenv("GEMINI_PRO_MODEL", "gemini-2.5-pro")

def generate_story(outline, character_name, tone):
    fallback = [
        {"panel": p.get("panel", i+1), "narration": p.get("beat", ""), "dialogue": f"{character_name}: Let's do this!"}
        for i, p in enumerate(outline[:5])
    ]
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return fallback
    try:
        client = genai.Client(api_key=key)
        prompt = f'''Turn this outline into 5 short comic narration/dialogue pairs.
Character: {character_name}
Tone: {tone}
Outline: {json.dumps(outline)}
Return JSON array only with panel, narration, dialogue.'''
        text = client.models.generate_content(model=MODEL, contents=prompt).text.strip()
        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        if isinstance(data, list) and len(data) >= 5:
            return data[:5]
    except Exception:
        pass
    return fallback
