"""
utils/resume_builder.py
------------------------
Generates a professionally formatted PDF resume using ReportLab.
Takes structured user data and returns PDF bytes for download.
"""

import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

# ─── Color Palette ────────────────────────────────────────────────────────────
PRIMARY    = colors.HexColor("#1a365d")   # Dark navy
ACCENT     = colors.HexColor("#2b6cb0")   # Medium blue
LIGHT_GRAY = colors.HexColor("#f7fafc")
TEXT_DARK  = colors.HexColor("#1a202c")
DIVIDER    = colors.HexColor("#bee3f8")


def build_resume_pdf(data: dict) -> bytes:
    """
    Generate a complete PDF resume from structured data.
    
    Args:
        data: ResumeBuildRequest dict with name, education, skills, etc.
    
    Returns:
        PDF file as bytes (ready to return as HTTP response)
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )
    
    # ─── Styles ───────────────────────────────────────────────────────────────
    styles = getSampleStyleSheet()
    
    name_style = ParagraphStyle(
        "NameStyle", parent=styles["Title"],
        fontSize=22, textColor=PRIMARY, spaceAfter=2,
        alignment=TA_CENTER, fontName="Helvetica-Bold"
    )
    contact_style = ParagraphStyle(
        "ContactStyle", fontSize=9, textColor=ACCENT,
        alignment=TA_CENTER, spaceAfter=6
    )
    section_header_style = ParagraphStyle(
        "SectionHeader", fontSize=11, textColor=PRIMARY,
        fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=2
    )
    body_style = ParagraphStyle(
        "Body", fontSize=9, textColor=TEXT_DARK,
        leading=14, spaceAfter=2
    )
    bullet_style = ParagraphStyle(
        "Bullet", fontSize=9, textColor=TEXT_DARK,
        leftIndent=12, leading=13, spaceAfter=1,
        bulletIndent=4
    )
    sub_style = ParagraphStyle(
        "Sub", fontSize=9, textColor=ACCENT,
        fontName="Helvetica-Bold", spaceAfter=1
    )

    story = []

    # ─── Header: Name ─────────────────────────────────────────────────────────
    story.append(Paragraph(data["name"].upper(), name_style))

    # ─── Contact Line ─────────────────────────────────────────────────────────
    contact_parts = [data.get("email", ""), data.get("phone", "")]
    if data.get("linkedin"):
        contact_parts.append(f"linkedin.com/in/{data['linkedin']}")
    if data.get("github"):
        contact_parts.append(f"github.com/{data['github']}")
    story.append(Paragraph("  |  ".join(filter(None, contact_parts)), contact_style))

    def section_divider(title: str):
        story.append(Paragraph(title.upper(), section_header_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceAfter=4))

    # ─── Education ────────────────────────────────────────────────────────────
    section_divider("Education")
    for edu in data.get("education", []):
        story.append(Paragraph(f"<b>{edu['degree']}</b> — {edu['institution']} ({edu['year']})" +
                               (f" | CGPA: {edu['cgpa']}" if edu.get("cgpa") else ""), body_style))

    # ─── Skills ───────────────────────────────────────────────────────────────
    section_divider("Technical Skills")
    skills_text = " &nbsp;·&nbsp; ".join(data.get("skills", []))
    story.append(Paragraph(skills_text, body_style))

    # ─── Projects ─────────────────────────────────────────────────────────────
    if data.get("projects"):
        section_divider("Projects")
        for proj in data["projects"]:
            story.append(Paragraph(f"<b>{proj['title']}</b> <font color='#718096'>| {proj['technologies']}</font>", sub_style))
            story.append(Paragraph(f"• {proj['description']}", bullet_style))

    # ─── Internships ─────────────────────────────────────────────────────────
    if data.get("internships"):
        section_divider("Internships")
        for intern in data["internships"]:
            story.append(Paragraph(
                f"<b>{intern['role']}</b> @ {intern['company']} <font color='#718096'>({intern['duration']})</font>", sub_style))
            story.append(Paragraph(f"• {intern['description']}", bullet_style))

    # ─── Achievements ─────────────────────────────────────────────────────────
    if data.get("achievements"):
        section_divider("Achievements")
        for ach in data["achievements"]:
            story.append(Paragraph(f"• {ach}", bullet_style))

    # ─── Certifications ───────────────────────────────────────────────────────
    if data.get("certifications"):
        section_divider("Certifications")
        for cert in data["certifications"]:
            story.append(Paragraph(f"• {cert}", bullet_style))

    # ─── Build PDF ────────────────────────────────────────────────────────────
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
