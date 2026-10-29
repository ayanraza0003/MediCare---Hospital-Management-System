"""Bill creation with saved line-item snapshots."""
from datetime import date, datetime
from decimal import Decimal
from utils.ids import next_id
from utils.storage import load_records, save_records
from utils.validators import money, valid_date


def calculate_total(items):
    if not items:
        raise ValueError("Add at least one bill item.")
    return float(sum((Decimal(str(money(item.get("amount"), "Item amount"))) for item in items), Decimal("0.00")))


def create_bill(patient_id, doctor_id, bill_date, items):
    if not any(row.get("id") == patient_id for row in load_records("patients.json")):
        raise ValueError("Select a registered patient.")
    doctor = next((row for row in load_records("doctors.json") if row.get("id") == doctor_id), None) if doctor_id else None
    if doctor_id and doctor is None:
        raise ValueError("Select a registered doctor or leave the doctor blank.")
    if not bill_date:
        bill_date = date.today().isoformat()
    bill_date = valid_date(bill_date, "Bill date").isoformat()
    bill_items = [{"description": str(item.get("description", "")).strip(), "amount": money(item.get("amount"), "Item amount")} for item in items]
    if any(not item["description"] for item in bill_items):
        raise ValueError("Each bill item needs a description.")
    total = calculate_total(bill_items)
    bills = load_records("bills.json")
    record = {"id": next_id(bills, "B"), "patient_id": patient_id, "doctor_id": doctor_id or "", "date": bill_date, "items": bill_items, "total": total, "created_at": datetime.now().isoformat(timespec="seconds")}
    bills.append(record)
    save_records("bills.json", bills)
    return record
