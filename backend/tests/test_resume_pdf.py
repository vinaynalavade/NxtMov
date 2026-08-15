import io
import pytest
from fastapi.testclient import TestClient
import pypdf
from app.main import app
from app.services.resume_service import (
    extract_text_from_file_bytes,
    parse_resume_text,
    calculate_ats_score,
    clean_and_normalize_text,
    extract_education_entries
)

client = TestClient(app)

def test_clean_and_normalize_text_removes_pdf_artifacts():
    raw_artifact_text = (
        "%PDF-1.7\n"
        "4 0 obj\n"
        "stream\nx\x9c+T0\x00\x03\x00\x01\x8d\x00\xef\n"
        "endstream\n"
        "endobj\n"
        "Vinay Nalavade\n"
        "Email: vinaynalavade0704@gmail.com\n"
        "Skills: Selenium, Java, Pytest, Manual Testing, Postman, SQL, JIRA\n"
        "Education: Bachelor of Technology (B.Tech)\n"
    )
    cleaned = clean_and_normalize_text(raw_artifact_text)
    assert "%PDF-" not in cleaned
    assert "obj" not in cleaned.splitlines()[0]
    assert "Vinay Nalavade" in cleaned

def test_multi_entry_education_detection_vinay_resume():
    """
    Validates detection of multiple education entries without generic normalization or overwriting.
    Must detect both B.Tech (DBATU University, 2024, CGPA 7.98) and Diploma (MSBTE, 2021, 84.00%).
    """
    resume_text = (
        "VINAY NALAVADE\n"
        "Software Quality Assurance & Automation Engineer | Pune, India\n"
        "Email: vinaynalavade0704@gmail.com | Phone: +91 93593 45433\n"
        "LinkedIn: https://linkedin.com/in/vinaynalavade | GitHub: https://github.com/vinaynalavade\n\n"
        "PROFESSIONAL SUMMARY\n"
        "Dedicated QA Automation Engineer with expertise in Test Automation Frameworks, Selenium WebDriver, Core Java, Postman API Testing, and Manual Testing. Proven track record in designing Page Object Models and reducing test regression execution time by 40%.\n\n"
        "EDUCATION\n"
        "Bachelors of Technology – Computer Science & Engineering\n"
        "DBATU University – Fabtech Technical Campus\n"
        "CGPA 7.98\n"
        "2024\n\n"
        "Diploma – Computer Technology\n"
        "Maharashtra State Board of Technical Education\n"
        "Brahmdevdada Mane Polytechnic\n"
        "84.00%\n"
        "2021\n\n"
        "TECHNICAL SKILLS\n"
        "Programming Languages: Core Java, Basic Python, SQL\n"
        "Automation: Selenium WebDriver, TestNG, Maven, POM (Page Object Model), Fireflink\n"
        "API Testing: Postman, REST API\n"
        "Testing: Manual Testing, Regression Testing, Smoke Testing, Functional Testing, STLC, SDLC, Test Case Design, Defect Lifecycle Management\n"
        "BI & Reporting: SAP BusinessObjects, Advanced Excel\n"
        "Tools & Methodologies: Git, GitHub, Jenkins, Jira, Eclipse, VS Code, Agile / Scrum\n\n"
        "PROFESSIONAL EXPERIENCE & PROJECTS\n"
        "QA Automation Engineer - Web Application Testing\n"
        "• Developed hybrid automation test framework using Selenium WebDriver, TestNG, and Page Object Model architecture.\n"
        "• Executed 250+ automated regression and smoke test suites across cross-browser platforms.\n"
        "• Conducted end-to-end REST API testing using Postman, validating JSON request payloads and HTTP response status codes.\n"
        "• Managed defect life cycle in Jira, logging 80+ critical bugs and collaborating with development teams in Agile sprints.\n"
    )

    parsed = parse_resume_text(resume_text)

    # 1. Verify candidate identity
    assert parsed["full_name"] == "VINAY NALAVADE"
    assert parsed["email"] == "vinaynalavade0704@gmail.com"
    assert parsed["phone"] is not None and "93593" in parsed["phone"]

    # 2. Verify BOTH education entries are extracted
    entries = parsed["education_entries"]
    assert len(entries) >= 2

    # Verify B.Tech entry
    btech = next((e for e in entries if "Bachelor" in e["degree"] or "B.Tech" in e["degree"]), None)
    assert btech is not None
    assert "Computer Science" in (btech["specialization"] or "")
    assert "DBATU" in (btech["institution"] or "")
    assert btech["year"] == 2024
    assert btech["score"] is not None and "7.98" in btech["score"]

    # Verify Diploma entry
    diploma = next((e for e in entries if "Diploma" in e["degree"]), None)
    assert diploma is not None
    assert "Computer" in (diploma["specialization"] or "")
    assert "Maharashtra State Board" in (diploma["institution"] or "") or "Polytechnic" in (diploma["institution"] or "")
    assert diploma["year"] == 2021
    assert diploma["score"] is not None and "84" in diploma["score"]

    # 3. Verify Categorized Skills
    cat_skills = parsed["categorized_skills"]
    assert "Programming Languages" in cat_skills
    assert "Java" in cat_skills["Programming Languages"]
    assert "Python" in cat_skills["Programming Languages"]
    assert "Quality Assurance & Automation" in cat_skills

    # 4. Verify ATS Scoring
    ats = calculate_ats_score(resume_text, parsed)
    assert ats["ats_score"] >= 80
    assert "score_breakdown" in ats
    assert len(ats["strengths"]) >= 3

