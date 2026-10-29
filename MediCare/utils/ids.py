"""Readable sequential IDs for demo records."""


def next_id(records, prefix):
    largest = 0
    for record in records:
        value = str(record.get("id", ""))
        if value.startswith(prefix) and value[len(prefix):].isdigit():
            largest = max(largest, int(value[len(prefix):]))
    return f"{prefix}{largest + 1:04d}"
