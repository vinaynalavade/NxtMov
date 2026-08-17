from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.database import get_db
from app.core.tenant import get_current_tenant, TenantContext
from app.core.permissions import require_permission, Permission
from app.models.company import Company
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse
from app.schemas.contact import ContactResponse
from app.schemas.requirement import JobRequirementResponse

router = APIRouter()

@router.get("", response_model=List[CompanyResponse], summary="List Companies in Workspace")
def list_companies(
    search: Optional[str] = Query(None, description="Search by name, industry, or location"),
    skip: int = 0,
    limit: int = 100,
    ctx: TenantContext = Depends(require_permission(Permission.COMPANIES_VIEW)),
    db: Session = Depends(get_db)
):
    query = db.query(Company).filter(Company.organization_id == ctx.organization.id)
    if search:
        term = f"%{search}%"
        query = query.filter(
            or_(
                Company.name.ilike(term),
                Company.industry.ilike(term),
                Company.location.ilike(term)
            )
        )
    companies = query.order_by(Company.name.asc()).offset(skip).limit(limit).all()
    return companies

@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED, summary="Create Company")
def create_company(
    company_in: CompanyCreate,
    ctx: TenantContext = Depends(require_permission(Permission.COMPANIES_MANAGE)),
    db: Session = Depends(get_db)
):
    # Prevent exact duplicate company names within the same tenant workspace
    existing = (
        db.query(Company)
        .filter(
            Company.organization_id == ctx.organization.id,
            Company.name.ilike(company_in.name.strip())
        )
        .first()
    )
    if existing:
        return existing

    company = Company(
        organization_id=ctx.organization.id,
        name=company_in.name.strip(),
        website=company_in.website,
        industry=company_in.industry,
        location=company_in.location,
        notes=company_in.notes
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company

@router.get("/{company_id}", response_model=CompanyResponse, summary="Get Company Detail")
def get_company(
    company_id: int,
    ctx: TenantContext = Depends(require_permission(Permission.COMPANIES_VIEW)),
    db: Session = Depends(get_db)
):
    company = (
        db.query(Company)
        .filter(Company.id == company_id, Company.organization_id == ctx.organization.id)
        .first()
    )
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found.")
    return company

@router.put("/{company_id}", response_model=CompanyResponse, summary="Update Company")
def update_company(
    company_id: int,
    company_in: CompanyUpdate,
    ctx: TenantContext = Depends(require_permission(Permission.COMPANIES_MANAGE)),
    db: Session = Depends(get_db)
):
    company = (
        db.query(Company)
        .filter(Company.id == company_id, Company.organization_id == ctx.organization.id)
        .first()
    )
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found.")

    update_data = company_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)

    db.commit()
    db.refresh(company)
    return company

@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Company")
def delete_company(
    company_id: int,
    ctx: TenantContext = Depends(require_permission(Permission.COMPANIES_MANAGE)),
    db: Session = Depends(get_db)
):
    company = (
        db.query(Company)
        .filter(Company.id == company_id, Company.organization_id == ctx.organization.id)
        .first()
    )
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found.")

    db.delete(company)
    db.commit()
    return None

@router.get("/{company_id}/contacts", response_model=List[ContactResponse], summary="Get Related HR Contacts")
def get_company_contacts(
    company_id: int,
    ctx: TenantContext = Depends(require_permission(Permission.COMPANIES_VIEW)),
    db: Session = Depends(get_db)
):
    company = (
        db.query(Company)
        .filter(Company.id == company_id, Company.organization_id == ctx.organization.id)
        .first()
    )
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found.")
    return company.contacts
