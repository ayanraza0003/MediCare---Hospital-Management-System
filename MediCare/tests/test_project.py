import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

from utils import storage
from utils.validators import integer, money, valid_date, phone
from services.records import medicine_warnings, patient_record, search_records
from services.billing import calculate_total
from services.analytics import billing_summary, visits_last_days, scipy_summary
from services.health_scraper import parse_html, validate_url, fetch_page
from services.appointments import save_appointment
from services.billing import create_bill


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.original = storage.DATA_DIR
        storage.DATA_DIR = Path(self.temp.name)

    def tearDown(self):
        storage.DATA_DIR = self.original
        self.temp.cleanup()

    def test_missing_files_and_round_trip(self):
        storage.initialize_storage()
        self.assertEqual(storage.load_records("patients.json"), [])
        row = [{"id": "P0001", "name": "Demo Person"}]
        storage.save_records("patients.json", row)
        self.assertEqual(storage.load_records("patients.json"), row)

    def test_invalid_json_preserved(self):
        path = Path(self.temp.name) / "patients.json"
        path.write_text("{broken", encoding="utf-8")
        with self.assertRaises(ValueError):
            storage.load_records("patients.json")
        self.assertEqual(path.read_text(encoding="utf-8"), "{broken")


class ValidationTests(unittest.TestCase):
    def test_validators(self):
        self.assertEqual(integer("4", "Age", 0, 120), 4)
        self.assertEqual(money("2.345"), 2.35)
        self.assertEqual(valid_date("2030-01-01").isoformat(), "2030-01-01")
        self.assertTrue(phone("+1 (555) 123-4567"))
        with self.assertRaises(ValueError): integer("bad", "Age")

    def test_patient_validation(self):
        record = patient_record({"name":"Demo Person", "age":"20", "gender":"Prefer not to say", "phone":"12345678", "email":"", "address":""})
        self.assertEqual(record["age"], 20)
        with self.assertRaises(ValueError): patient_record({"name":"", "age":"20", "gender":"X", "phone":"12345678"})


class AppointmentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.original = storage.DATA_DIR
        storage.DATA_DIR = Path(self.temp.name)
        storage.initialize_storage()
        storage.save_records("patients.json", [{"id":"P0001", "name":"Demo Patient"}])
        storage.save_records("doctors.json", [{"id":"D0001", "name":"Demo Doctor", "fee":75}])

    def tearDown(self):
        storage.DATA_DIR = self.original
        self.temp.cleanup()

    def test_booking_conflict_and_cancelled_slot(self):
        appointment_date = (date.today() + timedelta(days=2)).isoformat()
        data = {"patient_id":"P0001", "doctor_id":"D0001", "date":appointment_date, "time":"10:00", "status":"Booked"}
        save_appointment(data)
        with self.assertRaisesRegex(ValueError, "already has"):
            save_appointment(data)
        storage.save_records("appointments.json", [{**storage.load_records("appointments.json")[0], "status":"Cancelled"}])
        save_appointment(data)

    def test_edit_excludes_self_and_bill_snapshot(self):
        appointment_date = (date.today() + timedelta(days=2)).isoformat()
        appointment = save_appointment({"patient_id":"P0001", "doctor_id":"D0001", "date":appointment_date, "time":"10:00", "status":"Booked"})
        updated = save_appointment({"patient_id":"P0001", "doctor_id":"D0001", "date":appointment_date, "time":"10:00", "status":"Booked"}, appointment["id"])
        self.assertEqual(updated["id"], appointment["id"])
        bill = create_bill("P0001", "D0001", date.today().isoformat(), [{"description":"Consultation", "amount":75}])
        storage.save_records("doctors.json", [{"id":"D0001", "name":"Demo Doctor", "fee":120}])
        self.assertEqual(storage.load_records("bills.json")[0]["items"][0]["amount"], 75)
        with self.assertRaises(ValueError): create_bill("P0001", "", "not-a-date", [{"description":"Item", "amount":1}])

    def test_medicine_warnings(self):
        today = date(2030, 1, 1)
        self.assertEqual(medicine_warnings({"quantity":2,"reorder_level":2,"expiry":"2029-12-31"},today), ["Low stock", "Expired"])
        self.assertIn("Expires soon", medicine_warnings({"quantity":5,"reorder_level":2,"expiry":"2030-01-20"},today))


class AnalyticsBillingTests(unittest.TestCase):
    def test_bill_total(self):
        self.assertEqual(calculate_total([{"amount":"10.20"},{"amount":"2.30"}]), 12.5)
        with self.assertRaises(ValueError): calculate_total([])

    def test_numpy_summary_and_empty(self):
        result = billing_summary([{"total":10},{"total":20}])
        self.assertEqual(result["total"],30)
        self.assertEqual(billing_summary([])["count"],0)

    def test_visits_and_scipy(self):
        today = date(2030,1,30)
        _, counts = visits_last_days(30,[{"date":"2030-01-29","status":"Completed"}],today)
        self.assertEqual(int(counts.sum()),1)
        self.assertIsNone(scipy_summary([1]))


class ScraperTests(unittest.TestCase):
    def test_parse_html(self):
        result = parse_html('<title>Health</title><h1>Guide</h1><p>Read here</p><a href="/topic">Topic</a>', 'https://example.org/page')
        self.assertEqual(result["title"],"Health")
        self.assertEqual(result["headings"],["Guide"])
        self.assertEqual(result["links"][0]["url"],"https://example.org/topic")

    def test_missing_html_and_url(self):
        self.assertEqual(parse_html("<html></html>","https://example.org")["title"],"Untitled page")
        with self.assertRaises(ValueError): validate_url("file:///etc/passwd")
        with self.assertRaises(ValueError): validate_url("http://example.org")

    @patch("services.health_scraper.requests.get")
    def test_timeout_message(self, get):
        import requests
        get.side_effect = requests.Timeout()
        with self.assertRaisesRegex(ValueError,"too long"):
            fetch_page("https://example.org")


if __name__ == "__main__":
    unittest.main()
