from contextlib import asynccontextmanager
import secrets

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.api import chat, dashboard, projects, settings, sources
from app.config import get_config
from app.database import init_db
from app.mcp_server import mcp


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with mcp.session_manager.run():
        yield


config = get_config()
app = FastAPI(title=config.app_name, version="0.1.0", lifespan=lifespan)


@app.middleware("http")
async def protect_api(request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)
    supplied = request.headers.get("authorization", "")
    supplied = supplied[7:].strip() if supplied.lower().startswith("bearer ") else ""
    public_api_paths = {"/api/health", "/api/auth/status"}
    if request.url.path.startswith("/api") and request.url.path not in public_api_paths and config.app_api_key:
        if not secrets.compare_digest(supplied, config.app_api_key):
            return JSONResponse({"detail": "Authentication required"}, status_code=401, headers={"WWW-Authenticate": "Bearer"})
    if request.url.path.startswith("/mcp") and config.mcp_api_key:
        if not secrets.compare_digest(supplied, config.mcp_api_key):
            return JSONResponse({"error": "Unauthorized"}, status_code=401, headers={"WWW-Authenticate": "Bearer"})
    return await call_next(request)


app.add_middleware(CORSMiddleware, allow_origins=config.cors_origin_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(projects.router, prefix="/api")
app.include_router(sources.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")


@app.get("/api/health")
async def health(): return {"status": "ok"}


@app.get("/api/auth/status")
async def auth_status(): return {"required": bool(config.app_api_key)}


@app.get("/api/auth/verify")
async def auth_verify(): return {"authenticated": True}


app.mount("/", mcp.streamable_http_app())
