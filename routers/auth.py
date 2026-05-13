"""
routers/auth.py — Authentication endpoints.

POST /login   — validate credentials, return session info
POST /logout  — no-op (stateless); client drops its stored token
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

import db
from routers._deps import require_secret

router = APIRouter(prefix="/auth", tags=["auth"], dependencies=[Depends(require_secret)])


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(body: LoginRequest):
    """
    Validate credentials against Supabase (online) or local cache (offline).
    Returns the user record and login mode on success.
    Raises 401 on failure.
    """
    result = db.validate_login(body.email, body.password)
    if not result.get("success"):
        raise HTTPException(status_code=401, detail=result.get("message", "Login failed"))
    return {
        "success": True,
        "user": result.get("user"),
        "mode": result.get("mode", "online"),
    }


@router.post("/logout")
def logout():
    """
    Stateless logout — the client simply discards its session token.
    This endpoint exists so the JS layer can call it uniformly.
    """
    return {"success": True}
