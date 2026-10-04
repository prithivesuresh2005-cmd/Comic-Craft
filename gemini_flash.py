import json
import os
from google import genai

MODEL = os.getenv("GEMINI_FLASH_MODEL", "gemini-2.5-flash")

def fallback(character, setting):
    return [
        {"panel": 1, "title": "The Beginning", "image_prompt": f"{character} arrives in {setting}", "beat": "The adventure begins."},
        {"panel": 2, "title": "The Problem", "image_prompt": f"{character} faces a mysterious challenge in {setting}", "beat": "A problem suddenly appears."},
        {"panel": 3, "title": "The Discovery", "image_prompt": f"{character} discovers a secret in {setting}", "beat": "A hidden clue changes everything."},
        {"panel": 4, "title": "The Action", "image_prompt": f"{character} bravely acts in {setting}", "beat": "The hero takes action."},
        {"panel": 5, "title": "The Ending", "image_prompt": f"{character} celebrates after the adventure in {setting}", "beat": "The adventure ends with a memorable moment."},
    ]

def generate_outline(story_prompt, character_name, setting, tone, art_style):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return fallback(character_name, setting)
    try:
        client = genai.Client(api_key=key)
        prompt = f'''Create exactly 5 comic panels as JSON only.
Story: {story_prompt}
Character: {character_name}
Setting: {setting}
Tone: {tone}
Art style: {art_style}
Each object needs panel, title, image_prompt, beat. No markdown.'''
        text = client.models.generate_content(model=MODEL, contents=prompt).text.strip()
        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        if isinstance(data, list) and len(data) >= 5:
            return data[:5]
    except Exception:
        pass
    return fallback(character_name, setting)
