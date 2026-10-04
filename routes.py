from pathlib import Path
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from .gemini_flash import generate_outline
from .gemini_pro import generate_story
from .image_generator import generate_image
from .layout_builder import build_comic_layout
from .exporters import save_pdf
from .video_builder import build_motion_video

load_dotenv()
router = APIRouter()
templates = Jinja2Templates(directory="templates")

class PromptRequest(BaseModel):
    story_prompt: str = Field(min_length=3, max_length=2000)
    character_name: str = Field(min_length=1, max_length=100)
    setting: str = Field(min_length=1, max_length=150)
    tone: str = Field(min_length=1, max_length=50)
    art_style: str = Field(min_length=1, max_length=100)

def create_comic(data):
    outline = generate_outline(
        data.story_prompt, data.character_name, data.setting,
        data.tone, data.art_style
    )
    story = generate_story(outline, data.character_name, data.tone)

    images = [
        generate_image(
            f"{p.get('image_prompt', '')}, {data.art_style} comic illustration, "
            "consistent character design, cinematic composition, no text",
            scene_index=i,
        )
        for i, p in enumerate(outline[:5])
    ]

    layout = build_comic_layout(outline, story, images)
    pdf_path = save_pdf(layout)
    return layout, pdf_path

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request},
    )

@router.post("/generate", response_class=HTMLResponse)
async def generate(
    request: Request,
    story_prompt: str = Form(...),
    character_name: str = Form(...),
    setting: str = Form(...),
    tone: str = Form(...),
    art_style: str = Form(...),
):
    try:
        data = PromptRequest(
            story_prompt=story_prompt,
            character_name=character_name,
            setting=setting,
            tone=tone,
            art_style=art_style,
        )

        layout, pdf_path = create_comic(data)

        # IMPORTANT: create the actual MP4 motion-comic here.
        video_path = build_motion_video(layout)

        return templates.TemplateResponse(
            request=request,
            name="comic_preview.html",
            context={
                "request": request,
                "layout": layout,
                "pdf_url": "/" + str(pdf_path).replace("\\", "/"),
                "video_url": "/" + str(video_path).replace("\\", "/"),
            },
        )

    except Exception as exc:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"request": request, "error": str(exc)},
            status_code=500,
        )

@router.post("/generate-comic/json")
async def generate_comic_json(data: PromptRequest):
    try:
        layout, pdf_path = create_comic(data)
        video_path = build_motion_video(layout)
        return JSONResponse({
            "success": True,
            "panels": layout,
            "pdf_path": "/" + str(pdf_path).replace("\\", "/"),
            "video_path": "/" + str(video_path).replace("\\", "/"),
        })
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.get("/test-image")
async def test_image(prompt: str = "A brave fox exploring an enchanted forest, anime comic art"):
    path = generate_image(prompt)
    return {"success": True, "image_path": "/" + str(path).replace("\\", "/")}

@router.get("/export/{filename}")
async def export_file(filename: str):
    safe = Path(filename).name
    path = Path("static/exports") / safe
    if not path.exists():
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(path, media_type="application/pdf", filename=safe)

@router.get("/video/{filename}")
async def video_file(filename: str):
    safe = Path(filename).name
    path = Path("static/videos") / safe
    if not path.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(path, media_type="video/mp4", filename=safe)
