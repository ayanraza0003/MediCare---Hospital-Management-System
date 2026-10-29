"""Patient, doctor and inventory operations."""
from datetime import date, datetime, timedelta
from utils.ids import next_id
from utils.storage import load_records, save_records
from utils.validators import integer, money, optional_email, phone, required_text, valid_date


def search_records(filename, query, fields):
    query = query.casefold().strip()
    records = load_records(filename)
    return records if not query else [row for row in records if any(query in str(row.get(key, "")).casefold() for key in fields)]


def save_entity(filename, prefix, record, record_id=None):
    records = load_records(filename)
    item = dict(record)
    item["id"] = record_id or next_id(records, prefix)
    item.setdefault("created_at", datetime.now().isoformat(timespec="seconds"))
    found = False
    for index, old in enumerate(records):
        if old.get("id") == item["id"]:
            item["created_at"] = old.get("created_at", item["created_at"])
            records[index] = item
            found = True
            break
    if not found:
        records.append(item)
    save_records(filename, records)
    return item


def delete_entity(filename, record_id, protected_files=()):
    for other_file, key in protected_files:
        if any(row.get(key) == record_id for row in load_records(other_file)):
            raise ValueError("This record is linked to existing activity and cannot be deleted safely.")
    rows = load_records(filename)
    filtered = [row for row in rows if row.get("id") != record_id]
    if len(filtered) == len(rows):
        raise ValueError("The selected record no longer exists.")
    save_records(filename, filtered)


def patient_record(data):
    return {"name": required_text(data["name"], "Full name"), "age": integer(data["age"], "Age", 0, 120), "gender": required_text(data["gender"], "Gender"), "phone": phone(data["phone"]), "email": optional_email(data.get("email", "")), "address": str(data.get("address", "")).strip()}


def doctor_record(data):
    return {"name": required_text(data["name"], "Full name"), "specialization": required_text(data["specialization"], "Specialization"), "phone": phone(data["phone"]), "fee": money(data["fee"], "Consultation fee")}


def medicine_record(data):
    expiry = valid_date(data["expiry"], "Expiry date")
    return {"name": required_text(data["name"], "Medicine name"), "category": required_text(data["category"], "Category"), "quantity": integer(data["quantity"], "Quantity"), "unit": required_text(data["unit"], "Unit"), "reorder_level": integer(data["reorder_level"], "Reorder threshold"), "expiry": expiry.isoformat(), "price": money(data["price"], "Unit price")}


def medicine_warnings(row, today=None):
    today = today or date.today()
    warnings = []
    if int(row.get("quantity", 0)) <= int(row.get("reorder_level", 0)):
        warnings.append("Low stock")
    try:
        expiry = valid_date(row.get("expiry", ""), "Expiry date")
        if expiry < today:
            warnings.append("Expired")
        elif expiry <= today + timedelta(days=30):
            warnings.append("Expires soon")
    except ValueError:
        warnings.append("Invalid expiry date")
    return warnings
