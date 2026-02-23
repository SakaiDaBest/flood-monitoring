from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
import os

router = APIRouter()
templates = Jinja2Templates(directory="dashboard/templates")

@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    devices = db.query(models.Device).all()
    return templates.TemplateResponse("dashboard.html", {"request": request, "devices": devices})
