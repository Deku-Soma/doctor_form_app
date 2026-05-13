"""
routers/employees.py — Employee CRUD endpoints.

GET    /employees                        — list all employees (optionally filter by company_id)
GET    /employees/{employee_id}          — get one employee
POST   /employees                        — create employee
PUT    /employees/{employee_id}          — update employee
DELETE /employees/{employee_id}          — delete employee
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from routers._deps import require_secret
from Utility.local_db import local_db

router = APIRouter(
    prefix="/employees",
    tags=["employees"],
    dependencies=[Depends(require_secret)],
)


class EmployeeIn(BaseModel):
    company_id: str
    first_name: str
    last_name: str
    id_number: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


@router.get("")
def list_employees(company_id: Optional[str] = Query(None)):
    """Return employees, optionally filtered by company_id."""
    if company_id:
        rows = local_db.get_employees_by_company(company_id)
    else:
        rows = local_db.get_all_employees()
    return {"employees": [dict(r) for r in rows]}


@router.get("/{employee_id}")
def get_employee(employee_id: str):
    """Return a single employee by ID."""
    row = local_db.get_employee(employee_id)
    if not row:
        raise HTTPException(status_code=404, detail="Employee not found")
    return dict(row)


@router.post("")
def create_employee(body: EmployeeIn):
    """Create a new employee."""
    import ulid as _ulid
    employee_id = str(_ulid.new())
    payload = {"id": employee_id, **body.model_dump()}
    local_db.save_employee(payload)
    return {"success": True, "id": employee_id}


@router.put("/{employee_id}")
def update_employee(employee_id: str, body: EmployeeIn):
    """Update an existing employee."""
    existing = local_db.get_employee(employee_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Employee not found")
    updated = {**dict(existing), **body.model_dump(exclude_none=True)}
    local_db.save_employee(updated)
    return {"success": True}


@router.delete("/{employee_id}")
def delete_employee(employee_id: str):
    """Delete an employee."""
    local_db.delete_employee(employee_id)
    return {"success": True}
