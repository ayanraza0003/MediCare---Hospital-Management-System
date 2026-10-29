"""Safe JSON storage shared by all application modules."""
import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
FILES = ("patients.json", "doctors.json", "appointments.json", "medicines.json", "bills.json")


def initialize_storage():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for filename in FILES:
        path = DATA_DIR / filename
        if not path.exists():
            path.write_text("[]\n", encoding="utf-8")


def _path(filename):
    name = Path(filename).name
    if name not in FILES:
        raise ValueError(f"Unsupported data file: {name}")
    initialize_storage()
    return DATA_DIR / name


def load_records(filename):
    path = _path(filename)
    try:
        with path.open("r", encoding="utf-8") as stream:
            records = json.load(stream)
    except json.JSONDecodeError as error:
        raise ValueError(f"{path.name} contains invalid JSON. Restore or repair the file before continuing.") from error
    except OSError as error:
        raise OSError(f"Could not read {path.name}: {error}") from error
    if not isinstance(records, list) or any(not isinstance(item, dict) for item in records):
        raise ValueError(f"{path.name} must contain a JSON list of records.")
    return records


def save_records(filename, records):
    if not isinstance(records, list) or any(not isinstance(item, dict) for item in records):
        raise ValueError("Records must be a list of dictionaries.")
    path = _path(filename)
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            json.dump(records, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    except OSError as error:
        temporary.unlink(missing_ok=True)
        raise OSError(f"Could not save {path.name}: {error}") from error
