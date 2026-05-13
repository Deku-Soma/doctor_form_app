"""
routers/_deps.py — Shared FastAPI dependencies.

require_secret():
    Validates the X-App-Secret header against the per-process secret set in
    main_server.py.  Must be applied to every router via:

        router = APIRouter(dependencies=[Depends(require_secret)])

    WARNING: Without this, any process on the device that can reach port 8765
    can call the API unauthenticated.  This is especially critical on Android
    where multiple apps share the same network stack.
"""
import os

from fastapi import Depends, Header, HTTPException


def require_secret(x_app_secret: str = Header(..., alias="x-app-secret")) -> None:
    """Raise 401 if the caller's X-App-Secret doesn't match ours."""
    _secret = os.environ.get("HC360_APP_SECRET", "")
    if not _secret or x_app_secret != _secret:
        raise HTTPException(status_code=401, detail="Unauthorised")


def get_current_session(x_app_secret: str = Header(..., alias="x-app-secret")) -> None:
    """Alias — convenience wrapper for require_secret."""
    require_secret(x_app_secret)
