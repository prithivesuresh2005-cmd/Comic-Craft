from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import uuid

OUT = Path("static/exports")
OUT.mkdir(parents=True, exist_ok=True)

def save_pdf(layout):
    path = OUT / f"comic_{uuid.uuid4().hex[:10]}.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    for p in layout:
        story += [
            Paragraph(str(p["title"]), styles["Heading2"]),
            Paragraph(str(p["narration"]), styles["BodyText"]),
            Paragraph(str(p["dialogue"]), styles["BodyText"]),
            Spacer(1, 14),
        ]
    doc.build(story)
    return str(path).replace("\\", "/")
