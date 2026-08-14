import random
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.tenant import get_current_tenant, TenantContext
from app.models.company import Company, Contact, ContactStatus
from app.models.requirement import JobRequirement, EmploymentType, RequirementStatus
from app.models.activity import Call, Followup, CallType, CallOutcome, FollowupStatus, FollowupPriority, EntityType
from app.models.application import Application, ApplicationStage, Interview, InterviewOutcome

router = APIRouter()

COMPANIES_SEED = [
    ("Infosys Technologies", "IT Services & Consulting", "Bengaluru", "https://infosys.com"),
    ("Tata Consultancy Services", "IT & Business Solutions", "Mumbai", "https://tcs.com"),
    ("Wipro Digital", "Information Technology", "Bengaluru", "https://wipro.com"),
    ("HCL Tech", "Software & Cloud Services", "Noida", "https://hcltech.com"),
    ("Tech Mahindra", "Telecom & Software", "Pune", "https://techmahindra.com"),
    ("Accenture India", "Management Consulting", "Gurugram", "https://accenture.com"),
    ("Cognizant", "IT Services", "Chennai", "https://cognizant.com"),
    ("Capgemini", "Consulting & Tech", "Hyderabad", "https://capgemini.com"),
    ("IBM India", "Cloud & AI", "Bengaluru", "https://ibm.com"),
    ("Amazon India", "E-Commerce & AWS", "Hyderabad", "https://amazon.jobs"),
    ("Microsoft India", "Software & Cloud", "Hyderabad", "https://careers.microsoft.com"),
    ("Google India", "Internet & Software", "Bengaluru", "https://careers.google.com"),
    ("Flipkart", "E-Commerce", "Bengaluru", "https://flipkartcareers.com"),
    ("Zomato", "Food Tech", "Gurugram", "https://zomato.com"),
    ("Swiggy", "Delivery Tech", "Bengaluru", "https://swiggy.com"),
    ("Paytm", "FinTech", "Noida", "https://paytm.com"),
    ("PhonePe", "Digital Payments", "Bengaluru", "https://phonepe.com"),
    ("Razorpay", "FinTech", "Bengaluru", "https://razorpay.com"),
    ("Freshworks", "SaaS Software", "Chennai", "https://freshworks.com"),
    ("Zoho Corporation", "SaaS Software", "Chennai", "https://zoho.com"),
    ("Ola Cabs", "Mobility Tech", "Bengaluru", "https://olacabs.com"),
    ("MakeMyTrip", "Travel Tech", "Gurugram", "https://makemytrip.com"),
    ("InMobi", "AdTech & SaaS", "Bengaluru", "https://inmobi.com"),
    ("Postman", "API Platform", "Bengaluru", "https://postman.com"),
    ("BrowserStack", "Testing Cloud", "Mumbai", "https://browserstack.com"),
]

FIRST_NAMES = ["Priya", "Rahul", "Ananya", "Amit", "Sneha", "Vikram", "Kavya", "Rohan", "Neha", "Siddharth", "Pooja", "Arjun", "Divya", "Deepak", "Shreya", "Karan", "Meera", "Nikhil", "Aishwarya", "Varun"]
LAST_NAMES = ["Sharma", "Patil", "Verma", "Gupta", "Rao", "Nair", "Kulkarni", "Deshmukh", "Singh", "Joshi", "Iyer", "Chopra", "Reddy", "Mehta", "Bhat", "Agarwal", "Saxena", "Pillai", "Das", "Kapoor"]
DESIGNATIONS = ["Senior Technical Recruiter", "Talent Acquisition Manager", "HR Business Partner", "Lead Recruiter", "Head of Hiring", "Technical Sourcer", "HR Executive"]
JOB_TITLES = ["Senior QA Automation Engineer", "Full Stack Software Engineer", "Python Backend Developer", "DevOps Cloud Engineer", "Frontend React/JS Specialist", "Data Engineer", "SDET Lead", "Engineering Manager"]
SKILLS_LIST = ["Python, FastAPI, Pytest, Docker", "Java, Spring Boot, Microservices", "React, JavaScript, CSS3, HTML5", "Node.js, PostgreSQL, Redis", "AWS, Kubernetes, Terraform", "Selenium, Playwright, Python"]

