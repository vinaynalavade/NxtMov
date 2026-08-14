import json
from typing import Dict, Any, List, Optional
from app.models.candidate import Candidate
from app.models.requirement import JobRequirement, WorkMode
from app.models.student_profile import StudentProfile

def extract_skills_set(cand: Candidate, profile: Optional[StudentProfile] = None) -> set[str]:
    raw_skills = []
    if cand.primary_skills:
        raw_skills.extend([s.strip().lower() for s in cand.primary_skills.replace(",", ";").split(";") if s.strip()])
    if cand.secondary_skills:
        raw_skills.extend([s.strip().lower() for s in cand.secondary_skills.replace(",", ";").split(";") if s.strip()])
    if cand.skills:
        raw_skills.extend([s.strip().lower() for s in cand.skills.replace(",", ";").split(";") if s.strip()])

    if profile:
        for text_field in [profile.programming_languages, profile.frameworks, profile.testing_tools, profile.databases, profile.cloud_technologies]:
            if text_field:
                raw_skills.extend([s.strip().lower() for s in text_field.replace(",", ";").split(";") if s.strip()])

    return set(raw_skills)

def calculate_match_score(cand: Candidate, req: JobRequirement, profile: Optional[StudentProfile] = None) -> Dict[str, Any]:
    # Candidate skills
    cand_skills = extract_skills_set(cand, profile)

    # Job requirement skills
    req_skills_raw = []
    if req.skills_req:
        req_skills_raw = [s.strip().lower() for s in req.skills_req.replace(",", ";").split(";") if s.strip()]
    
    # 1. Skills Scoring (40% Weight)
    matched_skills = []
    partial_skills = []
    missing_skills = []

    if req_skills_raw:
        for r_skill in req_skills_raw:
            if r_skill in cand_skills:
                matched_skills.append(r_skill.title())
            elif any(c_skill in r_skill or r_skill in c_skill for c_skill in cand_skills):
                partial_skills.append(r_skill.title())
            else:
                missing_skills.append(r_skill.title())
        
        match_ratio = (len(matched_skills) + 0.5 * len(partial_skills)) / len(req_skills_raw)
        skills_score = min(100.0, match_ratio * 100.0)
    else:
        skills_score = 75.0  # Default baseline if requirement specifies no specific skills

    # 2. Experience Scoring (25% Weight)
    cand_exp = float(cand.experience_years or 0.0)
    min_exp = float(req.min_experience_years or 0.0)
    max_exp = float(req.max_experience_years or 99.0)

    if cand_exp >= min_exp and cand_exp <= max_exp + 2.0:
        exp_score = 100.0
        exp_status = f"{cand_exp} yrs exp matches required {min_exp}-{max_exp} yrs"
    elif cand_exp < min_exp:
        diff = min_exp - cand_exp
        exp_score = max(20.0, 100.0 - (diff * 35.0))
        exp_status = f"{cand_exp} yrs exp (Requires minimum {min_exp} yrs)"
    else:
        exp_score = 80.0
        exp_status = f"{cand_exp} yrs exp (Overqualified for max {max_exp} yrs)"

    # 3. Location Scoring (15% Weight)
    cand_loc = (cand.location or "").strip().lower()
    profile_locs = []
    if profile and profile.preferred_locations:
        profile_locs = [l.strip().lower() for l in profile.preferred_locations.split(",") if l.strip()]

    req_loc = (req.location or "").strip().lower()

    if req.work_mode == WorkMode.REMOTE:
        location_score = 100.0
        location_status = "Remote position (Fully location compatible)"
    elif not req_loc or not cand_loc:
        location_score = 70.0
        location_status = "Location unspecified"
    elif cand_loc in req_loc or req_loc in cand_loc or any(p in req_loc for p in profile_locs):
        location_score = 100.0
        location_status = f"Location match ({req.location})"
    else:
        location_score = 50.0
        location_status = f"Requires relocation to {req.location}"

    # 4. Education Scoring (10% Weight)
    deg = (profile.degree or profile.highest_qualification or "").strip().lower() if profile else ""
    if deg and ("b.e" in deg or "b.tech" in deg or "m.tech" in deg or "mca" in deg or "b.sc" in deg or "computer" in deg):
        edu_score = 100.0
        edu_status = f"Strong qualification match ({profile.degree or profile.highest_qualification})"
    elif profile and profile.highest_qualification:
        edu_score = 80.0
        edu_status = f"Qualification: {profile.highest_qualification}"
    else:
        edu_score = 70.0
        edu_status = "Education details not specified"

    # 5. Preferences & Salary Match (10% Weight)
    exp_sal = 0.0
    if profile and profile.expected_salary:
        exp_sal = float(profile.expected_salary)
    elif cand and cand.expected_salary:
        exp_sal = float(cand.expected_salary)
    max_sal = float(req.max_salary or 0.0)
    
    if max_sal > 0 and exp_sal > 0:
        if exp_sal <= max_sal:
            pref_score = 100.0
        else:
            pref_score = 60.0
    else:
        pref_score = 85.0

    # Total Weighted Match Score
    total_score = round(
        (skills_score * 0.40) +
        (exp_score * 0.25) +
        (location_score * 0.15) +
        (edu_score * 0.10) +
        (pref_score * 0.10)
    )
    total_score = max(10, min(99, total_score))

    # Why it matches & what is missing
    why_matches = []
    if matched_skills:
        why_matches.append(f"Matching core skills: {', '.join(matched_skills[:4])}")
    if exp_score >= 80:
        why_matches.append(f"Relevant experience level ({exp_status})")
    if location_score >= 90:
        why_matches.append(f"Compatible work location / mode ({location_status})")
    if edu_score >= 80:
        why_matches.append(edu_status)

    what_is_missing = []
    if missing_skills:
        what_is_missing.append(f"Missing required skills: {', '.join(missing_skills[:4])}")
    if exp_score < 80:
        what_is_missing.append(exp_status)
    if location_score < 90 and req.work_mode != WorkMode.REMOTE:
        what_is_missing.append(f"Location mismatch: Job is in {req.location}")

    if not why_matches:
        why_matches.append("General candidate profile match for entry/mid-level requirements")

    return {
        "match_score": total_score,
        "matched_skills": matched_skills,
        "partial_skills": partial_skills,
        "missing_skills": missing_skills,
        "experience_status": exp_status,
        "location_status": location_status,
        "why_matches": why_matches,
        "what_is_missing": what_is_missing,
        "breakdown": {
            "skills_score": round(skills_score),
            "experience_score": round(exp_score),
            "location_score": round(location_score),
            "education_score": round(edu_score),
            "preference_score": round(pref_score)
        }
    }

def calculate_candidate_match(cand: Candidate, req: JobRequirement, profile: Optional[StudentProfile] = None) -> Dict[str, Any]:
    res = calculate_match_score(cand, req, profile)
    return {
        "candidate": cand,
        "match_score": float(res["match_score"]),
        "score_label": "NxtMov Match Score",
        "pros": res["why_matches"],
        "cons": res["what_is_missing"],
        "matched_skills": res["matched_skills"],
        "missing_skills": res["missing_skills"]
    }
