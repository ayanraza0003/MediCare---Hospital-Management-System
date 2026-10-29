"""Aggregate operational summaries using NumPy and SciPy."""
from datetime import date, timedelta
import numpy as np
from utils.storage import load_records


def billing_summary(bills=None):
    bills = load_records("bills.json") if bills is None else bills
    values = np.array([float(row.get("total", 0)) for row in bills], dtype=float)
    if values.size == 0:
        return {"count": 0, "total": 0.0, "mean": 0.0, "minimum": 0.0, "maximum": 0.0}
    return {"count": int(values.size), "total": float(np.sum(values)), "mean": float(np.mean(values)), "minimum": float(np.min(values)), "maximum": float(np.max(values))}


def visits_last_days(days=30, appointments=None, today=None):
    appointments = load_records("appointments.json") if appointments is None else appointments
    today = today or date.today()
    start = today - timedelta(days=days - 1)
    counts = []
    labels = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        labels.append(day)
        counts.append(sum(1 for row in appointments if row.get("date") == day.isoformat() and row.get("status") == "Completed"))
    return labels, np.array(counts, dtype=int)


def scipy_summary(counts):
    values = np.asarray(counts, dtype=float)
    if values.size < 2:
        return None
    from scipy import stats
    result = stats.describe(values)
    fields = [int(result.nobs), float(result.minmax[0]), float(result.minmax[1]), float(result.mean), float(result.variance)]
    if not np.all(np.isfinite(fields)):
        return None
    return {"observations": fields[0], "minimum": fields[1], "maximum": fields[2], "mean": fields[3], "variance": fields[4]}
