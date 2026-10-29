"""Appointment validation, conflict checks and status updates."""
from datetime import date, datetime
from utils.storage import load_records, save_records
from utils.ids import next_id
from utils.validators import required_text, valid_date, valid_time


def appointment_record(data, appointment_id=None, today=None):
    patients = load_records("patients.json")
    doctors = load_records("doctors.json")
    patient_id, doctor_id = data.get("patient_id"), data.get("doctor_id")
    if not any(row["id"] == patient_id for row in patients):
        raise ValueError("Select a registered patient.")
    if not any(row["id"] == doctor_id for row in doctors):
        raise ValueError("Select a registered doctor.")
    day = valid_date(data.get("date", ""), "Appointment date")
    at = valid_time(data.get("time", ""))
    now = datetime.now()
    today = today or now.date()
    if day < today or (day == today and at <= now.time().replace(second=0, microsecond=0)):
        raise ValueError("New or rescheduled appointments must be in the future.")
    status = data.get("status", "Booked")
    if status not in ("Booked", "Completed", "Cancelled"):
        raise ValueError("Choose a valid appointment status.")
    rows = load_records("appointments.json")
    for row in rows:
        if row.get("id") != appointment_id and row.get("status") == "Booked" and row.get("doctor_id") == doctor_id and row.get("date") == day.isoformat() and row.get("time") == at.strftime("%H:%M"):
            raise ValueError("This doctor already has a booked appointment at that time.")
    return {"patient_id": patient_id, "doctor_id": doctor_id, "date": day.isoformat(), "time": at.strftime("%H:%M"), "reason": str(data.get("reason", "")).strip(), "status": status}


def save_appointment(data, appointment_id=None):
    rows = load_records("appointments.json")
    item = appointment_record(data, appointment_id)
    item["id"] = appointment_id or next_id(rows, "A")
    item["created_at"] = next((r.get("created_at") for r in rows if r.get("id") == appointment_id), datetime.now().isoformat(timespec="seconds"))
    if appointment_id:
        rows = [item if row.get("id") == appointment_id else row for row in rows]
    else:
        rows.append(item)
    save_records("appointments.json", rows)
    return item


def set_status(appointment_id, status):
    rows = load_records("appointments.json")
    row = next((r for r in rows if r.get("id") == appointment_id), None)
    if row is None:
        raise ValueError("The selected appointment no longer exists.")
    if status not in ("Booked", "Completed", "Cancelled"):
        raise ValueError("Choose a valid status.")
    row["status"] = status
    save_records("appointments.json", rows)
