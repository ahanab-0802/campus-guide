"""
routes/resume.py
----------------
Endpoints for:
  POST /resume/build   - Generate PDF from form data
  POST /resume/analyze - Upload PDF and get full ML analysis
"""

import io
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, ResumeMetadata
from app.schemas.schemas import ResumeBuildRequest, FullAnalysisResponse
from app.utils.auth import get_current_user_email
from app.utils.resume_parser import parse_resume
from app.utils.resume_builder import build_resume_pdf
from app.services.ats_scorer import calculate_ats_score
from app.services.ml_predictor import (
    predict_shortlisting,
    predict_job_role,
    predict_salary,
    predict_company_type,
    get_improvement_suggestions
)

router = APIRouter(prefix="/resume", tags=["Resume"])


@router.post("/build")
def build_resume(
    payload: ResumeBuildRequest,
    email: str = Depends(get_current_user_email)
):
    """
    Build and return a formatted PDF resume.
    
    Accepts structured JSON (name, education, skills, projects, etc.)
    Returns a downloadable PDF file.
    """
    try:
        pdf_bytes = build_resume_pdf(payload.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

    filename = f"{payload.name.replace(' ', '_')}_Resume.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.post("/analyze", response_model=FullAnalysisResponse)
async def analyze_resume(
    file: UploadFile = File(...),
    email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db)
):
    """
    Full resume analysis pipeline:
    
    1. Extract text from uploaded PDF
    2. Parse features (skills, sections, etc.)
    3. Calculate ATS score
    4. Predict shortlisting (XGBoost)
    5. If shortlisted: predict job role (SVM), salary & company (RF)
    6. If not shortlisted: return improvement suggestions
    7. Save metadata to database
    
    Returns: FullAnalysisResponse JSON
    """
    # ── Validate file type ────────────────────────────────────────────────────
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:   # 10 MB limit
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit.")

    # ── Step 1-2: Parse resume ────────────────────────────────────────────────
    parsed = parse_resume(file_bytes)
    if not parsed["raw_text"]:
        raise HTTPException(status_code=422, detail="Could not extract text from PDF. Ensure it's not a scanned image.")

    # ── Step 3: ATS Score ─────────────────────────────────────────────────────
    ats_result  = calculate_ats_score(parsed)
    ats_score   = ats_result["ats_score"]

    # ── Step 4: Shortlisting prediction ──────────────────────────────────────
    shortlisted, confidence = predict_shortlisting(parsed)

    # ── Step 5 or 6: Conditional predictions ─────────────────────────────────
    result = {
        "ats_score":   ats_score,
        "shortlisted": shortlisted,
        "confidence":  confidence,
    }

    if shortlisted:
        result["job_role"]          = predict_job_role(parsed)
        result["salary_prediction"] = predict_salary(parsed)
        result["company_type"]      = predict_company_type(parsed)
    else:
        improvements = get_improvement_suggestions(parsed, ats_score)
        result["suggestions"]     = improvements["suggestions"]
        result["missing_keywords"] = improvements["missing_keywords"]

    # ── Step 7: Save to DB ────────────────────────────────────────────────────
    user = db.query(User).filter(User.email == email).first()
    if user:
        meta = ResumeMetadata(
            user_id      = user.id,
            filename     = file.filename,
            ats_score    = ats_score,
            shortlisted  = shortlisted,
            job_role     = result.get("job_role"),
            salary       = result.get("salary_prediction"),
            company_type = result.get("company_type"),
        )
        db.add(meta)
        db.commit()

    return result


@router.get("/history")
def get_resume_history(
    email: str = Depends(get_current_user_email),
    db: Session = Depends(get_db)
):
    """Return the authenticated user's resume analysis history."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    records = db.query(ResumeMetadata).filter(ResumeMetadata.user_id == user.id).all()
    return [
        {
            "id":           r.id,
            "filename":     r.filename,
            "ats_score":    r.ats_score,
            "shortlisted":  r.shortlisted,
            "job_role":     r.job_role,
            "salary":       r.salary,
            "company_type": r.company_type,
            "uploaded_at":  r.uploaded_at,
        }
        for r in records
    ]
