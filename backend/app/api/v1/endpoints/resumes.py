import os
import json
import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.tenant import get_current_tenant, TenantContext
from app.models.candidate import Candidate, Document, DocumentType
from app.models.student_profile import StudentProfile
from app.models.resume import Resume, ResumeAnalysis
from app.schemas.resume import ResumeResponse, ResumeAnalysisResponse, ApplyAnalysisRequest
from app.services.resume_service import (
    extract_text_from_file_bytes, parse_resume_text, calculate_resume_quality_score, calculate_profile_completeness
)
from app.api.v1.endpoints.profile import get_or_create_student_profile
from app.services.notification_service import create_notification

router = APIRouter()

RESUME_STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "static_uploads", "resumes")
os.makedirs(RESUME_STORAGE_DIR, exist_ok=True)

@router.get("", response_model=List[ResumeResponse], summary="List Resumes for Current Student")
def list_resumes(
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    candidate, _ = get_or_create_student_profile(db, ctx)
    resumes = db.query(Resume).filter(
        Resume.organization_id == ctx.organization.id,
        Resume.candidate_id == candidate.id
    ).order_by(Resume.id.desc()).all()

    output = []
    for r in resumes:
        strengths = json.loads(r.strengths_json) if r.strengths_json else []
        improvements = json.loads(r.improvements_json) if r.improvements_json else []
        output.append(ResumeResponse(
            id=r.id,
            candidate_id=r.candidate_id,
            file_name=r.file_name,
            file_type=r.file_type,
            file_url=r.file_url,
            file_size_bytes=r.file_size_bytes,
            is_current=r.is_current,
            quality_score=r.quality_score,
            strengths=strengths,
            improvements=improvements,
            created_at=r.created_at
        ))
    return output

@router.post("/upload", response_model=ResumeResponse, summary="Upload Resume & Execute Intelligence Analysis")
async def upload_resume(
    file: UploadFile = File(...),
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    original_filename = file.filename or "resume.pdf"
    ext = os.path.splitext(original_filename)[1].lower()
    content = await file.read()

    if not content or len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded. Please select a valid resume document.")

    if ext not in [".pdf", ".docx", ".txt"]:
        raise HTTPException(status_code=415, detail="Unsupported resume format. Upload PDF, DOCX, or TXT.")

    file_size_bytes = len(content)
    if file_size_bytes > 15 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Resume file is too large (max 15MB).")

    candidate, profile = get_or_create_student_profile(db, ctx)

    # Save physical file
    stored_token = f"resume_{candidate.id}_{uuid.uuid4().hex[:8]}{ext}"
    saved_path = os.path.join(RESUME_STORAGE_DIR, stored_token)
    with open(saved_path, "wb") as f:
        f.write(content)

    file_url = f"/static/resumes/{stored_token}"

    # Extract text & parse
    extracted_text = extract_text_from_file_bytes(content, original_filename)
    if not extracted_text or len(extracted_text.strip()) < 5:
        extracted_text = "Resume uploaded, but text could not be extracted. Please upload a text-readable PDF/DOCX/TXT file."

    parsed = parse_resume_text(extracted_text)
    quality = calculate_resume_quality_score(extracted_text, parsed)

    # Mark existing resumes as not current
    db.query(Resume).filter(
        Resume.organization_id == ctx.organization.id,
        Resume.candidate_id == candidate.id
    ).update({"is_current": False})

    # Create new Resume record
    resume = Resume(
        organization_id=ctx.organization.id,
        candidate_id=candidate.id,
        file_name=original_filename,
        file_type=file.content_type or ext,
        file_url=file_url,
        file_size_bytes=file_size_bytes,
        extracted_text=extracted_text,
        is_current=True,
        quality_score=quality["quality_score"],
        strengths_json=json.dumps(quality["strengths"]),
        improvements_json=json.dumps(quality["improvements"])
    )
    db.add(resume)
    db.flush()

    # Sync Candidate document & resume_url
    candidate.resume_url = file_url
    doc = Document(
        organization_id=ctx.organization.id,
        candidate_id=candidate.id,
        file_name=original_filename,
        file_type=file.content_type or ext,
        file_url=file_url,
        doc_type=DocumentType.RESUME
    )
    db.add(doc)

    # Create ResumeAnalysis record for user review ([Accept] [Edit] [Ignore])
    analysis = ResumeAnalysis(
        organization_id=ctx.organization.id,
        resume_id=resume.id,
        candidate_id=candidate.id,
        parsed_data_json=json.dumps(parsed),
        status="PENDING_REVIEW"
    )
    db.add(analysis)

    # Recalculate profile completeness
    comp_res = calculate_profile_completeness(candidate, profile)
    profile.completeness_score = comp_res["completeness_score"]

    db.commit()

    # Create Notification
    create_notification(
        db=db,
        organization_id=ctx.organization.id,
        user_id=ctx.user.id,
        title="Resume Analysis Completed",
        message=f"Analyzed '{original_filename}'. Resume Quality Score: {quality['quality_score']}/100.",
        notification_type="RESUME_ANALYZED",
        link_url="#/resume"
    )

    return ResumeResponse(
        id=resume.id,
        candidate_id=candidate.id,
        file_name=resume.file_name,
        file_type=resume.file_type,
        file_url=resume.file_url,
        file_size_bytes=resume.file_size_bytes,
        is_current=resume.is_current,
        quality_score=resume.quality_score,
        strengths=quality["strengths"],
        improvements=quality["improvements"],
        created_at=resume.created_at
    )

@router.get("/{id}/analysis", response_model=ResumeAnalysisResponse, summary="Get Resume Parsing Intelligence Analysis")
def get_resume_analysis(
    id: int,
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    analysis = db.query(ResumeAnalysis).filter(
        ResumeAnalysis.organization_id == ctx.organization.id,
        ResumeAnalysis.resume_id == id
    ).first()

    if not analysis:
        raise HTTPException(status_code=404, detail="Resume analysis not found.")

    return ResumeAnalysisResponse(
        id=analysis.id,
        resume_id=analysis.resume_id,
        candidate_id=analysis.candidate_id,
        parsed_data=json.loads(analysis.parsed_data_json),
        status=analysis.status,
        created_at=analysis.created_at
    )

@router.post("/{id}/apply-analysis", summary="Accept/Apply Resume Extracted Data to Student Profile")
def apply_resume_analysis(
    id: int,
    req: ApplyAnalysisRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    analysis = db.query(ResumeAnalysis).filter(
        ResumeAnalysis.organization_id == ctx.organization.id,
        ResumeAnalysis.resume_id == id
    ).first()

    if not analysis:
        raise HTTPException(status_code=404, detail="Resume analysis not found.")

    candidate, profile = get_or_create_student_profile(db, ctx)
    parsed = json.loads(analysis.parsed_data_json)
    accepted = req.accept_fields

    if "phone" in accepted and parsed.get("phone"):
        candidate.phone = parsed["phone"]
        ctx.user.phone = parsed["phone"]

    if "skills" in accepted and parsed.get("skills"):
        skills_str = ", ".join(parsed["skills"])
        if candidate.primary_skills:
            candidate.primary_skills = f"{candidate.primary_skills}, {skills_str}"
        else:
            candidate.primary_skills = skills_str

    if "linkedin_url" in accepted and parsed.get("linkedin_url"):
        profile.linkedin_url = parsed["linkedin_url"]

    if "github_url" in accepted and parsed.get("github_url"):
        profile.github_url = parsed["github_url"]

    if "education" in accepted and parsed.get("education"):
        profile.degree = parsed["education"][0]
        profile.highest_qualification = parsed["education"][0]

    analysis.status = "ACCEPTED"
    comp_res = calculate_profile_completeness(candidate, profile)
    profile.completeness_score = comp_res["completeness_score"]

    db.commit()

    return {"message": f"Successfully applied detected information ({', '.join(accepted)}) to your profile."}
