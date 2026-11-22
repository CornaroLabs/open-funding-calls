from datetime import datetime, timezone
from pathlib import Path

import pytest

from open_funding_calls import validate_file

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"
NOW = datetime(2026, 11, 22, 12, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize("name", ["nlnet-restack-2.json", "dao-rolling-grant.json"])
def test_valid_examples_have_no_issues(name):
    assert validate_file(EXAMPLES / name, now=NOW) == []


def rules(name):
    return {i.rule for i in validate_file(EXAMPLES / "invalid" / name, now=NOW)}


def test_semantic_errors_detected():
    assert {"date-order", "amount-range", "status-expired", "stale"} <= rules("bad-dates-and-amounts.json")


def test_structural_errors_detected():
    issues = validate_file(EXAMPLES / "invalid" / "missing-fields.json", now=NOW)
    assert issues and all(i.rule == "schema" for i in issues)
    text = " ".join(i.message for i in issues)
    for field in ("funder", "provenance", "ongoing", "no-prefix"):
        assert field in text


def test_expired_open_call_warns_later():
    later = datetime(2027, 2, 1, tzinfo=timezone.utc)
    found = {i.rule for i in validate_file(EXAMPLES / "nlnet-restack-2.json", now=later)}
    assert "status-expired" in found
