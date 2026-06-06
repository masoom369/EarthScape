import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import get_settings
from app.db.mongo import connect, create_indexes, disconnect
from app.middleware.logging import RequestLoggingMiddleware
from app.routes import alerts, auth, climate, ingest, jobs, support, system, users
from app.routes.ingest import limiter
from app.services.auth_service import AuthService

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    try:
        await connect()
        await create_indexes()
        await AuthService().ensure_default_admin(
            settings.default_admin_email,
            settings.default_admin_password,
        )
        logger.info("startup_complete", mongo_db=settings.mongo_db)
    except Exception as exc:
        logger.error("startup_failed", error=str(exc))
        raise SystemExit(1) from exc
    yield
    await disconnect()


settings = get_settings()

app = FastAPI(
    title="EarthScape Climate Agency API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware — order matters: CORS first, then logging, then rate-limit
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError):
    if "MongoDB not connected" in str(exc):
        return JSONResponse(status_code=503, content={"detail": "Database unavailable"})
    raise exc


# All routers on the single app — no sub-app mount, ensures middleware applies everywhere
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(ingest.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(climate.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(support.router, prefix="/api")
app.include_router(system.router)