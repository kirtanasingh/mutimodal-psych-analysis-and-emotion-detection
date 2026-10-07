from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes.auth import router as auth_router
from app.api.routes.patients import router as patients_router
from app.api.routes.sessions import router as sessions_router
from app.api.routes.dashboard import router as dashboard_router

app = FastAPI(title="Psychological Session Analysis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(sessions_router)
app.include_router(dashboard_router)

@app.get("/api/ping")
def ping():
    return {"status": "ok", "message": "Backend is alive"}
