from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.settings import settings
from app.api.auth import router as auth_router
from app.api.vendors import router as vendors_router
from app.api.catalog import router as catalog_router
from app.api.bookings import router as bookings_router
from app.api.orders import router as orders_router
from app.api.promotions import router as promotions_router
from app.api.admin import router as admin_router
from app.api.reviews import router as reviews_router



app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    summary="API for booking platform",
    debug=settings.app_debug,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Next.js dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(vendors_router, prefix="/api/v1")
app.include_router(catalog_router, prefix="/api/v1")
app.include_router(bookings_router, prefix="/api/v1")
app.include_router(orders_router, prefix="/api/v1")
app.include_router(promotions_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(reviews_router, prefix="/api/v1")


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}
