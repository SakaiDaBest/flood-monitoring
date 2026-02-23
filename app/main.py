from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.database import engine, Base
from app.routers import devices, readings, incidents, auth, dashboard
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Flood Monitoring System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(devices.router, prefix="/devices", tags=["devices"])
app.include_router(readings.router, prefix="/readings", tags=["readings"])
app.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
app.include_router(dashboard.router, tags=["dashboard"])

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "flood-monitor"}