@router.post("/seed", summary="Generate Realistic Development Seed Data")
def generate_seed_data(
    ctx: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    now = datetime.now(timezone.utc)
    
    # 1. Create Companies
    created_companies = []
    for name, ind, loc, web in COMPANIES_SEED:
        existing = db.query(Company).filter(Company.organization_id == ctx.organization.id, Company.name == name).first()
        if not existing:
            comp = Company(
                organization_id=ctx.organization.id,
                name=name,
                industry=ind,
                location=loc,
                website=web,
                notes="Generated development seed employer profile."
            )
            db.add(comp)
            db.flush()
            created_companies.append(comp)
        else:
            created_companies.append(existing)

    # 2. Create HR Contacts (3-5 per company)
    created_contacts = []
    statuses = list(ContactStatus)
    for comp in created_companies:
        for _ in range(random.randint(2, 4)):
            fn = random.choice(FIRST_NAMES)
            ln = random.choice(LAST_NAMES)
            contact_name = f"{fn} {ln}"
            email = f"{fn.lower()}.{ln.lower()}@{comp.name.lower().replace(' ', '')[:10]}.com"
            phone = f"+91 {random.randint(70000, 99999)} {random.randint(10000, 99999)}"
            
            existing = db.query(Contact).filter(Contact.organization_id == ctx.organization.id, Contact.email == email).first()
            if not existing:
                contact = Contact(
                    organization_id=ctx.organization.id,
                    company_id=comp.id,
                    name=contact_name,
                    designation=random.choice(DESIGNATIONS),
                    phone=phone,
                    email=email,
                    location=comp.location,
                    status=random.choice(statuses),
                    notes="Seed HR contact record."
                )
                db.add(contact)
                db.flush()
                created_contacts.append(contact)
            else:
                created_contacts.append(existing)

    # 3. Create Job Requirements / Opportunities
    created_requirements = []
    req_statuses = [RequirementStatus.NEW, RequirementStatus.INTERESTED, RequirementStatus.APPLIED, RequirementStatus.INTERVIEWING]
    for _ in range(15):
        comp = random.choice(created_companies)
        title = random.choice(JOB_TITLES)
        req = JobRequirement(
            organization_id=ctx.organization.id,
            company_id=comp.id,
            title=title,
            location=comp.location,
            employment_type=EmploymentType.FULL_TIME,
            skills_req=random.choice(SKILLS_LIST),
            openings_count=random.randint(1, 5),
            min_salary=1200000.00,
            max_salary=2500000.00,
            status=random.choice(req_statuses),
            notes="Active seed opportunity opening."
        )
        db.add(req)
        db.flush()
        created_requirements.append(req)

    # 4. Create Applications & Interviews
    for req in created_requirements[:8]:
        app_stage = ApplicationStage.INTERVIEWING if req.status == RequirementStatus.INTERVIEWING else ApplicationStage.APPLIED
        app_obj = Application(
            organization_id=ctx.organization.id,
            job_requirement_id=req.id,
            candidate_id=1,  # User's implicit candidate
            stage=app_stage,
            notes="Submitted resume & initial screening."
        )
        db.add(app_obj)
        db.flush()

        if app_stage == ApplicationStage.INTERVIEWING:
            interview = Interview(
                application_id=app_obj.id,
                round_name="Technical Round 1",
                scheduled_at=now + timedelta(days=random.randint(1, 5)),
                location_or_link="https://meet.google.com/seed-demo-link",
                interviewer_names="Engineering Hiring Team",
                outcome=InterviewOutcome.SCHEDULED
            )
            db.add(interview)

    # 5. Create Follow-up Tasks (Today, Overdue, Upcoming)
    followup_priorities = list(FollowupPriority)
    for i in range(12):
        if i % 3 == 0:
            due_dt = now  # Today
            t_title = f"Follow up call with {random.choice(created_contacts).name}"
        elif i % 3 == 1:
            due_dt = now - timedelta(days=2)  # Overdue
            # pyrefly: ignore [missing-attribute]
            t_title = f"Overdue: Reconnect with {random.choice(created_contacts).company.name} HR"
        else:
            due_dt = now + timedelta(days=3)  # Upcoming
            t_title = f"Upcoming: Send updated CV for {random.choice(JOB_TITLES)}"

        followup = Followup(
            organization_id=ctx.organization.id,
            assigned_user_id=ctx.user.id,
            title=t_title,
            description="Seed follow-up action item for testing.",
            due_date=due_dt,
            priority=random.choice(followup_priorities),
            status=FollowupStatus.PENDING
        )
        db.add(followup)

    db.commit()

    return {
        "message": "Development seed data created successfully!",
        "companies_created": len(created_companies),
        "contacts_created": len(created_contacts),
        "opportunities_created": len(created_requirements)
    }
