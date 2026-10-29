"""Small reusable input validators with user-friendly errors."""
import re
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def required_text(value, label):
    result = str(value).strip()
    if not result:
        raise ValueError(f"{label} is required.")
    return result


def integer(value, label, minimum=0, maximum=None):
    try:
        result = int(str(value).strip())
    except (ValueError, TypeError):
        raise ValueError(f"{label} must be a whole number.")
    if result < minimum or (maximum is not None and result > maximum):
        limit = f"{minimum}–{maximum}" if maximum is not None else f"at least {minimum}"
        raise ValueError(f"{label} must be {limit}.")
    return result


def money(value, label="Amount"):
    try:
        result = Decimal(str(value).strip()).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"{label} must be a valid amount, such as 25.00.")
    if not result.is_finite() or result < 0:
        raise ValueError(f"{label} must be a non-negative amount.")
    return float(result)


def valid_date(value, label="Date"):
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"{label} must use YYYY-MM-DD format.")


def valid_time(value):
    try:
        return datetime.strptime(str(value).strip(), "%H:%M").time()
    except ValueError:
        raise ValueError("Time must use 24-hour HH:MM format, such as 14:30.")


def phone(value):
    result = required_text(value, "Phone number")
    digits = sum(character.isdigit() for character in result)
    if digits < 7 or digits > 15 or not re.fullmatch(r"[+()\- .\d]+", result):
        raise ValueError("Enter a phone number with 7–15 digits; +, spaces, brackets and hyphens are allowed.")
    return result


def optional_email(value):
    result = str(value).strip()
    if result and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", result):
        raise ValueError("Enter a valid email address, or leave it blank.")
    return result
