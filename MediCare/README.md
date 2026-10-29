# MediCare — Hospital Management & Analytics System

MediCare is a local Tkinter desktop application for a Software Laboratory–I project. It demonstrates common administrative workflows with fictional data: patient and doctor records, appointment scheduling, medicine stock, bills, aggregate analytics, and a public health information explorer.

> **Educational prototype only.** Do not use this project to store real patient information, make medical decisions, or manage a real hospital. It has no production security, audit, backup, or compliance controls.

## Objectives and features

- Navigate a dashboard and seven administrative modules from a resizable desktop window.
- Create, search, edit, and safely delete patients, doctors, and medicines.
- Book, reschedule, complete, and cancel appointments; prevent booked slot conflicts.
- Track medicine low stock, expired stock, and expiry within 30 days.
- Create itemized bills with saved totals and optional consultation fee line items.
- Summarize actual local records with NumPy, SciPy descriptive statistics, and embedded Matplotlib charts.
- Retrieve one user-selected HTTPS page using Requests and parse its title, headings, links, and text with Beautiful Soup in a background thread.
- Persist data in readable local JSON files. The repository ignores generated JSON records.

## Technologies

Python 3, Tkinter/ttk, JSON, NumPy, SciPy, Matplotlib, Requests, Beautiful Soup 4, and the standard `unittest` framework. Tkinter is included with many Python distributions; Linux may require `python3-tk` (for example, `sudo apt install python3-tk`).

## Project structure

```text
main.py                 Application entry point
ui/app.py               Navigation, forms, tables, charts and explorer
services/records.py     Patient, doctor and medicine operations
services/appointments.py Appointment validation and status operations
services/billing.py     Bill snapshots and calculations
services/analytics.py   NumPy summaries and SciPy daily statistics
services/health_scraper.py Requests + Beautiful Soup workflow
utils/storage.py        Shared safe JSON file interface
utils/validators.py     Shared input validation
utils/ids.py            Sequential ID generation
data/                   Local records created at first launch
tests/                  Offline unit tests for business logic
```

## Install and run

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

The app creates `data/` and missing empty JSON files on startup. Start it from the project root with a Python build that includes Tkinter. Dependencies are not installed automatically by the application.

## Local storage and record interfaces

`utils.storage.load_records(filename)` returns a list of dictionaries; `save_records(filename, records)` writes a UTF-8 indented JSON list through a temporary file and replacement. Invalid JSON and file errors are reported without silently replacing the file. Supported files are `patients.json`, `doctors.json`, `appointments.json`, `medicines.json`, and `bills.json`. IDs use `P0001`, `D0001`, `A0001`, `M0001`, and `B0001` patterns. Cross-module links use `patient_id` and `doctor_id`. Bill items and totals are saved as snapshots, so later fee changes do not alter old bills. Add only fictional demo records; generated JSON is git-ignored.

## Module guide

- `ui/app.py` builds the application shell and page controls; Tkinter remains on the main thread. The web fetch runs in a worker and returns UI updates through `after()`.
- `services/records.py` validates entity fields and prevents removal of patients/doctors referenced by appointments or bills.
- `services/appointments.py` validates references and date/time and checks booked doctor slots, excluding the record being edited.
- `services/billing.py` validates bill items and calculates the final amount from stored item values.
- `services/analytics.py` produces aggregate summaries and daily completed-visit counts.
- `services/health_scraper.py` restricts URLs to HTTPS, sets a timeout and user agent, and parses a limited amount of page content.
- `utils/` contains shared file, ID, and validation helpers.

## Syllabus coverage

| Concept | Demonstration |
|---|---|
| Variables, types, operators, conditions and loops | Record forms, validation, warnings, totals and filtering in `ui/app.py` and `services/` |
| Lists, dictionaries and user-defined functions | JSON record operations and bill item lists in `services/` |
| File handling | `utils/storage.py` creates, loads and safely replaces local JSON files |
| Modules and packages | `ui/`, `services/`, `utils/`, and `tests/` |
| NumPy | `services/analytics.py`: sum, mean, minimum and maximum on actual bill totals and visit arrays |
| SciPy | `services/analytics.py`: `scipy.stats.describe` over 30 daily completed-visit counts; the GUI displays observations, range, mean and variance |
| Matplotlib | `ui/app.py`: embedded completed visits and date-based bill revenue charts |
| Requests | `services/health_scraper.py`: timeout-limited HTTPS webpage retrieval |
| Beautiful Soup | `services/health_scraper.py`: title, headings, links and paragraph extraction |

Representative oral-exam functions: `next_id()` scans saved records to create the next readable key; `appointment_record()` validates references, future time and a doctor's slot; `calculate_total()` sums validated Decimal amounts; `billing_summary()` safely summarizes aggregate amounts with NumPy; `parse_html()` extracts a bounded set of useful page elements.

## Four-person responsibility allocation

- **Member 1 — Patient and Doctor Management:** `services/records.py` patient/doctor validation and safe CRUD; corresponding forms/tables in `ui/app.py`.
- **Member 2 — Appointments and Inventory:** `services/appointments.py`, inventory functions in `services/records.py`, and their `ui/app.py` pages.
- **Member 3 — Billing and Analytics:** `services/billing.py`, `services/analytics.py`, and associated `ui/app.py` pages.
- **Member 4 — GUI, Storage Integration, and Web Explorer:** `ui/app.py`, `utils/storage.py`, `services/health_scraper.py`, `README.md`, and integration coordination.

All members should review the shared ID/reference formats, storage interface, and tests before integrating changes.

## Automated tests

Run offline logic tests with:

```bash
python -m unittest discover -s tests -v
```

The scraper tests parse local sample HTML and mock timeouts; they do not contact a live website. Some analytics assertions require only NumPy. SciPy and Matplotlib features require installing all dependencies from `requirements.txt`.

## Limitations

This is a single-user local demo with no login, database server, encryption, role permissions, backup, audit history, concurrency protection, calendar integration, or production-grade security. Records are plain JSON. The explorer retrieves only one public HTTPS page per user action and depends on the source allowing access. The charts summarize available administrative records and show explanatory empty states.
