"Testing CI/CD"
"""Main FastAPI application for MediBook."""
""" Testing the code for CI/CD"""
from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import init_db, db_session
from models.user import User
from models.appointment import Appointment
from routes import auth, appointments, doctors, prescriptions, files, messages, triggers
from utils.auth import get_password_hash

app = FastAPI(title="MediBook API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(appointments.router)
app.include_router(doctors.router)
app.include_router(prescriptions.router)
app.include_router(files.router)
app.include_router(messages.router)
app.include_router(triggers.router)
app.include_router(triggers.trigger_router)


@app.get("/")
def root() -> dict:
    """Health check root endpoint."""
    return {"status": "ok", "service": "MediBook"}


def _seed_users(db: Session) -> None:
    """Seed initial doctors and a demo patient if none exist."""
    if db.query(User).count() > 0:
        return

    doctors = [
        User(
            full_name="Dr. Priya Menon",
            email="priya.menon@medibook.local",
            hashed_password=get_password_hash("doctor123"),
            role="doctor",
            specialization="Cardiology",
            bio="Focuses on preventive cardiac care and lifestyle guidance.",
        ),
        User(
            full_name="Dr. Arjun Rao",
            email="arjun.rao@medibook.local",
            hashed_password=get_password_hash("doctor123"),
            role="doctor",
            specialization="Dermatology",
            bio="Treats acute and chronic skin conditions with empathy.",
        ),
        User(
            full_name="Dr. Aisha Khan",
            email="aisha.khan@medibook.local",
            hashed_password=get_password_hash("doctor123"),
            role="doctor",
            specialization="Pediatrics",
            bio="Cares for children and supports families with clear guidance.",
        ),
    ]
    patient = User(
        full_name="Demo Patient",
        email="patient@medibook.local",
        hashed_password=get_password_hash("patient123"),
        role="patient",
        bio="Sample patient account for testing.",
    )

    db.add_all(doctors + [patient])
    db.commit()


def _seed_appointments(db: Session) -> None:
    """Seed a demo appointment for the patient."""
    patient = db.query(User).filter(User.email == "patient@medibook.local").first()
    doctor = db.query(User).filter(User.email == "priya.menon@medibook.local").first()
    if not patient or not doctor:
        return

    existing = (
        db.query(Appointment)
        .filter(Appointment.patient_id == patient.id)
        .first()
    )
    if existing:
        return

    appt = Appointment(
        doctor_id=doctor.id,
        patient_id=patient.id,
        scheduled_at=datetime.utcnow() + timedelta(days=1, hours=2),
        status="scheduled",
        reason="General health consultation",
    )
    db.add(appt)
    db.commit()


@app.on_event("startup")
def on_startup() -> None:
    """Initialize database and seed sample data."""
    init_db()
    # Note: Seeding commented out due to bcrypt version compatibility.
    # Create users via /api/auth/register endpoint instead.
    # with db_session() as db:
    #     _seed_users(db)
    #     _seed_appointments(db)
