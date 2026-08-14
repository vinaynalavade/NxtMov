import re
import json
from typing import Dict, Any, List, Optional
from app.models.candidate import Candidate
from app.models.student_profile import StudentProfile
from app.models.resume import Resume

KNOWN_TECH_SKILLS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "html", "css", "sql",
    "selenium", "testng", "junit", "pytest", "playwright", "cypress", "appium",
    "react", "angular", "vue", "node.js", "express", "fastapi", "django", "spring boot",
    "postgresql", "mysql", "mongodb", "redis", "oracle",
    "aws", "docker", "kubernetes", "git", "github", "jira", "jenkins", "cicd",
    "manual testing", "automation testing", "api testing", "postman", "rest assured"
]

def extract_text_from_file_bytes(content: bytes, file_name: str) -> str:
    ext = file_name.lower().split(".")[-1] if "." in file_name else ""
    if ext in ["txt", "csv", "json", "md"]:
        return content.decode("utf-8-sig", errors="ignore")
    elif ext == "pdf":
        try:
            # Try reading pdf stream if pypdf or pdfplumber is available, else fallback to text decode
            text_chunks = []
            for line in content.split(b"\n"):
                clean = "".join(chr(b) for b in line if 32 <= b <= 126 or b in [10, 13])
                if len(clean) > 3:
                    text_chunks.append(clean)
            return "\n".join(text_chunks)
        except Exception:
            return content.decode("ascii", errors="ignore")
    else:
        # Fallback text decoder
        return content.decode("utf-8", errors="ignore")

def parse_resume_text(text: str) -> Dict[str, Any]:
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    full_text_lower = text.lower()

    # Extract Email
    email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    email = email_match.group(0) if email_match else None

    # Extract Phone
    phone_match = re.search(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
    phone = phone_match.group(0) if phone_match else None

    # Extract Name (Guess from first non-header line or email prefix)
    candidate_name = None
    if lines:
        for line in lines[:5]:
            if "@" not in line and not any(k in line.lower() for k in ["resume", "curriculum", "page", "contact"]):
                candidate_name = line.strip()
                break
    if not candidate_name and email:
        candidate_name = email.split("@")[0].replace(".", " ").title()

    # Extract Skills
    detected_skills = []
    for skill in KNOWN_TECH_SKILLS:
        if re.search(r"\b" + re.escape(skill) + r"\b", full_text_lower):
            detected_skills.append(skill.title())

    # Extract Education
    detected_education = []
    if "b.e" in full_text_lower or "b.tech" in full_text_lower or "bachelor" in full_text_lower:
        detected_education.append("Bachelor of Technology / Engineering")
    if "m.tech" in full_text_lower or "master" in full_text_lower or "mca" in full_text_lower:
        detected_education.append("Master of Technology / MCA")
    if "diploma" in full_text_lower:
        detected_education.append("Diploma")

    # Extract Links
    linkedin_match = re.search(r"https?://(www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+", text)
    github_match = re.search(r"https?://(www\.)?github\.com/[a-zA-Z0-9_-]+", text)

    return {
        "full_name": candidate_name,
        "email": email,
        "phone": phone,
        "skills": list(set(detected_skills)),
        "education": detected_education,
        "linkedin_url": linkedin_match.group(0) if linkedin_match else None,
        "github_url": github_match.group(0) if github_match else None,
        "raw_text_snippet": text[:500]
    }

def calculate_resume_quality_score(text: str, parsed: Dict[str, Any]) -> Dict[str, Any]:
    score = 40  # Base score
    strengths = []
    improvements = []

    if parsed.get("email") and parsed.get("phone"):
        score += 15
        strengths.append("✓ Clear contact details (Email & Phone detected)")
    else:
        improvements.append("⚠ Add explicit phone number and email address")

    skills_count = len(parsed.get("skills", []))
    if skills_count >= 5:
        score += 20
        strengths.append(f"✓ Rich technical skills detected ({skills_count} skills)")
    elif skills_count > 0:
        score += 10
        strengths.append(f"✓ Technical skills section found ({skills_count} skills)")
        improvements.append("⚠ List additional core technical skills & frameworks")
    else:
        improvements.append("⚠ Add a dedicated Skills section with relevant tech stack keywords")

    if parsed.get("education"):
        score += 15
        strengths.append(f"✓ Education & qualification detected ({', '.join(parsed['education'])})")
    else:
        improvements.append("⚠ Include degree, university, and graduation year details")

    if parsed.get("linkedin_url") or parsed.get("github_url"):
        score += 10
        strengths.append("✓ Professional links included (LinkedIn / GitHub)")
    else:
        improvements.append("⚠ Add your LinkedIn or GitHub profile link")

    if len(text.split()) > 150:
        score += 10
        strengths.append("✓ Adequate content length and detail")
    else:
        improvements.append("⚠ Expand work experience, projects, or responsibilities description")

    score = max(30, min(100, score))

    return {
        "quality_score": score,
        "strengths": strengths,
        "improvements": improvements
    }

def calculate_profile_completeness(cand: Candidate, profile: Optional[StudentProfile] = None) -> Dict[str, Any]:
    score = 0
    missing = []

    # 1. Identity & Contact (30%)
    if cand.full_name:
        score += 10
    if cand.email:
        score += 10
    if cand.phone or (profile and profile.city):
        score += 10
    else:
        missing.append("Phone number & location")

    # 2. Professional Info & Preferences (20%)
    if profile and (profile.headline or profile.career_objective):
        score += 10
    else:
        missing.append("Career objective / headline")

    if profile and profile.preferred_roles:
        score += 10
    else:
        missing.append("Preferred job roles & locations")

    # 3. Education & Qualification (15%)
    if profile and profile.highest_qualification:
        score += 15
    else:
        missing.append("Education & qualification details")

    # 4. Technical Skills (15%)
    if cand.primary_skills or (profile and (profile.programming_languages or profile.frameworks or profile.testing_tools)):
        score += 15
    else:
        missing.append("Technical skills & tools")

    # 5. Professional Links & Social (10%)
    if profile and (profile.linkedin_url or profile.github_url or profile.portfolio_url):
        score += 10
    else:
        missing.append("LinkedIn or GitHub profile link")

    # 6. Resume Upload (10%)
    if cand.resume_url:
        score += 10
    else:
        missing.append("Uploaded resume file")

    score = max(0, min(100, score))

    return {
        "completeness_score": score,
        "missing_items": missing
    }
