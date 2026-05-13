"""
routers/documents.py — Document listing endpoint.

GET /documents/{employee_id}   — list PDF paths for an employee
GET /documents/pdf             — serve a PDF file by path (for in-browser preview)
"""
import os

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from routers._deps import require_secret
from Utility.file_manager import FileManager

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    dependencies=[Depends(require_secret)],
)

_fm = FileManager(base_path=os.environ.get("HC360_OUTPUT_DIR", "outputs"))


@router.get("/{employee_id}")
def list_documents(employee_id: str, company_folder: str = Query(...)):
    """
    Return a list of PDF file paths for a given employee.
    Requires company_folder so we can locate the correct sub-directory.
    """
    employee_dir = _fm.get_employee_folder(company_folder, employee_id)
    if not os.path.isdir(employee_dir):
        return {"documents": []}

    pdfs = sorted(
        [
            os.path.join(employee_dir, f)
            for f in os.listdir(employee_dir)
            if f.lower().endswith(".pdf")
        ],
        reverse=True,  # newest first (ULID filenames sort chronologically)
    )
    return {"documents": pdfs}


@router.get("/pdf", include_in_schema=True)
def serve_pdf(path: str = Query(...)):
    """
    Serve a PDF file directly so the browser can display it inline.
    Only files within the configured output root are accessible.
    """
    output_root = os.path.abspath(os.environ.get("HC360_OUTPUT_DIR", "outputs"))
    abs_path = os.path.abspath(path)
    if not abs_path.startswith(output_root):
        raise HTTPException(status_code=403, detail="Access denied")
    if not os.path.isfile(abs_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(abs_path, media_type="application/pdf")