def test_universal_multidomain_resume_intelligence():
    """
    Tests holistic domain detection and ATS scoring across diverse career tracks
    (Full Stack / Python Backend & DevOps / Cloud) without forcing QA assumptions.
    """
    # 1. Software Development / Python Backend Resume
    dev_resume = (
        "ARJUN SHARMA\n"
        "Full Stack & Backend Software Engineer | Bengaluru, India\n"
        "Email: arjun.dev@example.com | Phone: +91 98765 43210\n"
        "LinkedIn: https://linkedin.com/in/arjundev | GitHub: https://github.com/arjundev\n\n"
        "PROFESSIONAL SUMMARY\n"
        "Software Engineer with 4 years of experience architecting high-throughput microservices using Python, FastAPI, Django, PostgreSQL, and React.js. Reduced API latency by 35% and scaled distributed systems to 500k+ active users.\n\n"
        "EDUCATION\n"
        "Bachelor of Technology in Computer Science\n"
        "Indian Institute of Technology (IIT), 2020\n"
        "CGPA: 8.9\n\n"
        "SKILLS\n"
        "Python, JavaScript, TypeScript, FastAPI, Django, React.js, PostgreSQL, Redis, Docker, Git\n\n"
        "EXPERIENCE\n"
        "Senior Backend Developer\n"
        "• Engineered REST APIs using FastAPI and PostgreSQL handling 2M+ daily requests with 99.9% uptime.\n"
        "• Built responsive frontend dashboards using React.js, Tailwind CSS, and Webpack.\n"
    )
    dev_parsed = parse_resume_text(dev_resume)
    assert dev_parsed["career_domain"] == "Software Development"
    assert any("Developer" in r or "Engineer" in r for r in dev_parsed["likely_roles"])
    dev_ats = calculate_ats_score(dev_resume, dev_parsed)
    assert dev_ats["ats_score"] >= 80

    # 2. DevOps & Cloud Infrastructure Resume
    devops_resume = (
        "PRIYA PATEL\n"
        "Cloud & DevOps Engineer | Hyderabad, India\n"
        "Email: priya.devops@example.com | Phone: +91 98765 11111\n"
        "LinkedIn: https://linkedin.com/in/priyadevops | GitHub: https://github.com/priyadevops\n\n"
        "PROFESSIONAL SUMMARY\n"
        "DevOps Engineer specializing in AWS cloud infrastructure, Kubernetes orchestration, Terraform Infrastructure-as-Code, and automated CI/CD pipelines.\n\n"
        "EDUCATION\n"
        "Bachelor of Engineering in Information Technology\n"
        "Osmania University, 2021\n\n"
        "SKILLS\n"
        "AWS, Docker, Kubernetes, Terraform, Jenkins, GitHub Actions, Linux, Prometheus, Grafana\n\n"
        "EXPERIENCE\n"
        "DevOps Engineer\n"
        "• Architected Kubernetes clusters on AWS using Terraform and automated deployments via GitHub Actions.\n"
        "• Deployed Prometheus and Grafana monitoring stacks reducing incident response time by 45%.\n"
    )
    devops_parsed = parse_resume_text(devops_resume)
    assert devops_parsed["career_domain"] == "DevOps & Cloud Engineering"
    assert any("DevOps" in r or "Cloud" in r for r in devops_parsed["likely_roles"])
    devops_ats = calculate_ats_score(devops_resume, devops_parsed)
    assert devops_ats["ats_score"] >= 75

