"""Structural (JSON Schema) and semantic validation of funding call records."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator, FormatChecker

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schema" / "funding-call.schema.json"
STALE_AFTER = timedelta(days=30)


@dataclass(frozen=True)
class Issue:
    """One validation finding. Rule ids are stable so tools can filter them."""

    rule: str
    severity: str  # "error" or "warning"
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.severity.upper():7} {self.rule:22} {self.path or '/'}: {self.message}"


def load_schema(path: Path | str = SCHEMA_PATH) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _parse_dt(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else None


def _structural(record: Any, schema: dict) -> Iterable[Issue]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for err in sorted(validator.iter_errors(record), key=lambda e: list(e.absolute_path)):
        path = "/" + "/".join(str(p) for p in err.absolute_path)
        yield Issue("schema", "error", path, err.message)


def _semantic(record: dict, now: datetime) -> Iterable[Issue]:
    # Timestamps without a time zone are ambiguous.
    dates = record.get("dates") or {}
    raw = [("/dates/opens", dates.get("opens"))] + [
        (f"/dates/deadlines/{i}/dateTime", d.get("dateTime"))
        for i, d in enumerate(dates.get("deadlines") or [])
        if isinstance(d, dict)
    ]
    for path, value in raw:
        if isinstance(value, str) and _parse_dt(value) is None:
            yield Issue("date-timezone", "error", path, "date-time must include a time zone offset (e.g. Z or +01:00)")

    opens = _parse_dt(dates.get("opens"))
    deadlines = [
        _parse_dt(d.get("dateTime")) for d in (dates.get("deadlines") or []) if isinstance(d, dict)
    ]
    deadlines = [d for d in deadlines if d]

    if opens and any(d < opens for d in deadlines):
        yield Issue("date-order", "error", "/dates", "a deadline is earlier than the opening date")

    status = record.get("status")
    if status in ("open", "upcoming") and deadlines and max(deadlines) < now:
        yield Issue("status-expired", "warning", "/status", f"status is '{status}' but all deadlines have passed")
    if status == "upcoming" and opens and opens < now:
        yield Issue("status-upcoming-past", "warning", "/status", "status is 'upcoming' but the opening date has passed")
    if status == "rolling" and deadlines:
        yield Issue("rolling-with-deadline", "warning", "/dates", "status is 'rolling' but fixed deadlines are given")
    if status in ("open", "upcoming") and not deadlines and not dates.get("rolling"):
        yield Issue("no-deadline", "warning", "/dates", "open or upcoming call has no deadline and is not marked rolling")

    amount = record.get("amount") or {}
    lo, hi, total = amount.get("minPerProject"), amount.get("maxPerProject"), amount.get("totalBudget")
    if isinstance(lo, (int, float)) and isinstance(hi, (int, float)) and lo > hi:
        yield Issue("amount-range", "error", "/amount", "minPerProject is greater than maxPerProject")
    if isinstance(hi, (int, float)) and isinstance(total, (int, float)) and hi > total:
        yield Issue("amount-total", "error", "/amount", "maxPerProject is greater than totalBudget")

    verified = _parse_dt((record.get("provenance") or {}).get("lastVerified"))
    if verified and status not in ("closed", "cancelled") and now - verified > STALE_AFTER:
        days = (now - verified).days
        yield Issue("stale", "warning", "/provenance/lastVerified", f"record not verified for {days} days")
    if verified and verified > now + timedelta(minutes=5):
        yield Issue("verified-in-future", "error", "/provenance/lastVerified", "lastVerified is in the future")


def validate(record: Any, schema: dict | None = None, now: datetime | None = None) -> list[Issue]:
    """Return all issues for one record. An empty list means valid with no warnings."""
    schema = schema or load_schema()
    now = now or datetime.now(timezone.utc)
    issues = list(_structural(record, schema))
    if isinstance(record, dict):
        issues.extend(_semantic(record, now))
    return issues


def validate_file(path: Path | str, schema: dict | None = None, now: datetime | None = None) -> list[Issue]:
    """Validate a .json file (one record or a list) or a .jsonl file (one record per line)."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".jsonl":
        records = [json.loads(line) for line in text.splitlines() if line.strip()]
    else:
        data = json.loads(text)
        records = data if isinstance(data, list) else [data]
    issues: list[Issue] = []
    for i, rec in enumerate(records):
        prefix = f"/{i}" if len(records) > 1 else ""
        for issue in validate(rec, schema, now):
            issues.append(Issue(issue.rule, issue.severity, prefix + issue.path, issue.message))
    return issues
