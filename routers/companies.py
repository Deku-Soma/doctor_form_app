"""
routers/companies.py — Company CRUD endpoints.

GET    /companies              — list all companies
GET    /companies/{company_id} — get one company
POST   /companies              — create company
PUT    /companies/{company_id} — update company
DELETE /companies/{company_id} — soft-delete company
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from routers._deps import require_secret
from Utility.local_db import local_db

router = APIRouter(
    prefix="/companies",
    tags=["companies"],
    dependencies=[Depends(require_secret)],
)


class CompanyIn(BaseModel):
    name: str
    folder_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None


@router.get("")
def list_companies():
    """Return all companies from local SQLite."""
    rows = local_db.get_all_companies()
    return {"companies": [dict(r) for r in rows]}


@router.get("/{company_id}")
def get_company(company_id: str):
    """Return a single company by ID."""
    row = local_db.get_company(company_id)
    if not row:
        raise HTTPException(status_code=404, detail="Company not found")
    return dict(row)


@router.post("")
def create_company(body: CompanyIn):
    """Create a new company."""
    import re, ulid as _ulid
    folder = body.folder_name or re.sub(r"\s+", "_", body.name).lower()
    company_id = str(_ulid.new())
    local_db.save_company({
        "id": company_id,
        "name": body.name,
        "folder_name": folder,
        "contact_email": body.contact_email or "",
        "contact_phone": body.contact_phone or "",
        "address": body.address or "",
    })
    return {"success": True, "id": company_id}


@router.put("/{company_id}")
def update_company(company_id: str, body: CompanyIn):
    """Update an existing company."""
    existing = local_db.get_company(company_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Company not found")
    updated = {**dict(existing), **body.model_dump(exclude_none=True)}
    local_db.save_company(updated)
    return {"success": True}


@router.delete("/{company_id}")
def delete_company(company_id: str):
    """Delete a company (local only for now)."""
    local_db.delete_company(company_id)
    return {"success": True}
