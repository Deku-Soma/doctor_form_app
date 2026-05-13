"""
main_server.py — HealthCorp360 FastAPI entry point.
Mounts all routers, serves web_ui/ as static files.
On desktop: auto-opens system browser at http://127.0.0.1:8765.
On Android (Phase 10): started by Kotlin in a background thread; WebView
                        connects to the same URL without the browser call.
"""
import os
import secrets
import threading
import webbrowser

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# ── Per-process shared secret ────────────────────────────────────────────────
# Generated fresh every time the server starts. The JS bootstrap endpoint
# delivers it to the first page load; all subsequent requests must include it
# as the X-App-Secret header.  Prevents other processes on the device from
# calling the API unauthenticated.
os.environ["HC360_APP_SECRET"] = secrets.token_hex(32)

app = FastAPI(title="HealthCorp360", version="0.6.0")

# ── CORS — localhost only ─────────────────────────────────────────────────────
# WARNING: Do NOT use allow_origins=["*"]. Lock to local origin only.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8765", "http://localhost:8765"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["X-App-Secret", "Authorization", "Content-Type"],
    allow_credentials=True,
)

# ── Routers ───────────────────────────────────────────────────────────────────
from routers import auth, companies, employees, forms, documents, sync  # noqa: E402

for router_module in [auth, companies, employees, forms, documents, sync]:
    app.include_router(router_module.router)


# ── Health & bootstrap endpoints ─────────────────────────────────────────────
@app.get("/health", tags=["meta"])
def health():
    """Liveness probe. Returns {status: ok}."""
    return {"status": "ok"}


@app.get("/bootstrap", tags=["meta"])
def bootstrap():
    """
    Delivers the per-process shared secret to the first page load.
    The JS layer caches it in window.__APP_SECRET__ and sends it with every
    subsequent API request via the X-App-Secret header.
    """
    return {"secret": os.environ["HC360_APP_SECRET"]}


# ── Static files — must be mounted LAST (catch-all) ──────────────────────────
# web_ui/ is created in Phase 7. A placeholder is created now so the server
# starts without error.
_WEB_UI_DIR = os.path.join(os.path.dirname(__file__), "web_ui")
os.makedirs(_WEB_UI_DIR, exist_ok=True)
app.mount("/", StaticFiles(directory=_WEB_UI_DIR, html=True), name="static")


# ── Entry point ───────────────────────────────────────────────────────────────
def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")


if __name__ == "__main__":
    # Desktop: open browser 1.5 s after server starts (lets uvicorn bind first)
    threading.Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:8765")).start()
    run_server()