def test_parse_empty_unreadable_resume():
    parsed = parse_resume_text("")
    assert parsed["full_name"] is None
    assert parsed["email"] is None
    assert parsed["skills"] == []
    assert parsed["education"] == []
    assert parsed["extraction_warning"] is not None

def test_resume_upload_view_and_avatar_lifecycle():
    """
    Tests authenticated resume upload, authenticated file streaming via /file,
    and profile picture upload / remove persistence.
    """
    # 1. Register user
    reg_res = client.post("/api/v1/auth/register", json={
        "full_name": "Vinay Nalavade",
        "email": "vinay.integration@example.com",
        "password": "Password123!"
    })
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Upload text resume
    resume_content = (
        b"VINAY NALAVADE\nEmail: vinay.integration@example.com\nPhone: +91 9359345433\nLinkedIn: https://linkedin.com/in/vinay\n"
        b"PROFESSIONAL SUMMARY\nExperienced Software & QA Automation Engineer with expertise in building robust test automation frameworks.\n"
        b"EDUCATION\nBachelors of Technology - Computer Science, DBATU University, 2024, CGPA 7.98\n"
        b"Diploma in Information Technology, MSBTE Board, 2021, Percentage 88.5%\n"
        b"SKILLS: Selenium WebDriver, Core Java, Python, SQL, Postman, REST API, TestNG, Jira, Git, Agile, Docker, AWS\n"
        b"EXPERIENCE & PROJECTS\nAutomated web applications using Selenium WebDriver and Page Object Model with 95% regression test pass rate.\n"
        b"Engineered REST API automation test suites reducing execution time by 40% across 500+ test cases.\n"
    )
    upload_res = client.post(
        "/api/v1/resumes/upload",
        headers=headers,
        files={"file": ("resume_vinay.txt", resume_content, "text/plain")}
    )
    assert upload_res.status_code == 200
    res_data = upload_res.json()
    resume_id = res_data["id"]
    assert res_data["ats_score"] >= 75
    assert "career_domain" in res_data
    assert "likely_roles" in res_data

    # 3. View authenticated resume file
    file_res = client.get(f"/api/v1/resumes/{resume_id}/file", headers=headers)
    assert file_res.status_code == 200
    assert file_res.headers["content-type"].startswith("text/plain")

    # 4. View file via token query parameter (for direct browser tab opening)
    tab_file_res = client.get(f"/api/v1/resumes/{resume_id}/file?token={token}")
    assert tab_file_res.status_code == 200

    # 5. Apply extracted analysis to profile
    apply_res = client.post(
        f"/api/v1/resumes/{resume_id}/apply-analysis",
        headers=headers,
        json={"accept_fields": ["name", "email", "phone", "skills", "education"]}
    )
    assert apply_res.status_code == 200
    assert apply_res.json()["status"] == "ACCEPTED"

    # 6. Profile Avatar Upload (.png)
    fake_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82"
    avatar_res = client.post(
        "/api/v1/profile/avatar",
        headers=headers,
        files={"file": ("avatar.png", fake_png, "image/png")}
    )
    assert avatar_res.status_code == 200
    avatar_url = avatar_res.json()["avatar_url"]
    assert avatar_url.startswith("/api/v1/profile/avatar/")

    # 7. Check Profile has updated avatar_url and education entries
    prof_res = client.get("/api/v1/profile", headers=headers)
    assert prof_res.status_code == 200
    pdata = prof_res.json()
    assert pdata["avatar_url"] == avatar_url
    assert "Selenium" in (pdata["testing_tools"] or "") or "Java" in (pdata["programming_languages"] or "")

    # 8. Delete Avatar and ensure removal
    del_res = client.delete("/api/v1/profile/avatar", headers=headers)
    assert del_res.status_code == 200

    prof_after_del = client.get("/api/v1/profile", headers=headers)
    assert prof_after_del.json()["avatar_url"] is None
