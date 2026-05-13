"""
routers/sync.py — Manual Supabase sync trigger.

POST /sync   — push all unsynced local records to Supabase for a given company.
               Called automatically by app.js every 60 s when online.
"""
import threading
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

import db
from routers._deps import require_secret

router = APIRouter(
    prefix="/sync",
    tags=["sync"],
    dependencies=[Depends(require_secret)],
)


class SyncRequest(BaseModel):
    company_id: Optional[str] = None


@router.post("")
def trigger_sync(body: SyncRequest):
    """
    Kick off a background sync.  Returns immediately so the UI doesn't block.
    company_id is used to also sync company_templates for that company.
    """
    def _do_sync():
        db.sync_to_cloud()
        if body.company_id:
            db.sync_company_templates_to_cloud(body.company_id)

    threading.Thread(target=_do_sync, daemon=True).start()
    return {"success": True, "message": "Sync started in background"}
